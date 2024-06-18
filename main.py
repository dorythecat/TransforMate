import os
import aiohttp
import utils

from dotenv import load_dotenv

import discord

# SETTINGS
WEBHOOK_NAME = "TransforMate Webhook"  # Name to use for the webhooks
BLOCKED_USERS = [  # Users that are blocked from using the bot, for whatever reason.
    "967123840587141181"
]
USER_REPORTS_CHANNEL_ID = 1252358817682030743  # Channel to use for the /report command

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)


# Transformation functions
async def transform_function(ctx: discord.ApplicationContext,
                             user: discord.User,
                             into: str,
                             image_url: str,
                             channel: discord.TextChannel) -> bool:
    if not image_url:
        image_url = user.avatar.url
    image_url = image_url.strip()
    if image_url[:4] != "http":
        await ctx.send("Invalid Image URL! Please provide a valid image URL!")
        return False
    if "?" in image_url:  # Prune url, if possible, to preserve space
        image_url = image_url[:image_url.index("?")]

    utils.write_tf(user, ctx.guild, channel, transformed_by=str(ctx.author.id), into=into, image_url=image_url)
    utils.write_transformed(ctx.guild, user, channel)
    return True


# Bot startup
@bot.event
async def on_ready() -> None:
    print(f'\nSuccessfully logged into Discord as "{bot.user}"\n')
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.watching,
                                                        name="people get transformed"))


# Message sent
@bot.event
async def on_message(message: discord.Message) -> None:
    # Check if the message is sent by the bot, we don't want an endless loop that ends on an error/crash, do we?
    if message.author == bot.user or message.author.bot:
        return

    if not message.guild:
        if "report" in message.content.lower():
            await message.author.send("Uh, oh! Do you want to report someone? If so, please provide the user ID, which"
                                      " you can get by right-clicking on their name and selecting \"Copy ID\".")
            user_id = await bot.wait_for('message', check=lambda m: m.author == message.author)
            if not user_id.content.isdigit():
                await message.author.send("That's not a valid user ID! Please try reporting another time!")
                return
            user = await bot.fetch_user(int(user_id.content))
            if not user:
                await message.author.send("That user does not exist! Please try reporting another time!")
                return
            await message.author.send("Please provide a reason for the report.")
            reason = await bot.wait_for('message', check=lambda m: m.author == message.author)
            if reason == "":
                await message.author.send("Please provide a valid reason for the report!")
                return

            await message.author.send(
                "Are you sure you want to report this user? This will send a message to the server owner, and to "
                "the bot developers, with the reason you provided. This action is irreversible. If we find this "
                "is a false report, we will take action against you. Please confirm this action by typing "
                "\"CONFIRM\"."
            )
            response = await bot.wait_for('message', check=lambda m: m.author == message.author)
            if response.content.strip() != "CONFIRM":
                await message.author.send("Cancelled the report!")
                return

            embed = utils.get_embed_base("RECEIVED A REPORT")
            embed.add_field(name="Reported User", value=user.mention)
            embed.add_field(name="Reporter", value=message.author.mention)
            embed.add_field(name="Reason", value=reason.content.strip())
            embed.add_field(name="Reported in DMs", value="")
            await bot.get_channel(USER_REPORTS_CHANNEL_ID).send(embed=embed)
            await message.author.send("Thank you for your report! It has been sent to the developers, for review.")
        return

    # Check if user is transformed, and send their messages as webhooks, deleting the original
    if not utils.is_transformed(message.author, message.guild, message.channel) or \
            message.content.strip().startswith('('):
        return

    if message.stickers:
        await message.author.send("Sorry, but we don't support  sending stickers, for the moment! :(")
        return

    data = utils.load_tf(message.author, message.guild)

    # Handle blocked channels
    # Not necessary to check for blocked users, since they shouldn't be able to use the bot anyway
    if str(message.channel.id) in (data['blocked_channels'] or
                                   utils.load_transformed(message.guild)['blocked_channels']):
        return
    if str(message.channel.id) in (data and
                                   utils.load_transformed(message.guild)['transformed_users'][str(message.author.id)]):
        data = data[str(message.channel.id)]
    elif 'all' in (data and utils.load_transformed(message.guild)['transformed_users'][str(message.author.id)]):
        data = data['all']
    else:
        return

    name = data['into']
    image_url = data['image_url']

    if message.channel.type == discord.ChannelType.private_thread or \
            message.channel.type == discord.ChannelType.public_thread:
        webhook = utils.get_webhook_by_name(await message.channel.parent.webhooks(), WEBHOOK_NAME)
        if not webhook:
            webhook = await message.channel.parent.create_webhook(name=WEBHOOK_NAME)
        # Prepare data to send
        json = {
            'username': name,
            'avatar_url': image_url,
            'content': '',
        }
        if message.content:
            # Check if muffles are active in data
            if data['muffle']['active']:
                # Send the original message to transformed_by if claim is None, otherwise to claim
                if data['claim'] in ["", None]:
                    # Get the user who transformed the user
                    transformed_by = bot.get_user(int(data['transformed_by']))
                else:
                    # Get the user who claimed the user
                    transformed_by = bot.get_user(int(data['claim']))
                # Check if the message is from the user who transformed the user
                if not message.author == transformed_by:
                    # DM the user who transformed the user the original message
                    await transformed_by.send(
                        f"**{message.author.name}** said in #**{message.channel.name}**:\n```{message.content}```")
            json['content'] = utils.transform_text(data, message.content)
        # This method, used down below too, works well, but it's *kinda* janky,
        # especially with more than one attachment...
        # TODO: Find a better way to do this (Low priority)
        for attachment in message.attachments:
            attachment_url = attachment.url.strip()[
                             :attachment.url.index("?")] if "?" in attachment.url else attachment.url
            if image_url == attachment_url:
                return
            json['content'] += "\n" + attachment_url
        # Post data to the webhook using aiohttp
        async with aiohttp.ClientSession() as session:
            # TODO: Add error handling (Low priority)
            # From: https://stackoverflow.com/questions/70631696/discord-webhook-post-to-channel-thread
            async with session.post(
                    f"https://discord.com/api/webhooks/{webhook.id}/{webhook.token}?thread_id={message.channel.id}",
                    json=json
            ) as resp:
                # See https://en.wikipedia.org/wiki/List_of_HTTP_status_codes for meaning of HTTP status codes
                if resp.status not in [200, 203, 204]:
                    print(f"Failed to send message to webhook: {resp.status}")
                    print(f"With data:\n{json}")
        await message.delete()
        return

    webhook = utils.get_webhook_by_name(await message.channel.webhooks(), WEBHOOK_NAME)
    if not webhook:
        webhook = await message.channel.create_webhook(name=WEBHOOK_NAME)

    content = ""
    if message.content:  # If there's no content, and we try to send it, it will trigger a 400 error
        if message.reference:
            content += f"**Replying to {message.reference.resolved.author.mention}:**\n"
            if message.reference.resolved.content:
                content += f">>> {message.reference.resolved.content}"
                # If we don't send this by itself, we'll get fucked over by the multi-line quote, sorry everyone :(
                await webhook.send(content, username=name, avatar_url=image_url)
                content = ""
        # Check if muffles are active in data
        if data['muffle']['active']:
            # Send the original message to transformed_by if claim is None, otherwise to claim
            if data['claim'] in ["", None]:
                # Get the user who transformed the user
                transformed_by = bot.get_user(int(data['transformed_by']))
            else:
                # Get the user who claimed the user
                transformed_by = bot.get_user(int(data['claim']))
            # Check if the message is from the user who transformed the user
            if not message.author == transformed_by:
                # DM the user who transformed the user the original message
                await transformed_by.send(
                    f"**{message.author.name}** said in #**{message.channel.name}**:\n```{message.content}```")
        content += utils.transform_text(data, message.content)

    for attachment in message.attachments:
        attachment_url = attachment.url.strip()[:attachment.url.index("?")] if "?" in attachment.url else attachment.url
        if image_url == attachment_url:
            return
        content += "\n" + attachment_url
    await webhook.send(content, username=name, avatar_url=image_url)
    await message.delete()


# Reaction added
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User) -> None:
    if str(reaction.emoji) == "❓":
        # Check if reaction is reacting to a message sent by a transformed user
        # I know this isn't the most efficient method, but it's really the best we have, at least for now
        # TODO: Find a better way to do this (maybe?)
        tfee_data = utils.load_transformed(reaction.message.guild)['transformed_users']
        for tfee in tfee_data:
            data = utils.load_tf_by_id(tfee, reaction.message.guild)
            data = data[str(reaction.message.channel.id)] if str(reaction.message.channel.id) in data else data['all']
            if data['into'] == reaction.message.author.name:
                await user.send(f"\"{reaction.message.author.name}\" is, in fact, {bot.get_user(int(tfee)).mention}!\n"
                                f"(Transformed by {bot.get_user(int(data['transformed_by'])).mention})")
                await reaction.remove(user)


# Transformation commands
@bot.slash_command(description="Transform someone")
async def transform(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None,
                    into: discord.Option(discord.SlashCommandOptionType.string,
                                         description="Who to transform") = None,
                    image_url: discord.Option(discord.SlashCommandOptionType.string,
                                              description="Image URL to use") = None,
                    channel: discord.Option(discord.TextChannel,
                                            description="Transform the user only on this channel") = None) -> None:
    if not user:
        user = ctx.author

    data = utils.load_tf(user, ctx.guild)
    tfee_data = utils.load_transformed(ctx.guild)
    channel_id = str(ctx.channel.id if not channel else channel.id)

    # Blocked channels (user)
    if data != {}:
        if channel_id in data['blocked_channels']:
            await ctx.respond(f"You can't transform {user.mention} in this channel! They have blocked the bot here!")
            return

    if tfee_data != {}:
        # Blocked channels (server)
        if channel_id in tfee_data['blocked_channels']:
            await ctx.respond(f"You're blocked from using this bot on this channel!")
            return

        # Blocked users (server)
        if str(ctx.user.id) in tfee_data['blocked_users']:
            await ctx.respond(f"You're blocked from using this bot on this server!")
            return
        if str(user.id) in tfee_data['blocked_users']:
            await ctx.respond(f"You're blocked from transforming that user on this server!")
            return

    # Blocked users (globally)
    if str(ctx.user.id) in BLOCKED_USERS:
        await ctx.respond(f"You're blocked from using this bot at all! You must've done something very bad...")
        return
    if str(user.id) in BLOCKED_USERS:
        await ctx.respond(f"You can't transform that user at all! They've been very naughty...")
        return

    if utils.is_transformed(user, ctx.guild):
        if channel_id in data:
            data = data[channel_id]
        elif 'all' in data:
            data = data['all']
        else:
            return
        if data['claim'].strip() not in ["", None] and data['claim'] != ctx.author.name and data['eternal']:
            if ctx.author.name != user.name:
                await ctx.respond(f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
                return
            await ctx.respond(f"Your master can't allow you to transform, at least for now...")
            return

    if into:
        if len(into.strip()) <= 1:
            await ctx.send("Please provide a name longer than 1 character!")
            return
        if await transform_function(ctx, user, into, image_url, channel):
            await ctx.respond(f'You have transformed {user.mention} into "{into}"!')
        return

    await ctx.respond(f"What do we want to transform {user.mention} into? (Send CANCEL to cancel)")
    response = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    if response.content.strip() == "CANCEL":
        await ctx.respond("Cancelled the transformation!")
        return
    if len(response.content.strip()) <= 1:
        await ctx.send("Please provide a name longer than 1 character!")
        return
    if await transform_function(ctx,
                                user,
                                response.content,
                                response.attachments[0].url if response.attachments else None,
                                channel):
        await ctx.respond(f'You have transformed {user.mention} into "{response.content}"!')


@bot.slash_command(description="Return someone to their previous state")
async def goback(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None) -> None:
    if user is None:
        user = ctx.author
    data = utils.load_tf(user, ctx.guild)
    channel = None
    if str(ctx.channel.id) in data:
        data = data[str(ctx.channel.id)]
        channel = ctx.channel
    elif 'all' in data:
        data = data['all']
    else:
        await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to! "
                          f"(At least on this channel)")
        return

    if not utils.is_transformed(user, ctx.guild, ctx.channel) and not utils.is_transformed(user, ctx.guild):
        if data['into'].strip() in ["", None]:
            await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to!")
            return
        utils.write_transformed(ctx.guild, user, channel)
        await ctx.respond(f"{user.mention} has been turned back to their last form!")
        return

    if data['eternal'] and data['claim'] != ctx.author.name:
        if ctx.author.name != user.name:
            await ctx.respond(f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
            return
        await ctx.respond(f"Your master won't allow you to turn back, at least for now...")
        return

    utils.remove_transformed(user, ctx.guild, None if utils.is_transformed(user, ctx.guild) else ctx.channel)
    await ctx.respond(f"{user.mention} has been turned back to normal!")


@bot.slash_command(description="Claim a transformed user")
async def claim(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User)) -> None:
    if user == ctx.author:
        await ctx.respond(f"You can't claim yourself!")
        return
    if not utils.is_transformed(user, ctx.guild):
        await ctx.respond(f"{user.mention} is not transformed at the moment, you can't claim them!")
        return
    data = utils.load_tf(user, ctx.guild)
    channel = None
    if str(ctx.channel) in data:
        data = data[str(ctx.channel)]
        channel = ctx.channel
    else:
        data = data['all']
    if data['claim'].strip() not in ["", None] and data['claim'] != ctx.author.name:
        await ctx.respond(f"You can't do that! {user.mention} has been claimed already by {data['claim']}!")
        return
    utils.write_tf(user, ctx.guild, channel, claim_user=ctx.author.name)
    await ctx.respond(f"You have successfully claimed {user.mention} for yourself! Hope you enjoy!")


@bot.slash_command(description="Unclaim a transformed user")
async def unclaim(ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User)) -> None:
    if user == ctx.author:
        await ctx.respond(f"You can't unclaim yourself! Only your master can do that!\n"
                          f"||Use \"/safeword\", if you actually want to unclaim yourself.||")
        return
    data = utils.load_tf(user, ctx.guild)
    channel = None
    if str(ctx.channel) in data:
        data = data[str(ctx.channel)]
        channel = ctx.channel
    else:
        data = data['all']
    if data['claim'].strip() in ["", None]:
        await ctx.respond(f"{user.mention} is currently not claimed by anyone!")
        return
    if data['claim'].strip() != ctx.author.name:
        await ctx.respond(f"You can't do that! {user.mention} is claimed by {data['claim']}, not you!")
        return
    utils.write_tf(user, ctx.guild, channel, claim_user="", eternal=0)
    await ctx.respond(f"You have successfully unclaimed {user.mention}! They are now free from your grasp!")


@bot.slash_command(description="Safeword command. Use in case of abuse or incommodity, to unclaim yourself.")
async def safeword(ctx: discord.ApplicationContext) -> None:
    data = utils.load_tf(ctx.author, ctx.guild)
    channel = None
    if str(ctx.channel) in data:
        data = data[str(ctx.channel)]
        channel = ctx.channel
    else:
        data = data['all']
    # We have to check if they are claimed OR eternally transformed. If both are false, safeword does nothing.
    # If either are true, we need to keep going, otherwise we can just return.
    if data['claim'].strip() in ["", None] and not data['eternal']:
        await ctx.respond(f"You can't do that! You are not claimed by anyone! Stop trying to abuse! >:(")
        return
    utils.write_tf(ctx.author, ctx.guild, channel, claim_user="", eternal=0)
    await ctx.respond(f"You have successfully activated the safeword command.\n"
                      f"Please, sort out any issues with your rp partner(s) before you continue using the bot .\n"
                      f"Use \"/goback\" to return to your normal self.")


# "Set" Commands
set_command = bot.create_group("set", "Set various things about transformed users")


@set_command.command(description="Set a prefix for the transformed messages")
async def prefix(ctx: discord.ApplicationContext,
                 prefix_word: discord.Option(discord.SlashCommandOptionType.string,
                                             description="Prefix to add"),
                 prefix_chance: discord.Option(discord.SlashCommandOptionType.integer,
                                               description="Chance for prefix to go off") = 30,
                 user: discord.Option(discord.User) = None,
                 whitespace: discord.Option(discord.SlashCommandOptionType.boolean,
                                            description="Add a space after the prefix (defaults true)") = True) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    prefix_word += (" " * whitespace)
    utils.write_tf(user, ctx.guild, prefix=prefix_word, mod_type="prefix", chance=prefix_chance)
    await ctx.respond(f"Prefix for {user.mention} set to \"*{prefix_word}*\"!")


@set_command.command(description="Set a suffix for the transformed messages")
async def suffix(ctx: discord.ApplicationContext,
                 suffix_word: discord.Option(discord.SlashCommandOptionType.string,
                                             description="Suffix to add"),
                 suffix_chance: discord.Option(discord.SlashCommandOptionType.integer,
                                               description="Chance for suffix to go off") = 30,
                 user: discord.Option(discord.User) = None,
                 whitespace: discord.Option(discord.SlashCommandOptionType.boolean,
                                            description="Add a space before the suffix (defaults true)") = True) \
        -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    suffix_word = (" " * whitespace) + suffix_word
    utils.write_tf(user, ctx.guild, suffix=suffix_word, mod_type="suffix", chance=suffix_chance)
    await ctx.respond(f"Suffix for {user.mention} set to \"*{suffix_word}*\"!")


@set_command.command(description="Set the transformed user to speak in big text")
async def big(ctx: discord.ApplicationContext,
              user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if data['big']:
        await ctx.respond(f"{user.mention} is already speaking big!")
        return
    utils.write_tf(user, ctx.guild, big=1)
    await ctx.respond(f"{user.mention} will now speak in big text!")


@set_command.command(description="Set the transformed user to speak in small text")
async def small(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if data['small']:
        await ctx.respond(f"{user.mention} is already speaking small!")
        return
    utils.write_tf(user, ctx.guild, small=1)
    await ctx.respond(f"{user.mention} will now speak in small text!")


@set_command.command(description="Set the transformed user to hush")
async def hush(ctx: discord.ApplicationContext,
               user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if data['hush']:
        await ctx.respond(f"{user.mention} is already hushed!")
        return
    utils.write_tf(user, ctx.guild, hush=1)
    await ctx.respond(f"{user.mention} will now hush!")


@set_command.command(description="Set the transformed user to be eternally transformed")
async def eternal(ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User)) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if data['eternal']:
        await ctx.respond(f"{user.mention} is already eternally transformed!")
        return
    utils.write_tf(user, ctx.guild, eternal=1)
    await ctx.respond(f"{user.mention} is now eternally transformed!")


@set_command.command(description="Set the transformed user to be censored")
async def censor(ctx: discord.ApplicationContext,
                 censor_word: discord.Option(discord.SlashCommandOptionType.string,
                                             description="Word to censor"),
                 replacement: discord.Option(discord.SlashCommandOptionType.string,
                                             description="Word to replace with"),
                 user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    utils.write_tf(user, ctx.guild, censor=censor_word, censor_replacement=replacement)
    await ctx.respond(f"{user.mention} will now have the word \"{censor}\" censored to \"{replacement}\"!")


@set_command.command(description="Set the transformed user to have specific words sprinkled in their messages")
async def sprinkle(ctx: discord.ApplicationContext,
                   sprinkle_word: discord.Option(discord.SlashCommandOptionType.string,
                                                 description="Word to sprinkle"),
                   sprinkle_chance: discord.Option(discord.SlashCommandOptionType.integer,
                                                   description='Chance for sprinkle to go off') = 30,
                   user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    utils.write_tf(user, ctx.guild, sprinkle=sprinkle_word, mod_type="sprinkle", chance=sprinkle_chance)
    await ctx.respond(f"{user.mention} will now have the word \"{sprinkle_word}\" sprinkled in their messages!")


@set_command.command(
    description="Set the transformed user to have their words randomly replaced with a specific set of words")
async def muffle(ctx: discord.ApplicationContext,
                 muffle_word: discord.Option(discord.SlashCommandOptionType.string,
                                             description="Word that will replace others"),
                 chance: discord.Option(discord.SlashCommandOptionType.integer,
                                        description='Chance for muffle to go off') = 30,
                 user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    utils.write_tf(user, ctx.guild, muffle=muffle_word, mod_type="muffle", chance=chance)
    await ctx.respond(f"{user.mention} will now have their words muffled with \"{muffle_word}\"!")


@set_command.command(description="Set a biography for the transformed user")
async def bio(ctx: discord.ApplicationContext,
              biography: discord.Option(discord.SlashCommandOptionType.string,
                                        description="Biography for the transformed user"),
              user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    utils.write_tf(user, ctx.guild, bio=biography)
    await ctx.respond(f"{user.mention}'s biography has been set!")


# "Clear" commands
clear_command = bot.create_group("clear", "Clear various things about transformed users")


@clear_command.command(description="Clear all settings for the transformed user")
async def all_fields(ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    utils.write_tf(user,
                   ctx.guild,
                   claim_user="",
                   eternal=0,
                   prefix="",
                   suffix="",
                   big=0,
                   small=0,
                   hush=0,
                   censor="",
                   sprinkle="",
                   muffle="",
                   bio="")
    await ctx.respond(f"{user.mention} has been cleared of all settings!")


@clear_command.command(description="Clear the prefix for the transformed messages")
async def prefix(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if data['prefix'].strip() in ["", None]:
        await ctx.respond(f"{user.mention} doesn't have a prefix set!")
        return
    utils.write_tf(user, ctx.guild, prefix="")
    await ctx.respond(f"Prefix for {user.mention} has been cleared!")


@clear_command.command(description="Clear the suffix for the transformed messages")
async def suffix(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if data['suffix'].strip() in ["", None]:
        await ctx.respond(f"{user.mention} doesn't have a suffix set!")
        return
    utils.write_tf(user, ctx.guild, suffix="")
    await ctx.respond(f"Suffix for {user.mention} has been cleared!")


@clear_command.command(description="Clear the big text setting for the transformed messages")
async def big(ctx: discord.ApplicationContext,
              user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if not data['big']:
        await ctx.respond(f"{user.mention} doesn't have big text set!")
        return
    utils.write_tf(user, ctx.guild, big=0)
    await ctx.respond(f"{user.mention} will no longer speak in big text!")


@clear_command.command(description="Clear the small text setting for the transformed messages")
async def small(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if not data['small']:
        await ctx.respond(f"{user.mention} doesn't have small text set!")
        return
    utils.write_tf(user, ctx.guild, small=0)
    await ctx.respond(f"{user.mention} will no longer speak in small text!")


@clear_command.command(description="Clear hush setting")
async def hush(ctx: discord.ApplicationContext,
               user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if not data['hush']:
        await ctx.respond(f"{user.mention} doesn't have hush set!")
        return
    utils.write_tf(user, ctx.guild, hush=0)
    await ctx.respond(f"{user.mention} will no longer hush!")


@clear_command.command(description="Clear censor setting")
async def censor(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None,
                 censor_word: discord.Option(discord.SlashCommandOptionType.string,
                                             description="Word to clear") = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if not data['censor']['active']:
        await ctx.respond(f"{user.mention} is not censored at the moment!")
        return
    if censor_word.strip() not in ["", None]:
        if censor_word not in data['censor']['contents']:
            await ctx.respond(f"{user.mention} is not censored with the word \"{censor_word}\"!")
            return
        data['censor']['contents'].remove(censor_word)
        utils.write_tf(user, ctx.guild, censor=data['censor'])
        return
    utils.write_tf(user, ctx.guild, censor="")
    await ctx.respond(f"{user.mention} will no longer have a censor set!")


@clear_command.command(description="Clear sprinkle setting")
async def sprinkle(ctx: discord.ApplicationContext,
                   user: discord.Option(discord.User) = None,
                   sprinkle_word: discord.Option(discord.SlashCommandOptionType.string,
                                                 description="Word to clear") = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    # If the user is not sprinkled, we can just return
    if not data['sprinkle']['active']:
        await ctx.respond(f"{user.mention} is not sprinkled at the moment!")
        return
    # If a word is provided, we can check if it is in the contents array
    if sprinkle_word.strip() not in ["", None]:
        if sprinkle_word not in data['sprinkle']['contents']:
            await ctx.respond(f"{user.mention} is not sprinkled with the word \"{sprinkle_word}\"!")
            return
        data['sprinkle']['contents'].remove(sprinkle_word)
        utils.write_tf(user, ctx.guild, sprinkle=data['sprinkle'])
        await ctx.respond(f"{user.mention} will no longer have the word \"{sprinkle_word}\" sprinkled!")
        return
    utils.write_tf(user, ctx.guild, sprinkle="")
    await ctx.respond(f"{user.mention} will no longer have a sprinkle set!")


@clear_command.command(description="Clear muffle setting")
async def muffle(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None,
                 muffle_word: discord.Option(discord.SlashCommandOptionType.string,
                                             description="Word to clear") = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    # If the user is not muffled, we can just return
    if not data['muffle']['active']:
        await ctx.respond(f"{user.mention} is not muffled at the moment!")
        return
    # If a word is provided, we can check if it is in the contents array
    if muffle_word.strip() not in ["", None]:
        if muffle_word not in data['muffle']['contents']:
            await ctx.respond(f"{user.mention} is not muffled with the word \"{muffle_word}\"!")
            return
        data['muffle']['contents'].remove(muffle_word)
        utils.write_tf(user, ctx.guild, muffle=data['muffle'])
        await ctx.respond(f"{user.mention} will no longer have the word \"{muffle_word}\" muffled!")
        return
    utils.write_tf(user, ctx.guild, muffle="")
    await ctx.respond(f"{user.mention} will no longer have a muffle set!")


@clear_command.command(description="Clear eternal setting")
async def eternal(ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User)) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if not data['eternal']:
        await ctx.respond(f"{user.mention} isn't eternally transformed!")
        return
    utils.write_tf(user, ctx.guild, eternal=0)
    await ctx.respond(f"{user.mention} is no longer eternally transformed!")


@clear_command.command(description="Clear a user's biography")
async def bio(ctx: discord.ApplicationContext,
              user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if data['bio'].strip() in ["", None]:
        await ctx.respond(f"{user.mention} doesn't have a biography set!")
        return
    utils.write_tf(user, ctx.guild, bio="")
    await ctx.respond(f"{user.mention}'s biography has been cleared!")


# 'Get' commands
get_command = bot.create_group("get", "Get to know various things about transformed users")


@get_command.command(description="List the settings for the transformed user")
async def settings(ctx: discord.ApplicationContext,
                   user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user, True)
    if not valid:
        return
    embed = utils.get_embed_base(f"Settings for {user.name}")
    embed.add_field(name="Prefix", value=f"{data['prefix']['chance']}%" if data['prefix'] else "None")
    embed.add_field(name="Suffix", value=f"{data['suffix']['chance']}%" if data['suffix'] else "None")
    embed.add_field(name="Big Text", value="Yes" if data['big'] else "No")
    embed.add_field(name="Small Text", value="Yes" if data['small'] else "No")
    embed.add_field(name="Hush", value="Yes" if data['hush'] else "No")
    embed.add_field(name="Censor", value="Yes" if data['censor']['active'] else "No")
    embed.add_field(name="Sprinkle", value=f"{data['sprinkle']['chance']}%" if data['sprinkle'] else "None")
    embed.add_field(name="Muffle", value=f"{data['muffle']['chance']}%" if data['muffle'] else "None")
    await ctx.respond(embed=embed)


@get_command.command(description="List the censors for the transformed user")
async def censors(ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user, True)
    if not valid:
        return
    if not data['censor']['active']:
        await ctx.respond(f"{user.mention} is not censored at the moment!")
        return
    embed = utils.get_embed_base(f"Censors for {user.name}")
    for word in data['censor']['contents']:
        embed.add_field(name=word, value=data['censor']['contents'][word])
    await ctx.respond(embed=embed)


@get_command.command(description="List the sprinkles for the transformed user")
async def sprinkles(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user, True)
    if not valid:
        return
    if not data['sprinkle']:
        await ctx.respond(f"{user.mention} has no sprinkles at the moment!")
        return
    embed = utils.get_embed_base(f"Sprinkles for {user.name}")
    embed.add_field(name='Sprinkle(s)', value=data['sprinkle']['contents'])
    await ctx.respond(embed=embed)


@get_command.command(description="List the muffle for the transformed user")
async def muffle(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user, True)
    if not valid:
        return
    if not data['muffle']:
        await ctx.respond(f"{user.mention} has no muffles at the moment!")
        return
    embed = utils.get_embed_base(f"Muffle for {user.name}")
    embed.add_field(name='Muffle(s)', value=data['muffle']['contents'])
    await ctx.respond(embed=embed)


@get_command.command(description="List the prefixes for the transformed user")
async def prefixes(ctx: discord.ApplicationContext,
                   user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user, True)
    if not valid:
        return
    if not data['prefix']:
        await ctx.respond(f"{user.mention} has no prefixes at the moment!")
        return
    embed = utils.get_embed_base(f"Prefixes for {user.name}")
    embed.add_field(name='Prefix', value='\n'.join(data['prefix']['contents']))
    await ctx.respond(embed=embed)


@get_command.command(description="List the suffixes for the transformed user")
async def suffixes(ctx: discord.ApplicationContext,
                   user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user, True)
    if not valid:
        return
    if not data['suffix']:
        await ctx.respond(f"{user.mention} has no suffixes at the moment!")
        return
    embed = utils.get_embed_base(f"Suffixes for {user.name}")
    embed.add_field(name='Suffix', value='\n'.join(data['suffix']['contents']))
    await ctx.respond(embed=embed)


@get_command.command(description="Get the biography of a transformed user")
async def bio(ctx: discord.ApplicationContext,
              user: discord.Option(discord.User) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user, True)
    if not valid:
        return
    if data['bio'].strip() in ["", None]:
        await ctx.respond(f"{user.mention} has no biography set!")
        return
    embed = utils.get_embed_base(f"Biography for {user.name}")
    embed.add_field(name="", value=data['bio'])
    await ctx.respond(embed=embed)


@get_command.command(description="Get a list of transformed users")
async def transformed(ctx: discord.ApplicationContext) -> None:
    tfee_data = utils.load_transformed(ctx.guild)['transformed_users']
    if not tfee_data:
        await ctx.respond("No one is transformed (globally) at the moment!")
        return
    description = ""
    for tfee in tfee_data:
        transformed_data = utils.load_tf_by_id(tfee, ctx.guild)
        transformed_data = transformed_data[str(ctx.channel.id) if str(ctx.channel.id) in transformed_data else 'all']
        into = transformed_data['into']
        description += f"**{tfee}** -> *{into}*\n\n"
    # Take off the last two new lines
    description = description[:-2]
    await ctx.respond(embed=utils.get_embed_base("Transformed Users", description))


# "Admin" Commands
admin_command = bot.create_group("admin", "Admin commands for the bot")


@admin_command.command(description="Kill all webhooks, and let the bot regenerate them")
@discord.default_permissions(administrator=True)
async def killhooks(ctx: discord.ApplicationContext) -> None:
    for wh in await ctx.guild.webhooks():
        if wh.name == WEBHOOK_NAME:  # Delete only our webhooks, which all *should* have the same name
            await wh.delete()
    await ctx.respond("All webhooks have been deleted! The bot will regenerate them as needed.", ephemeral=True)


@admin_command.command(description="(Un)block a channel from being users being transformed in")
@discord.default_permissions(administrator=True)
async def block_channel(ctx: discord.ApplicationContext,
                        channel: discord.TextChannel = None) -> None:
    if channel is None:
        channel = ctx.channel
    utils.write_transformed(ctx.guild, block_channel=channel)
    data = utils.load_transformed(ctx.guild)['blocked_channels']
    word = "blocked" if str(channel.id) in data else "unblocked"
    await ctx.respond(f"{channel.mention} has been {word}!", ephemeral=True)


@admin_command.command(description="(Un)block a user from being transformed in this server")
@discord.default_permissions(administrator=True)
async def block_user(ctx: discord.ApplicationContext,
                     user: discord.User) -> None:
    utils.write_transformed(ctx.guild, block_user=user)
    data = utils.load_transformed(ctx.guild)['blocked_users']
    word = "blocked" if str(user.id) in data else "unblocked"
    await ctx.respond(f"{user.mention} has been {word}!", ephemeral=True)


# Misc commands
@bot.slash_command(description="Set a channel where you just wanna be yourself")
async def block_channel(ctx: discord.ApplicationContext,
                        channel: discord.TextChannel = None) -> None:
    if channel is None:
        channel = ctx.channel
    utils.write_tf(ctx.author, ctx.guild, block_channel=channel)
    word = "yourself" if str(channel.id) in utils.load_tf(ctx.user, ctx.guild)['blocked_channels'] else "transformed"
    channel_word = "this channel" if channel == ctx.channel else channel.mention
    await ctx.respond(f"You will now be {word} in {channel_word}!")


@bot.slash_command(description="Report a user for misuse of this bot")
async def report(ctx: discord.ApplicationContext,
                 user: discord.User,
                 reason: discord.SlashCommandOptionType.string) -> None:
    if reason.strip() == "":
        await ctx.respond("Please provide a valid reason for the report!")
        return
    await ctx.respond(
        "Are you sure you want to report this user? This will send a message to the server owner, and to "
        "the bot developers, with the reason you provided. This action is irreversible. If we find this "
        "is a false report, we will take action against you. Please confirm this action by typing "
        "\"CONFIRM\".", ephemeral=True
    )
    response = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    if response.content.strip() != "CONFIRM":
        await ctx.send("Cancelled the report!")
        return
    await ctx.channel.delete_messages([response])  # Delete confirmation message, for privacy

    embed = utils.get_embed_base("RECEIVED A REPORT")
    embed.add_field(name="Reported User", value=user.mention)
    embed.add_field(name="Reporter", value=ctx.author.mention)
    embed.add_field(name="Reason", value=reason)
    await ctx.guild.owner.send(embed=embed)

    # Dev data
    embed.add_field(name="Server", value=ctx.guild.name)
    embed.add_field(name="Server Owner", value=ctx.guild.owner.mention)
    await bot.get_channel(USER_REPORTS_CHANNEL_ID).send(embed=embed)

    await ctx.respond("Report sent! Thank you for helping us keep this bot safe!", ephemeral=True)


@bot.slash_command(description="See information about the bot")
async def info(ctx: discord.ApplicationContext) -> None:
    embed = utils.get_embed_base("Info", "> \"Let's get transforming!\"")
    embed.add_field(name="Original Creators", value="<@770662556456976415>\n<@250982256976330754>")
    embed.add_field(name="Logo by", value="<@317115440180494337>")
    embed.add_field(name="Source Code", value="[GitHub](https://github.com/dorythecat/transformate)")
    embed.add_field(name="Official Discord Server", value="[Join here!](https://discord.gg/uGjWk2SRf6)")
    await ctx.respond(embed=embed)


@bot.slash_command(description="Invite the bot to your server")
async def invite(ctx: discord.ApplicationContext) -> None:
    await ctx.respond("You can't invite this bot yet, since we're under development, still. :(")


@bot.slash_command(description="Replies with the bot's latency.")
async def ping(ctx: discord.ApplicationContext) -> None:
    await ctx.respond(f"Pong! ({bot.latency * 1000:.0f}ms)")


# Start the bot up
load_dotenv()
bot.run(os.getenv("BOT_TOKEN"))

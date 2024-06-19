import os
import aiohttp
import discord

import utils

from dotenv import load_dotenv

# SETTINGS
WEBHOOK_NAME: str = "TransforMate Webhook"  # Name to use for the webhooks
BLOCKED_USERS: list[int] = [  # Users that are blocked from using the bot, for whatever reason.
    967123840587141181
]
USER_REPORTS_CHANNEL_ID: int = 1252358817682030743  # Channel to use for the /report command

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

    utils.write_tf(user, ctx.guild, channel, transformed_by=str(ctx.author.id), into=into.strip(), image_url=image_url)
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
    if ctx.user.id in BLOCKED_USERS:
        await ctx.respond(f"You're blocked from using this bot at all! You must've done something very bad...")
        return
    if user.id in BLOCKED_USERS:
        await ctx.respond(f"You can't transform that user at all! They've been very naughty...")
        return

    if utils.is_transformed(user, ctx.guild):
        if channel_id in data:
            data = data[channel_id]
        elif 'all' in data:
            data = data['all']
        else:
            return
        if data['claim'] not in ["", None] and data['claim'] != ctx.author.name and data['eternal']:
            if ctx.author.name != user.name:
                await ctx.respond(f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
                return
            await ctx.respond(f"Your master can't allow you to transform, at least for now...")
            return

    if into:
        if len(into) <= 1:
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
        if data['into'] in ["", None]:
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
    if data['claim'] not in ["", None] and data['claim'] != ctx.author.name:
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
    if data['claim'] in ["", None]:
        await ctx.respond(f"{user.mention} is currently not claimed by anyone!")
        return
    if data['claim'] != ctx.author.name:
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
    if data['claim'] in ["", None] and not data['eternal']:
        await ctx.respond(f"You can't do that! You are not claimed by anyone! Stop trying to abuse! >:(")
        return
    utils.write_tf(ctx.author, ctx.guild, channel, claim_user="", eternal=0)
    await ctx.respond(f"You have successfully activated the safeword command.\n"
                      f"Please, sort out any issues with your rp partner(s) before you continue using the bot .\n"
                      f"Use \"/goback\" to return to your normal self.")


bot.load_extension('cogs.set')  # "Set" Commands
bot.load_extension('cogs.clear')  # "Clear" Commands
bot.load_extension('cogs.get')  # "Get" Commands
bot.load_extension('cogs.admin')  # "Admin" Commands


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

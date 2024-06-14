import os
import utils

from dotenv import load_dotenv

import discord



COMMAND_PREFIX = "!"

intents = discord.Intents.all()

bot = discord.Bot(intents=intents)


# Transformation functions
async def transform_function(ctx: discord.ApplicationContext,
                             user: discord.User,
                             into: str,
                             image_url: str):
    if not image_url:
        image_url = user.avatar.url
    if image_url[:4] != "http":
        return await ctx.send("Invalid URL! Please provide a valid image URL!")
    if "?" in image_url:
        image_url = image_url[:image_url.index("?")]  # Prune url

    utils.write_tf(user, ctx.guild, None, ctx.author.name, into, image_url)
    utils.write_transformed(user, ctx.guild)


# Bot startup
@bot.event
async def on_ready():
    print(f'\nSuccessfully logged into Discord as "{bot.user}"\n')
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.watching,
                                                        name="people get transformed"))


# Message sent
@bot.event
async def on_message(message: discord.Message):
    # Check if the message is sent by the bot, we don't want an endless loop that ends on an error/crash, do we?
    if message.author == bot.user:
        return

    # Check if user is transformed, and send their messages as webhooks, deleting the original
    if utils.is_transformed(message.author, message.guild):
        if message.content.startswith('. '):
            return
        data = utils.load_tf(message.author, message.guild)
        if str(message.channel.id) in data:
            data = data[str(message.channel.id)]
        elif 'all' in data:
            data = data['all']
        else:
            return
        name = data['into']
        image_url = data['image_url']

        webhook = utils.get_webhook_by_name(await message.channel.webhooks(), name)
        if not webhook:
            webhook = await message.channel.create_webhook(name=name)

        if message.content:  # If there's no content, and we try to send it, it will trigger a 400 error
            if message.reference:
                await webhook.send(f"**Replying to {message.reference.resolved.author.mention}:**\n",
                                   avatar_url=image_url)
                if message.reference.resolved.content:
                    await webhook.send(f">>> {message.reference.resolved.content}",
                                       avatar_url=image_url, wait=True)
            await webhook.send(utils.transform_text(data, message.content), avatar_url=image_url, wait=True)
        for attachment in message.attachments:
            if (attachment.url[:attachment.url.index("?")] if "?" in attachment.url else attachment.url) == image_url:
                return
            await webhook.send(file=await attachment.to_file(), avatar_url=image_url)
        await message.delete()

        if message.stickers:
            await message.author.send("Sorry, but we don't support stickers, at the moment! :(")


# Reaction added
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    # Check if reaction is reacting to a message sent by a transformed user
    if str(reaction.emoji) == "❓":
        transformed = utils.load_transformed(reaction.message.guild)
        for tfed in transformed:
            data = utils.load_tf_by_name(tfed, reaction.message.guild)
            if str(reaction.message.channel.id) in data:
                data = data[str(reaction.message.channel.id)]
            elif 'all' in data:
                data = data['all']
            else:
                return
            if data['into'] == reaction.message.author.name:
                await user.send(f"*{reaction.message.author.name}* is, in fact, *{tfed}*!\n"
                                f"(Transformed by *{data['transformed_by']}*)")
                await reaction.remove(user)


# Transformation commands
@bot.slash_command(description="Transform someone")
async def transform(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None,
                    into: discord.Option(discord.SlashCommandOptionType.string,
                                         description="Who to transform") = None,
                    image_url: discord.Option(discord.SlashCommandOptionType.string,
                                              description="Image URL to use") = None):
    if not user:
        user = ctx.author

    if utils.is_transformed(user, ctx.guild):
        data = utils.load_tf(user, ctx.guild)
        if str(ctx.channel.id) in data:
            data = data[str(ctx.channel.id)]
        elif 'all' in data:
            data = data['all']
        else:
            return
        if data['claim'] is not None and data['claim'] != ctx.author.name:
            return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}!")
        if data['eternal'] and ctx.author.name != data['claim']:
            if ctx.author.name != user.name:
                return await ctx.respond(
                    f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
            return await ctx.respond(f"Your master can't allow you to transform, at least for now...")

    if into:
        if len(into.strip()) <= 1:
            return await ctx.send("Please provide a name longer than 1 character!")
        await transform_function(ctx, user, into, image_url)
        await ctx.respond(f'You have transformed {user.mention} into "{into}"!')
        return

    await ctx.respond(f"What do we want to transform {user.mention} into? (Send CANCEL to cancel)")
    response = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    if response.content.strip() == "CANCEL":
        return await ctx.respond("Cancelled the transformation!")
    if len(response.content.strip()) <= 1:
        return await ctx.send("Please provide a name longer than 1 character!")
    await transform_function(ctx,
                             user,
                             response.content,
                             response.attachments[0].url if response.attachments else None)
    await ctx.respond(f'You have transformed {user.mention} into "{response.content}"!')


@bot.slash_command(description="Return someone to their previous state")
async def goback(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    data = utils.load_tf(user, ctx.guild)
    if str(ctx.channel.id) in data:
        data = data[str(ctx.channel.id)]
    elif 'all' in data:
        data = data['all']
    else:
        return await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to!"
                                 f"(At least on this channel)")
    into = data['into']

    if not utils.is_transformed(user, ctx.guild):
        if into == "":
            return await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to!")
        utils.write_transformed(user, ctx.guild)
        return await ctx.respond(f"{user.mention} has been turned back to their last form!")

    if data['eternal'] and ctx.author.name != data['claim']:
        if ctx.author.name != user.name:
            return await ctx.respond(
                f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
        return await ctx.respond(f"Your master won't allow you to turn back, at least for now...")

    utils.remove_transformed(user, ctx.guild)

    # Delete all webhooks with the same name
    # This can lead to deleting more webhooks than we need to, but it shouldn't cause too much of a performance hit
    for wh in await ctx.guild.webhooks():
        if wh.name == into:
            await wh.delete()
    await ctx.respond(f"{user.mention} has been turned back to normal!")


@bot.slash_command(description="Get a list of transformed users")
async def listtransformed(ctx: discord.ApplicationContext):
    transformed = utils.load_transformed(ctx.guild)
    if not transformed:
        return await ctx.respond("No one is transformed (globally) at the moment!")
    to_send = "The following people are transformed (globally) at the moment:\n"
    for tfed in transformed:
        data = utils.load_tf_by_name(tfed, ctx.guild)
        for channel in data:
            if channel == 'all':
                data = data[channel]
                break
        to_send += f"**{tfed}** has been transformed into *{data['into']}* by *{data['transformed_by']}*\n"
    await ctx.respond(to_send)


@bot.slash_command(description="Claim a transformed user")
async def claim(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User)):
    if user == ctx.author:
        return await ctx.respond(f"You can't claim yourself!")
    if not utils.is_transformed(user, ctx.guild):
        return await ctx.respond(f"{user.mention} is not transformed at the moment, you can't claim them!")
    data = utils.load_tf(user, ctx.guild)
    channel = None
    if str(ctx.channel) in data:
        data = data[str(ctx.channel)]
        channel = ctx.channel
    else:
        data = data['all']
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} has been claimed already by {data['claim']}!")
    utils.write_tf(user, ctx.guild, channel, claim_user=ctx.author.name)
    await ctx.respond(f"You have successfully claimed {user.mention} for yourself! Hope you enjoy!")


@bot.slash_command(description="Unclaim a transformed user")
async def unclaim(ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User)):
    if user == ctx.author:
        return await ctx.respond(f"You can't unclaim yourself! Only your master can do that!\n"
                                 f"||Use \"/safeword\", if you actually want to unclaim yourself.||")
    data = utils.load_tf(user, ctx.guild)
    channel = None
    if str(ctx.channel) in data:
        data = data[str(ctx.channel)]
        channel = ctx.channel
    else:
        data = data['all']
    if data['claim'] is None:
        return await ctx.respond(f"{user.mention} is currently not claimed by anyone!")
    if data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is claimed by {data['claim']}, not you!")
    utils.write_tf(user, ctx.guild, channel, claim_user="", eternal=0)
    await ctx.respond(f"You have successfully unclaimed {user.mention}! They are now free from your grasp!")


@bot.slash_command(description="Safeword command. Use in case of abuse or incomodity, to unclaim yourself.")
async def safeword(ctx: discord.ApplicationContext):
    data = utils.load_tf(ctx.author, ctx.guild)
    channel = None
    if str(ctx.channel) in data:
        data = data[str(ctx.channel)]
        channel = ctx.channel
    else:
        data = data['all']
    # We have to check if they are claimed OR eternally transformed. If both are false, safeword does nothing.
    # If either are true, we need to keep going, otherwise we can just return.
    if data['claim'] is None and not data['eternal']:
        return await ctx.respond(f"You can't do that! You are not claimed by anyone!")
    utils.write_tf(ctx.author, ctx.guild, channel, claim_user="", eternal=0)
    await ctx.respond(f"You have successfully activated the safeword command.\n"
                      f"Please, sort out any issues with your rp partner(s) before you continue using the bot .\n"
                      f"Use \"/goback\" to return to your normal self.")


# "Set" Commands
set_command = bot.create_group("set", "Set various things about transformed users")


@set_command.command(description="Set a prefix for the transformed messages")
async def prefix(ctx: discord.ApplicationContext,
                 prefix: discord.Option(discord.SlashCommandOptionType.string,
                                        description="Prefix to add"),
                 user: discord.Option(discord.User) = None,
                 whitespace: discord.Option(discord.SlashCommandOptionType.boolean,
                                            description="Add a space after the prefix (defaults true)") = True):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    if whitespace:
        prefix = prefix + " "
    utils.write_tf(user, ctx.guild, prefix=prefix)
    await ctx.respond(f"Prefix for {user.mention} set to \"*{prefix}*\"!")


@set_command.command(description="Set a suffix for the transformed messages")
async def suffix(ctx: discord.ApplicationContext,
                 suffix: discord.Option(discord.SlashCommandOptionType.string,
                                        description="Suffix to add"),
                 user: discord.Option(discord.User) = None,
                 whitespace: discord.Option(discord.SlashCommandOptionType.boolean,
                                            description="Add a space before the suffix (defaults true)") = True):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    if whitespace:
        suffix = " " + suffix
    utils.write_tf(user, ctx.guild, suffix=suffix)
    await ctx.respond(f"Suffix for {user.mention} set to \"*{suffix}*\"!")



@set_command.command(description="Set the transformed user to speak in big text")
async def big(ctx: discord.ApplicationContext,
              user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if data['big']:
        return await ctx.respond(f"{user.mention} is already speaking big!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, big=1)
    await ctx.respond(f"{user.mention} will now speak in big text!")


@set_command.command(description="Set the transformed user to speak in small text")
async def small(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if data['small']:
        return await ctx.respond(f"{user.mention} is already speaking small!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, small=1)
    await ctx.respond(f"{user.mention} will now speak in small text!")


@set_command.command(description="Set the transformed user to hush")
async def hush(ctx: discord.ApplicationContext,
               user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if data['hush']:
        return await ctx.respond(f"{user.mention} is already hushed!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, hush=1)
    await ctx.respond(f"{user.mention} will now hush!")


@set_command.command(description="Set the transformed user to be eternally transformed")
async def eternal(ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User)):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if data['eternal']:
        return await ctx.respond(f"{user.mention} is already eternally transformed!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, eternal=1)
    await ctx.respond(f"{user.mention} is now eternally transformed!")

@set_command.command(description="Set the transformed user to be censored")
async def censor(ctx: discord.ApplicationContext,
                    censor: discord.Option(discord.SlashCommandOptionType.string,
                                            description="Word to censor"),
                    replacement: discord.Option(discord.SlashCommandOptionType.string,
                                                description="Word to replace with"),
                    user: discord.Option(discord.User) = None):
        if user is None:
            user = ctx.author
        transformed = utils.load_transformed(ctx.guild)
        if user.name not in transformed:
            return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
        data = utils.load_tf(user, ctx.guild)
        data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
        if data['claim'] is not None and data['claim'] != ctx.author.name:
            return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
        utils.write_tf(user, ctx.guild, censor=censor, censor_replacement=replacement)
        await ctx.respond(f"{user.mention} will now have the word \"{censor}\" censored to \"{replacement}\"!")

@set_command.command(description="Set the transformed user to have specific words sprinkled in their messages")
async def sprinkle(ctx: discord.ApplicationContext,
                    sprinkle: discord.Option(discord.SlashCommandOptionType.string,
                                            description="Word to sprinkle"),
                    user: discord.Option(discord.User) = None):
        if user is None:
            user = ctx.author
        transformed = utils.load_transformed(ctx.guild)
        if user.name not in transformed:
            return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
        data = utils.load_tf(user, ctx.guild)
        data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
        if data['claim'] is not None and data['claim'] != ctx.author.name:
            return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
        utils.write_tf(user, ctx.guild, sprinkle=sprinkle)
        await ctx.respond(f"{user.mention} will now have the word \"{sprinkle}\" sprinkled in their messages!")

@set_command.command(description="Set the transformed user to have their words randomly replaced with a specific set of words")
async def muffle(ctx: discord.ApplicationContext,
                    muffle: discord.Option(discord.SlashCommandOptionType.string,
                                            description="Word that will replace words"),
                    user: discord.Option(discord.User) = None):
        if user is None:
            user = ctx.author
        transformed = utils.load_transformed(ctx.guild)
        if user.name not in transformed:
            return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
        data = utils.load_tf(user, ctx.guild)
        data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
        if data['claim'] is not None and data['claim'] != ctx.author.name:
            return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
        utils.write_tf(user, ctx.guild, muffle=muffle)
        await ctx.respond(f"{user.mention} will now have their words muffled with \"{muffle}\"!")

# TODO: Add commands to remove individual censors, sprinkles, muffle, etc.
# TODO: Add commands to list censors, sprinkles, muffle, etc.
# TODO: Add commands to set chances for each to proc.

# "Clear" commands
clear_command = bot.create_group("clear", "Clear various things about transformed users")


@clear_command.command(description="Clear all settings for the transformed user")
async def all_fields(ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
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
                   muffle="")


@clear_command.command(description="Clear the prefix for the transformed messages")
async def prefix(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if data['prefix'] is None:
        return await ctx.respond(f"{user.mention} doesn't have a prefix set!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, prefix="")
    await ctx.respond(f"Prefix for {user.mention} has been cleared!")


@clear_command.command(description="Clear the suffix for the transformed messages")
async def suffix(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    if data['suffix'] is None:
        return await ctx.respond(f"{user.mention} doesn't have a suffix set!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, suffix="")
    await ctx.respond(f"Suffix for {user.mention} has been cleared!")


@clear_command.command(description="Clear the big text setting for the transformed messages")
async def big(ctx: discord.ApplicationContext,
              user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)    
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if not data['big']:
        return await ctx.respond(f"{user.mention} doesn't have big text set!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, big=0)
    await ctx.respond(f"{user.mention} will no longer speak in big text!")


@clear_command.command(description="Clear the small text setting for the transformed messages")
async def small(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if not data['small']:
        return await ctx.respond(f"{user.mention} doesn't have small text set!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, small=0)
    await ctx.respond(f"{user.mention} will no longer speak in small text!")


@clear_command.command(description="Clear hush setting")
async def hush(ctx: discord.ApplicationContext,
               user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if not data['hush']:
        return await ctx.respond(f"{user.mention} doesn't have hush set!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, hush=0)
    await ctx.respond(f"{user.mention} will no longer hush!")


@clear_command.command(description="Clear eternal setting")
async def eternal(ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User)):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if not data['eternal']:
        return await ctx.respond(f"{user.mention} isn't eternally transformed!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, eternal=0)
    await ctx.respond(f"{user.mention} is no longer eternally transformed!")

# Misc commands
@bot.slash_command(description="Replies with the bot's latency.")
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond(f"Pong! ({bot.latency * 1000:.0f}ms)")


@bot.slash_command(description="Kill all webhooks, and let the bot regenerate them")
@discord.default_permissions(administrator=True)
async def killhooks(ctx: discord.ApplicationContext):
    for wh in await ctx.guild.webhooks():
        await wh.delete()
    await ctx.respond("All webhooks have been deleted! The bot will regenerate them as needed.")


# Start the bot up
load_dotenv()
bot.run(os.getenv("BOT_TOKEN"))

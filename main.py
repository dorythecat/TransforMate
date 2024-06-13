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
    if len(into.strip()) <= 1:
        return await ctx.send("Please provide a name longer than 1 character!")

    if not image_url:
        image_url = user.avatar.url
    if image_url[:4] != "http":
        return await ctx.send("Invalid URL! Please provide a valid image URL!")
    if "?" in image_url:
        image_url = image_url[:image_url.index("?")]  # Prune url

    utils.write_tf(user, ctx.guild, ctx.author.name, into, image_url)
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
        tf_data = utils.load_tf(message.author, message.guild)
        name = tf_data['into']
        image_url = tf_data['image_url']

        webhook = utils.get_webhook_by_name(await message.channel.webhooks(), name)
        if not webhook:
            webhook = await message.channel.create_webhook(name=name)

        if message.content:  # If there's no content and we try to send, it will trigger a 400 error
            if message.reference:
                await webhook.send(f"**Replying to {message.reference.resolved.author.mention}:**\n"
                                   f">>> {message.reference.resolved.content})")
            await webhook.send(utils.transform_text(tf_data, message.content), avatar_url=image_url)
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
        transformed = utils.get_transformed(reaction.message.guild)
        for tfed in transformed:
            tf_data = utils.load_tf_by_name(tfed, reaction.message.guild)
            if tf_data['into'] == reaction.message.author.name:
                await user.send(f"*{reaction.message.author.name}* is, in fact, *{tfed}*!\n"
                                f"(Transformed by *{tf_data['transformed_by']}*)")
                await reaction.remove(user)


# Transformation commands
@bot.slash_command(description="Transform someone")
async def transform(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None,
                    into: discord.Option(discord.SlashCommandOptionType.string, description="Who to transform") = None,
                    image_url: discord.Option(discord.SlashCommandOptionType.string,
                                              description="Image URL to use") = None):
    if not user:
        user = ctx.author

    if utils.is_transformed(user, ctx.guild):
        data = utils.load_tf(user, ctx.guild)
        if data['eternal'] and ctx.author.name != data['claim']:
            if ctx.author.name != user.name:
                return await ctx.respond(
                    f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
            return await ctx.respond(f"Your master can't allow you to transform, at least for now...")

    if into:
        await transform_function(ctx, user, into, image_url)
        await ctx.respond(f'You have transformed {user.mention} into "{into}"!')
        return

    await ctx.respond(f"What do we want to transform {user.mention} into? (Send CANCEL to cancel)")
    response = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    if response.content.strip() == "CANCEL":
        return await ctx.respond("Cancelled the transformation!")
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
    into = utils.load_tf(user, ctx.guild)['into']

    if not utils.is_transformed(user, ctx.guild):
        if into == "":
            return await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to!")
        utils.write_transformed(user, ctx.guild)
        return await ctx.respond(f"{user.mention} has been turned back to their last form!")

    data = utils.load_tf(user, ctx.guild)
    if data['eternal'] and ctx.author.name != data['claim']:
        if ctx.author.name != user.name:
            return await ctx.respond(
                f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
        return await ctx.respond(f"Your master can't allow you to turn back, at least for now...")

    utils.remove_transformed(user, ctx.guild)

    # Delete all webhooks with the same name
    # This can lead to deleting more webhooks than we need to, but it shouldn't cause too much of a performance hit
    for wh in await ctx.guild.webhooks():
        if wh.name == into:
            await wh.delete()
    await ctx.respond(f"{user.mention} has been turned back to normal!")


@bot.slash_command(description="Get a list of transformed users")
async def listtransformed(ctx: discord.ApplicationContext):
    transformed = utils.get_transformed(ctx.guild)
    if not transformed:
        return await ctx.respond("No one is transformed at the moment!")
    await ctx.respond("The following people are transformed at the moment:\n" + "".join(transformed))


@bot.slash_command(description="Claim a transformed user")
async def claim(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User)):
    if user == ctx.author:
        return await ctx.respond(f"You can't claim yourself!")
    if not utils.is_transformed(user, ctx.guild):
        return await ctx.respond(f"{user.mention} is not transformed at the moment, you can't claim them!")
    data = utils.load_tf(user, ctx.guild)
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} has been claimed already by {data['claim']}!")
    utils.write_tf(user, ctx.guild, claim_user=ctx.author.name, eternal=1)
    await ctx.respond(f"You have successfully claimed {user.mention} for yourself! Hope you enjoy!")


@bot.slash_command(description="Unclaim a transformed user")
async def unclaim(ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User)):
    if user == ctx.author:
        return await ctx.respond(f"You can't unclaim yourself! Only your master can do that!\n"
                                 f"||Use \"/safeword\", if you actually want to unclaim yourself.||")
    data = utils.load_tf(user, ctx.guild)
    if data['claim'] is None:
        return await ctx.respond(f"{user.mention} is currently not claimed by anyone!")
    if data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is claimed by {data['claim']}, not you!")
    utils.write_tf(user, ctx.guild, claim_user="", eternal=0)
    await ctx.respond(f"You have successfully unclaimed {user.mention}! They are now free from your grasp!")


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
    transformed = utils.get_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
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
    transformed = utils.get_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
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
    transformed = utils.get_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
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
    transformed = utils.get_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
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
    transformed = utils.get_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    if data['hush']:
        return await ctx.respond(f"{user.mention} is already hushed!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, hush=1)
    await ctx.respond(f"{user.mention} will now hush!")


# "Clear" commands
clear_command = bot.create_group("clear", "Clear various things about transformed users")


@clear_command.command(description="Clear all settings for the transformed user")
async def all_fields(ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    transformed = utils.get_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
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
    transformed = utils.get_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
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
    transformed = utils.get_transformed(ctx.guild)
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
    transformed = utils.get_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
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
    transformed = utils.get_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
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
    transformed = utils.get_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    if not data['hush']:
        return await ctx.respond(f"{user.mention} doesn't have hush set!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, hush=0)
    await ctx.respond(f"{user.mention} will no longer hush!")


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

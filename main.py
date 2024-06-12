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
        name = tf_data["into"]
        avatar_url = tf_data["image_url"]

        webhook = utils.get_webhook_by_name(await message.channel.webhooks(), name)
        if not webhook:
            webhook = await message.channel.create_webhook(name=name)

        if message.content:  # If there's no content and we try to send, it will trigger a 400 error
            await webhook.send(message.content, username=name, avatar_url=avatar_url)
        if message.attachments:  # Send attachments too, even if in separate messages
            for attachment in message.attachments:
                await webhook.send(file=await attachment.to_file(), username=name, avatar_url=avatar_url)
        if message.stickers:
            await message.author.send("Sorry, but we don't support stickers, at the moment! :(")
        await message.delete()


# Reaction added
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    # Check if reaction is reacting to a message sent by a transformed user
    if str(reaction.emoji) == "❓":
        transformed = utils.get_transformed(reaction.message.guild)
        for tfed in transformed:
            tf_data = utils.load_tf_by_name(tfed, reaction.message.guild)
            if tf_data["into"] == reaction.message.author.name:
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


@bot.slash_command(description="Return someone to their previous state")
async def goback(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    into = utils.load_tf(user, ctx.guild)["into"]

    if not utils.is_transformed(user, ctx.guild):
        if into == "":
            return await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to!")
        utils.write_transformed(user, ctx.guild)
        return await ctx.respond(f"{user.mention} has been turned back to their last form!")

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


# Misc commands
@bot.slash_command(description="Replies with the bot's latency.")
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond(f"Pong! ({bot.latency * 1000:.0f}ms)")


# Start the bot up
load_dotenv()
bot.run(os.getenv("BOT_TOKEN"))

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

    with open(f"cache/people/{user.name}.txt", "w+") as f:
        f.write(into)
        f.write("\n")
        f.write(image_url if image_url else user.avatar.url)

    with open("cache/transformed.txt", "r+") as f:
        if user.name not in f.read():
            f.write(user.name)
            f.write("\n")


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
    with open("cache/transformed.txt", "r") as f1:
        if message.author.name in f1.read():
            with open(f"cache/people/{message.author.name}.txt", "r") as f2:
                lines = f2.readlines()
                name = lines[0].strip()
                avatar_url = lines[1].strip()

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


# Transformation commands
@bot.slash_command(description="Transform someone")
async def transform(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None,
                    into: discord.Option(discord.SlashCommandOptionType.string, description="Who to transform") = None,
                    image_url: discord.Option(discord.SlashCommandOptionType.string, description="Image URL to use") = None):
    if not user:
        user = ctx.author

    if into:
        await transform_function(ctx, user, into, image_url)
        await ctx.respond(f'You have transformed {user.mention} into "{into}"!')
        return

    await ctx.respond(f"What do we want to transform {user.mention} into?")
    response = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    await transform_function(ctx,
                             user,
                             response.content,
                             response.attachments[0].url if response.attachments else None)


@bot.slash_command(description="Return someone to their previous state")
async def goback(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author

    with open("cache/transformed.txt", "r+") as f:
        lines = f.readlines()

        # Empty the file
        f.seek(0)
        f.truncate()

        found = False
        for line in lines:
            if line.strip() != user.name:
                f.write(line)
            else:
                found = True
        if not found:
            with open(f"cache/people/{user.name}.txt", "r") as f2:
                if f2.read().strip() == "":
                    return await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to!")
            f.write(user.name)
            f.write("\n")
            return await ctx.respond(f"{user.mention} has been turned back to their last form!")

    # Keep the transformation file, just in case the user wants to go back again to their transformed form
    with open(f"cache/people/{user.name}.txt", "r") as f:
        name = f.readlines()[0].strip()

    # Delete all webhooks with the same name
    # This can lead to deleting more webhooks than we need to, but it shouldn't cause too much of a performance hit
    for wh in await ctx.guild.webhooks():
        if wh.name == name:
            await wh.delete()
    await ctx.respond(f"{user.mention} has been turned back to normal!")


# Misc commands
@bot.slash_command(description="Replies with the bot's latency.")
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond(f"Pong! ({bot.latency * 1000:.0f}ms)")


# Start the bot up
load_dotenv()
bot.run(os.getenv("BOT_TOKEN"))

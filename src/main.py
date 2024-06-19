import aiohttp
import discord

import utils
from config import *

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)


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
    if str(reaction.emoji) not in ["❓", "❔", "🔒", "🔓", "🔐"] or not reaction.message.author.bot or \
            reaction.message.author == bot.user:
        return

        # Check if reaction is reacting to a message sent by a transformed user
        # I know this isn't the most efficient method, but it's really the best we have, at least for now
        # TODO: Find a better way to do this (maybe?)
    tfee, data = utils.check_reactions(reaction)
    if not tfee:
        return
    if str(reaction.emoji) in ["❓", "❔"]:
        await user.send(f"\"{reaction.message.author.name}\" is, in fact, {bot.get_user(tfee).mention}!\n"
                        f"(Transformed by {bot.get_user(int(data['transformed_by'])).mention})")
        await reaction.remove(user)
        return
    data_claim = data['claim']
    if str(reaction.emoji) == "🔒":
        if data_claim not in ["", None]:
            await user.send(f"\"{reaction.message.author.name}\" is already claimed by {data_claim}!")
            await reaction.remove(user)
            return
        utils.write_tf(bot.get_user(tfee), reaction.message.guild, claim_user=user.name)
        await user.send(f"Successfully claimed \"{reaction.message.author.name}\" for yourself!")
        await reaction.message.channel.send(f"{user.mention} has claimed \"{reaction.message.author.name}\"!")
        await reaction.remove(user)
    elif str(reaction.emoji) == "🔓":
        if data_claim in ["", None]:
            await user.send(f"\"{reaction.message.author.name}\" is not claimed by anyone!")
            await reaction.remove(user)
            return
        if data_claim != user.name:
            await user.send(f"\"{reaction.message.author.name}\" is claimed by {data_claim}! You can't unclaim them!")
            await reaction.remove(user)
            return
        utils.write_tf(bot.get_user(tfee), reaction.message.guild, claim_user="", eternal=0)
        await user.send(f"Successfully unclaimed \"{reaction.message.author.name}\"!")
        await reaction.message.channel.send(f"{user.mention} has unclaimed \"{reaction.message.author.name}\"!")
        await reaction.remove(user)
    elif str(reaction.emoji) == "🔐":
        if data['eternal']:
            if data_claim != user.name:
                await user.send(f"\"{reaction.message.author.name}\" is eternally transformed by {data_claim}!"
                                f"You can't free them!")
                await reaction.remove(user)
                return
            # Clear the eternal transformation
            utils.write_tf(bot.get_user(tfee), reaction.message.guild, eternal=0)
            await user.send(f"Successfully un-eternally transformed \"{reaction.message.author.name}\"!")
            await reaction.message.channel.send(f"{user.mention} has un-eternally transformed"
                                                f"\"{reaction.message.author.name}\"!")
            await reaction.remove(user)
            return
        utils.write_tf(bot.get_user(tfee), reaction.message.guild, eternal=1, claim_user=user.name)
        await user.send(f"Successfully eternally transformed \"{reaction.message.author.name}\"!")
        await reaction.message.channel.send(f"{user.mention} has eternally transformed"
                                            f"\"{reaction.message.author.name}\"!")
        await reaction.remove(user)


bot.load_extension('cogs.transformation')  # Transformation (base) Commands
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


bot.run(BOT_TOKEN)  # Start the bot up

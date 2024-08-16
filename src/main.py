import discord

import utils
from config import *

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)


@bot.event
async def on_ready() -> None:
    print(f'\nSuccessfully logged into Discord as "{bot.user}"\n')
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.watching,
                                                        name="people get transformed"))


@bot.event
async def on_message(message: discord.Message) -> None:
    # Check if the message is sent by the bot, we don't want an endless loop that ends on an error/crash, do we?
    if message.author == bot.user:
        return

    if not message.guild:  # DMs
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

            embed = utils.get_embed_base(title="RECEIVED A REPORT", color=discord.Color.dark_red())
            embed.add_field(name="Reported User", value=user.mention)
            embed.add_field(name="Reporter", value=message.author.mention)
            embed.add_field(name="Reason", value=reason.content.strip())
            embed.add_field(name="Reported in DMs", value="")
            await bot.get_channel(USER_REPORTS_CHANNEL_ID).send(embed=embed)
            await message.author.send("Thank you for your report! It has been sent to the developers, for review.")
        return

    # Check if the message was sent by a bot
    # We use this to delete logs made by other bots, if this setting is enabled
    transformed_data = utils.load_transformed(message.guild)
    if message.author.bot and transformed_data != {} and transformed_data['clear_other_logs']:
        if message.author.id == 1273264155482390570:  # Dyno bot
            if message.embeds and message.embeds[0].description.__contains__("Deleted"):
                if utils.is_transformed(discord.utils.get(bot.get_all_members(), name=message.embeds[0].author.name),
                                        message.guild,
                                        message.channel):
                    await message.delete()
        return

    # Check if user is transformed
    if not utils.is_transformed(message.author, message.guild, message.channel) or \
            message.content.strip().startswith('('):
        return

    # If the message contains stickers, we just don't process it
    if message.stickers:
        await message.author.send("Sorry, but we don't support  sending stickers, for the moment! :(")
        return

    data = utils.load_tf(message.author, message.guild)
    if data == {}:  # User isn't transformed
        return

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

    # Check if affixes are enabled, and if they are, check if the message contains them
    if transformed_data['affixes']:
        if data['proxy_prefix'] != "":
            if message.content.startswith(data['proxy_prefix']):
                message.content = message.content[len(data['proxy_prefix']):]
            else:
                return
        if data['proxy_suffix'] != "":
            if message.content.endswith(data['proxy_suffix']):
                message.content = message.content[:-len(data['proxy_suffix'])]
            else:
                return

    name = data['into']
    image_url = data['image_url']

    is_thread = message.channel.type in [discord.ChannelType.private_thread, discord.ChannelType.public_thread]
    channel = message.channel.parent if is_thread else message.channel

    webhook = utils.get_webhook_by_name(await channel.webhooks(), WEBHOOK_NAME)
    if not webhook:
        webhook = await channel.create_webhook(name=WEBHOOK_NAME)

    content = ""
    if message.reference:  # Check if the message is a reply
        content += f"**Replying to {message.reference.resolved.author.mention}:**\n"
        if message.reference.resolved.content:
            content += f">>> {message.reference.resolved.content}"
            # If we don't send this by itself, we'll get fucked over by the multi-line quote, sorry everyone :(
            await webhook.send(content,
                               username=name,
                               avatar_url=image_url,
                               thread=message.channel if is_thread else discord.utils.MISSING)
            content = ""

    if message.content:
        # Check if censor, muffles, alt muffle, or sprinkles are active in data
        if (
                data['censor']['active'] or
                data['muffle']['active'] or
                data['alt_muffle']['active'] or
                data['sprinkle']['active']
        ):
            # Send the original message to transformed_by if claim is None, otherwise to claim
            if data['claim'] in ["", None]:
                # Get the user who transformed this user
                transformed_by = bot.get_user(int(data['transformed_by']))
            else:
                # Get the user who claimed the user
                transformed_by = bot.get_user(int(data['claim']))
            # Check if the message is from the user who transformed this user
            if not message.author == transformed_by:
                # DM the user who transformed this user the original message they sent
                await transformed_by.send(
                    f"**{message.author.name}** said in #**{channel.name}**:\n```{message.content}```")

        content += utils.transform_text(data, message.content)

    attachments = []
    for attachment in message.attachments:
        attachment_file = await attachment.to_file()
        attachments.append(attachment_file)

    # The message needs to either havbe content or attachments (or both) to be sent,
    # so we don't need to worry about sending empty messages and triggering 400 errors
    await webhook.send(content,
                       username=name,
                       avatar_url=image_url,
                       files=attachments,
                       thread=message.channel if is_thread else discord.utils.MISSING)
    await message.delete()


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User) -> None:
    if reaction.message.author == bot.user or not reaction.message.author.bot or \
            str(reaction.emoji) not in ["❓", "❔", "✏️", "❌", "🔒", "🔓", "🔐"]:
        return

    tfee, data = utils.check_reactions(reaction)
    if tfee is None:
        return
    await reaction.remove(user)  # Remove the reaction from the message

    # Message related reactions
    if str(reaction.emoji) in ["❓", "❔"]:
        await user.send(f"\"{reaction.message.author.name}\" is, in fact, {bot.get_user(tfee).mention}!\n"
                        f"(Transformed by {bot.get_user(int(data['transformed_by'])).mention})")
        return

    if str(reaction.emoji) == "✏️":
        # Edit message
        if user.id == tfee:
            # Editing messages that are not the last one will cause weird behaviours, so we prevent that by checking
            if reaction.message.channel.last_message_id != reaction.message.id:
                await user.send("You cannot edit this message! Sorry! :(")
                return
            await user.send(f"You have requested to edit the following message:\n"
                            f"\"{reaction.message.content}\"\n"
                            f"Please provide the edited message you want to send.")
            response = await bot.wait_for('message', check=lambda m: m.author == user)
            # Send the message through the webhook
            is_thread = reaction.message.channel.type in [discord.ChannelType.private_thread,
                                                          discord.ChannelType.public_thread]
            channel = reaction.message.channel.parent if is_thread else reaction.message.channel

            webhook = utils.get_webhook_by_name(await channel.webhooks(), WEBHOOK_NAME)
            if not webhook:
                webhook = await channel.create_webhook(name=WEBHOOK_NAME)

            await webhook.send(response.content,
                               username=data['into'],
                               avatar_url=data['image_url'],
                               thread=(reaction.message.channel if is_thread else discord.utils.MISSING))
            await reaction.message.delete()  # Delete the original message
            await user.send("Message edited successfully!")

            transformed_data = utils.load_transformed(reaction.message.guild)
            if transformed_data['logs'][0]:
                embed = utils.get_embed_base(title="Message Edited")
                embed.add_field(name="User", value=user.mention)
                embed.add_field(name="Original Message", value=reaction.message.content)
                embed.add_field(name="Edited Message", value=response.content)
                embed.add_field(name="Channel", value=reaction.message.channel.mention)
                await bot.get_channel(transformed_data['logs'][0]).send(embed=embed)
        return

    if str(reaction.emoji) == "❌":
        if user.id == tfee:
            await reaction.message.delete()
            await user.send("Message deleted successfully!")

            transformed_data = utils.load_transformed(reaction.message.guild)
            if transformed_data['logs'][1]:
                embed = utils.get_embed_base(title="Message Deleted", color=discord.Color.red())
                embed.add_field(name="User", value=user.mention)
                embed.add_field(name="Message", value=reaction.message.content)
                embed.add_field(name="Channel", value=reaction.message.channel.mention)
                await bot.get_channel(transformed_data['logs'][1]).send(embed=embed)
        return

    # Claim related reactions
    data_claim = data['claim']
    transformed_data = utils.load_transformed(reaction.message.guild)
    if str(reaction.emoji) == "🔒":
        if data_claim not in ["", None]:
            await user.send(f"\"{reaction.message.author.name}\" is already claimed by {data_claim}!")
            return
        utils.write_tf(bot.get_user(tfee), reaction.message.guild, claim_user=user.name)
        await user.send(f"Successfully claimed \"{reaction.message.author.name}\" for yourself!")
        await reaction.message.channel.send(f"{user.mention} has claimed \"{reaction.message.author.name}\"!")

        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Claimed", color=discord.Color.gold())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Claimed User", value=reaction.message.author.mention)
            embed.add_field(name="Channel", value=reaction.message.channel.mention)
            await bot.get_channel(transformed_data['logs'][3]).send(embed=embed)

        return

    if str(reaction.emoji) == "🔓":
        if data_claim in ["", None]:
            await user.send(f"\"{reaction.message.author.name}\" is not claimed by anyone!")
            return
        if data_claim != user.name:
            await user.send(f"\"{reaction.message.author.name}\" is claimed by {data_claim}! You can't unclaim them!")
            return
        utils.write_tf(bot.get_user(tfee), reaction.message.guild, claim_user="", eternal=0)
        await user.send(f"Successfully unclaimed \"{reaction.message.author.name}\"!")
        await reaction.message.channel.send(f"{user.mention} has unclaimed \"{reaction.message.author.name}\"!")

        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Unclaimed", color=discord.Color.gold())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Unclaimed User", value=reaction.message.author.mention)
            embed.add_field(name="Channel", value=reaction.message.channel.mention)
            await bot.get_channel(transformed_data['logs'][3]).send(embed=embed)

        return

    if str(reaction.emoji) == "🔐":
        if data['eternal']:
            if data_claim != user.name:
                await user.send(f"\"{reaction.message.author.name}\" is eternally transformed by {data_claim}!"
                                f"You can't free them!")
                return
            # Clear the eternal transformation
            utils.write_tf(bot.get_user(tfee), reaction.message.guild, eternal=0)
            await user.send(f"Successfully un-eternally transformed \"{reaction.message.author.name}\"!")
            await reaction.message.channel.send(f"{user.mention} has un-eternally transformed"
                                                f"\"{reaction.message.author.name}\"!")
            return
        utils.write_tf(bot.get_user(tfee), reaction.message.guild, eternal=1, claim_user=user.name)
        await user.send(f"Successfully eternally transformed \"{reaction.message.author.name}\"!")
        await reaction.message.channel.send(f"{user.mention} has eternally transformed"
                                            f"\"{reaction.message.author.name}\"!")

        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Eternally Transformed", color=discord.Color.gold())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Eternally Transformed User", value=reaction.message.author.mention)
            embed.add_field(name="Channel", value=reaction.message.channel.mention)
            await bot.get_channel(transformed_data['logs'][3]).send(embed=embed)


bot.load_extension('cogs.transformation')  # Transformation (base) Commands
bot.load_extension('cogs.set')  # "Set" Commands
bot.load_extension('cogs.clear')  # "Clear" Commands
bot.load_extension('cogs.get')  # "Get" Commands
bot.load_extension('cogs.admin')  # "Admin" Commands
bot.load_extension('cogs.block')  # "Block" Commands


# Misc commands
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

    embed = utils.get_embed_base(title="RECEIVED A REPORT", color=discord.Color.dark_red())
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
    embed = utils.get_embed_base(title="Info", desc="> \"Let's get transforming!\"")
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

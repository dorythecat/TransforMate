import discord
import os

# Make sure we're on the proper working directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
if os.name == "nt":
    os.chdir("\\".join(dname.split("\\")[:-1]))
else:
    os.chdir("/".join(dname.split("/")[:-1]))

from pathlib import Path

import utils as utils
from config import *

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready() -> None:
    print(f'\nSuccessfully logged into Discord as "{bot.user}"\n')
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.watching,
                                                        name="people get transformed"))

    # Generate the cache/people dirs so we don't have to worry about them further down the line
    Path("../cache/people").mkdir(parents=True, exist_ok=True)


# TODO: When the bot joins a server, we should check if it has the proper permissions, and then warn the owner of
# features that might be disabled.
@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    await guild.owner.send("# Thanks for adding the TransforMate bot to your server!\n"
                           "By having the bot on your server, you agree to our [Terms of Service]"
                           "(https://github.com/dorythecat/TransforMate/blob/main/legal/TERMS_OF_SERVICE.md), "
                           "and to our [Privacy Policy]"
                           "(https://github.com/dorythecat/TransforMate/blob/main/legal/PRIVACY_POLICY.md).\n"
                           "Check them anytime with the /legal command\n\n"
                           "We hope you enjoy this bot and all of its functions, and remember to always use it "
                           "with respect and consent from other users, and never for nefarious purposes!")

@bot.event
async def on_guild_remove(guild: discord.Guild) -> None:
    for member in guild.members:
        utils.remove_all_server_tf(member, guild)
    utils.remove_server_from_transformed(guild)

# We use on_raw_member_remove instead of on_member_remove because only the first will ALWAYS trigger
# See https://docs.pycord.dev/en/stable/api/events.html#discord.on_member_remove
@bot.event
async def on_raw_member_remove(payload: discord.RawMemberRemoveEvent) -> None:
    utils.remove_all_server_tf(payload.user, bot.get_guild(payload.guild_id))

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
            if message.embeds and "Deleted" in message.embeds[0].description:
                if utils.is_transformed(discord.utils.get(bot.get_all_members(), name=message.embeds[0].author.name),
                                        message.guild):
                    await message.delete()
        return

    # Check if user is transformed
    if not utils.is_transformed(message.author, message.guild):
        return

    # Check if user is using OOC mode
    if message.content.startswith("(") or message.content.startswith("\\"):
        return

    data = utils.load_tf(message.author, message.guild)
    if data == {}:  # User isn't transformed
        return

    # Handle blocked channels
    # Not necessary to check for blocked users, since they shouldn't be able to use the bot anyway
    if 'blocked_channels' not in data:
        data['blocked_channels'] = []
    if str(message.channel.id) in data['blocked_channels'] + utils.load_transformed(message.guild)['blocked_channels']:
        return

    # If the message contains stickers, we just don't process it
    if message.stickers:
        await message.author.send("Sorry, but we don't support sending stickers, for the moment! :(")
        return

    name = data['into']
    image_url = data['image_url']

    is_thread = message.channel.type in [discord.ChannelType.private_thread, discord.ChannelType.public_thread]
    channel = message.channel.parent if is_thread else message.channel

    webhook = await utils.get_webhook_by_name(channel, WEBHOOK_NAME)

    content = ""
    if message.reference:  # Check if the message is a reply
        mention = message.reference.resolved.author.mention
        if message.reference.resolved.webhook_id and not message.reference.resolved.author == bot.user:
            tfee, _ = utils.check_message(message.reference.resolved)
            mention = f"<@{tfee}>"
        content += (f"***Replying to {mention} on "
                    f"{message.reference.resolved.jump_url}:***\n")
        # TODO: Make this an option for server owners
        '''
        if message.reference.resolved.content:
            to_send = message.reference.resolved.content
            if message.reference.resolved.mentions:
                for mention in message.reference.resolved.mentions:
                    # This avoids people abusing mentions found in messages they are replying to
                    to_send = to_send.replace(mention.mention, f"@{mention.name}")
            to_send = to_send.split('\n')
            if to_send[0].startswith('***Replying to'):
                for line in to_send[1:]:
                    if line.startswith('> '):
                        continue
                    to_send = to_send[(to_send.index(line) + 1):] #  We add one to account for the blank line
                    break
            for line in to_send:
                if line.startswith('> '):
                    line = line[2:]
                elif line.startswith('>>> '):
                    line = line[4:]
                content += f"> {line}\n"
            content += "\n"
        '''

    if message.content:
        tfed_content = utils.transform_text(data, message.content)
        content += tfed_content

        # Check if censors, muffles, alt muffles, or sprinkles are active in data, and if the message is different from
        # the original, to send it to the author of the transformation
        if (data['censor'] != {} or
            data['muffle'] != {} or
            data['alt_muffle'] != {} or
            data['sprinkle'] != {}) and tfed_content != message.content:
            # Send the original message to transformed_by if claim is None, otherwise to claim
            transformed_by = bot.get_user(int(data['transformed_by'] if data['claim'] is None else data['claim']))

            # Check if the message is from the user who transformed this user
            if transformed_by not in [None, message.author]:
                # DM the user who transformed this user the original message they sent
                await transformed_by.send(
                    f"**{message.author.mention}** said in #**{channel.name}**:\n```{message.content}```")

    if len(content) > 2000:
        await message.author.send("Sorry, but your final message is too long to be sent!")
        return

    # The message needs to either have content or attachments (or both) to be sent,
    # so we don't need to worry about sending empty messages and triggering 400 errors
    await webhook.send(content,
                       username=name,
                       avatar_url=image_url,
                       files=[await attachment.to_file() for attachment in message.attachments],
                       thread=message.channel if is_thread else discord.utils.MISSING)
    await message.delete()


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User) -> None:
    if reaction.message.author == bot.user or not reaction.message.author.bot or \
            str(reaction.emoji) not in ["❓", "❔", "✏️", "❌", "🔒", "🔓", "🔐"]:
        return

    tfee, data = utils.check_message(reaction.message)
    if tfee is None:
        return
    await reaction.remove(user) # Remove the reaction from the message

    # Message related reactions
    if str(reaction.emoji) in ["❓", "❔"]:
        await user.send(f"\"{reaction.message.author.name}\" is, in fact, <@!{tfee}>!\n"
                        f"(Transformed by <@!{data['transformed_by']}>)")
        return

    if str(reaction.emoji) == "✏️":
        if user.id != tfee:
            return
        # Editing messages that are not the last one will cause weird behaviours, so we prevent that by checking
        await user.send(f"You have requested to edit the following message:\n"
                        f"\"{reaction.message.content}\"\n"
                        f"Please provide the edited message you want to send.")
        response = await bot.wait_for('message', check=lambda m: m.author == user and
                                                                       m.channel.type == discord.ChannelType.private)
        # Send the message through the webhook
        is_thread = reaction.message.channel.type in [discord.ChannelType.private_thread,
                                                      discord.ChannelType.public_thread]
        channel = reaction.message.channel.parent if is_thread else reaction.message.channel

        webhook = await utils.get_webhook_by_name(channel, WEBHOOK_NAME)

        attachments = []
        for attachment in response.attachments:
            attachment_file = await attachment.to_file()
            attachments.append(attachment_file)

        await webhook.edit_message(reaction.message.id, content=response.content, files=attachments)
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
        if data_claim not in ["", 0]:
            await user.send(f"\"{reaction.message.author.name}\" is already claimed by {bot.get_user(data_claim).mention}!")
            return
        utils.write_tf(bot.get_user(tfee), reaction.message.guild, claim_user=user.id)
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
        if data_claim in ["", 0]:
            await user.send(f"\"{reaction.message.author.name}\" is not claimed by anyone, at the moment!")
            return
        if data_claim != user.name:
            await user.send(f"\"{reaction.message.author.name}\" is claimed by {data_claim}! You can't unclaim them!")
            return
        utils.write_tf(bot.get_user(tfee), reaction.message.guild, claim_user=0, eternal=False)
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
            utils.write_tf(bot.get_user(tfee), reaction.message.guild, eternal=False)
            await user.send(f"Successfully un-eternally transformed \"{reaction.message.author.name}\"!")
            await reaction.message.channel.send(f"{user.mention} has un-eternally transformed"
                                                f"\"{reaction.message.author.name}\"!")
            return
        utils.write_tf(bot.get_user(tfee), reaction.message.guild, eternal=True, claim_user=user.id)
        await user.send(f"Successfully eternally transformed \"{reaction.message.author.name}\"!")
        await reaction.message.channel.send(f"{user.mention} has eternally transformed"
                                            f"\"{reaction.message.author.name}\"!")

        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Eternally Transformed", color=discord.Color.gold())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Eternally Transformed User", value=reaction.message.author.mention)
            embed.add_field(name="Channel", value=reaction.message.channel.mention)
            await bot.get_channel(transformed_data['logs'][3]).send(embed=embed)


bot.load_extension('.transformation', package='cogs')  # Transformation (base) Commands
bot.load_extension('.set', package='cogs')  # "Set" Commands
bot.load_extension('.clear', package='cogs')  # "Clear" Commands
bot.load_extension('.get', package='cogs')  # "Get" Commands
bot.load_extension('.admin', package='cogs')  # "Admin" Commands
bot.load_extension('.block', package='cogs')  # "Block" Commands


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
    embed.add_field(name="official Documentation", value="https://dorythecat.github.io/TransforMate/")
    embed.add_field(name="Official Discord Server", value="[Join here!](https://discord.gg/uGjWk2SRf6)")
    embed.add_field(name="Support the project!", value="[Patreon](https://www.patreon.com/dorythecat)")
    await ctx.respond(embed=embed)

@bot.slash_command(description="Legal stuff, so fun!")
async def legal(ctx: discord.ApplicationContext) -> None:
    desc = "By using this bot you agree to our "
    desc += "[Terms of Service](https://dorythecat.github.io/TransforMate/legal/tos.html) and our "
    desc += "[Privacy Policy](https://dorythecat.github.io/TransforMate/legal/privacy_policy.html)"
    embed = utils.get_embed_base(title="Legal Stuff",desc=desc)
    await ctx.respond(embed=embed)

@bot.slash_command(description="Invite the bot to your server")
async def invite(ctx: discord.ApplicationContext) -> None:
    await ctx.respond("To invite the bot to a server you own, use "
                      "[this link](https://discord.com/oauth2/authorize?client_id=1274436972621987881)!\n\n"
                      "Feel free to share it around with anyone! <3")


@bot.slash_command(description="Replies with the bot's latency.")
async def ping(ctx: discord.ApplicationContext) -> None:
    await ctx.respond(f"Pong! ({bot.latency * 1000:.0f}ms)")



if __name__ == "__main__":
    bot.run(BOT_TOKEN)  # Start the bot up
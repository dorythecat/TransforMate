import discord
import os

# Make sure we're on the proper working directory
sep = "\\" if os.name == "nt" else "/"
os.chdir(sep.join(os.path.dirname(os.path.abspath(__file__)).split(sep)[:-1]))

from pathlib import Path

import utils
from config import *

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

MAX_ITEMS_PER_PAGE: int = 10 # Max items per page for views

class PageView(discord.ui.View):
    embed_title: str = ""
    desc_list: list[str] = []
    total: int = 0
    offset: int = 0

    def __init__(self, embed_title: str, desc_list: list[str], total: int, offset: int = MAX_ITEMS_PER_PAGE) -> None:
        super().__init__(timeout=None)
        self.embed_title = embed_title
        self.desc_list = desc_list
        self.total = total
        self.offset = offset

    @discord.ui.button(label="⬅️ Previous Page", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_button_callback(self, button: discord.Button, interaction: discord.Interaction) -> None:
        if self.offset <= MAX_ITEMS_PER_PAGE:
            return
        self.next_button_callback.disabled = False
        self.offset -= MAX_ITEMS_PER_PAGE * 2
        desc = "\n\n".join(self.desc_list[self.offset:self.offset + MAX_ITEMS_PER_PAGE])
        footer = f"Page {self.offset // MAX_ITEMS_PER_PAGE + 1} of {(self.total - 1) // MAX_ITEMS_PER_PAGE + 1}"
        self.offset += MAX_ITEMS_PER_PAGE
        await interaction.response.edit_message(embed=utils.get_embed_base(self.embed_title, desc, footer), view=self)
        if self.offset <= MAX_ITEMS_PER_PAGE:
            button.disabled = True
            await interaction.message.edit(view=self)

    @discord.ui.button(label="Next Page ➡️", style=discord.ButtonStyle.primary)
    async def next_button_callback(self, button: discord.Button, interaction: discord.Interaction) -> None:
        if self.offset >= self.total:
            return
        self.previous_button_callback.disabled = False
        desc = "\n\n".join(self.desc_list[self.offset:self.offset + MAX_ITEMS_PER_PAGE])
        footer = f"Page {self.offset // MAX_ITEMS_PER_PAGE + 1} of {(self.total - 1) // MAX_ITEMS_PER_PAGE + 1}"
        self.offset += MAX_ITEMS_PER_PAGE
        await interaction.response.edit_message(embed=utils.get_embed_base(self.embed_title, desc, footer), view=self)
        if self.offset >= self.total:
            button.disabled = True
            await interaction.message.edit(view=self)

@bot.event
async def on_ready() -> None:
    print(f'\nSuccessfully logged into Discord as "{bot.user}"\n')
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.watching,
                                                        name="people get transformed"))

    # Generate the cache/people dirs so we don't have to worry about them further down the line
    Path(f"{CACHE_PATH}/people").mkdir(parents=True, exist_ok=True)


@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    await guild.owner.send("# Thanks for adding the TransforMate bot to your server!\n"
                           "By having the bot on your server, you agree to our [Terms of Service]"
                           "(https://dorythecat.github.io/TransforMate/legal/tos), "
                           "and to our [Privacy Policy]"
                           "(https://dorythecat.github.io/TransforMate/legal/privacy_policy).\n"
                           "Check them anytime with the /legal command\n\n"
                           "We hope you enjoy this bot and all of its functions, and remember to always use it "
                           "with respect and consent from other users, and never for nefarious purposes!")

@bot.event
async def on_guild_remove(guild: discord.Guild) -> None:
    await guild.owner.send("We're sorry to see you go! If you have any feedback on why you decided to "
                           "remove the bot from your server, please, feel free to let us know, so we "
                           "can improve!\n\n [Official Discord Server](https://discord.gg/uGjWk2SRf6)")
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
            await message.author.send("Uh, oh! Do you want to report someone? If so, please provide the user ID, which "
                                      "you can get by right-clicking on their name and selecting \"Copy ID\".")
            user_id = await bot.wait_for('message', check=lambda m: m.author == message.author)
            if not user_id.content.isdigit():
                await message.author.send("That's not a valid user ID! Please try reporting another time!")
                return
            try:
                user: discord.User = await bot.fetch_user(int(user_id.content))
            except discord.errors.NotFound:
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
            embed.add_field(name="Reported in DMs", value=str(user.id))
            await bot.get_channel(USER_REPORTS_CHANNEL_ID).send(embed=embed)
            print(f"[REPORT] User {user} reported by {message.author} in DMs for reason: {reason.content.strip()}")
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

    # Check if channel is of a type we don't want to process
    if message.channel.type in [discord.ChannelType.news, discord.ChannelType.news_thread, discord.ChannelType.forum]:
        return

    if (not utils.is_transformed(message.author, message.guild) or # Check if user is transformed
        message.content.startswith("(") or message.content.startswith("\\")): # Check if user is using OOC mode
        return

    data = utils.load_tf(message.author, message.guild)
    if data == {}: # User isn't transformed
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

    is_thread = message.channel.type in [discord.ChannelType.private_thread, discord.ChannelType.public_thread]
    channel = message.channel.parent if is_thread else message.channel

    webhook = await utils.get_webhook_by_name(channel, WEBHOOK_NAME)

    content: str = ""
    if message.reference:  # Check if the message is a reply
        mention = f"***{message.reference.resolved.author.mention}***"
        if message.reference.resolved.webhook_id and not message.reference.resolved.author == bot.user:
            tfee, _ = utils.check_message(message.reference.resolved)
            mention = f'***"{message.reference.resolved.author.display_name}"***'
            if tfee is not None:
                mention = f"***<@{tfee}>***"
        content += (f"***Replying to {mention} on "
                    f"{message.reference.resolved.jump_url}:***\n")

    if message.content:
        tfed_content = utils.transform_text(data, message.content)
        content += tfed_content

        # Check if censors, muffles, alt muffles, or sprinkles are active in data, and if the message is different from
        # the original, to send it to the author of the transformation
        if (data['censor'] != {} or data['muffle'] != {} or data['alt_muffle'] != {} or
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
                       username=data['into'],
                       avatar_url=data['image_url'],
                       files=[await attachment.to_file() for attachment in message.attachments],
                       thread=message.channel if is_thread else discord.utils.MISSING)
    await message.delete()


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User) -> None:
    if reaction.message.author == bot.user or not reaction.message.author.bot or \
            str(reaction.emoji) not in ["❓", "❔", "✏️", "📝", "❌", "🔒", "🔓", "🔐"]:
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

    if str(reaction.emoji) in ["✏️", "📝"]:
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
bot.load_extension('.clear', package='cogs')  # "Clear" Commands
bot.load_extension('.admin', package='cogs')  # "Admin" Commands
bot.load_extension('.block', package='cogs')  # "Block" Commands


@bot.slash_command(description="Set settings for transformed users")
async def set(ctx: discord.ApplicationContext,
              user: discord.Option(discord.User,
                                   "User to apply modifier to, defaults to executor") = None,
              mod_type: discord.Option(str,
                                       "Type of the modifier to set",
                                       choices=[
                                           "prefix", "suffix", "big", "small", "hush", "backwards", "eternal",
                                           "censor", "sprinkle", "muffle", "alt_muffle", "stutter", "bio", "nickname"
                                       ]) = None,
              content: discord.Option(str,
                                      "Content of the modifier") = None,
              chance: discord.Option(float,
                                     "Chance of the modifier going off") = None,
              whitespace: discord.Option(bool,
                                         "Wether to add a whitespace to prefixes and suffixes") = True,
              replacement: discord.Option(str,
                                          "Replacmeent for censors") = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return

    if mod_type in ["prefix", "suffix"]:
        if content is None or chance is None or not 0 < chance < 100 or whitespace is None or replacement is not None:
            await ctx.respond("Please provide valid settings for this modifier!", ephemeral=True)
            return
        # Prefixes and Suffixes
        if mod_type == "prefix":
            content += " " * whitespace
            utils.write_tf(user, ctx.guild, prefix=content, chance=chance)
        else:
            content = " " * whitespace + content
            utils.write_tf(user, ctx.guild, suffix=content, chance=chance)
        await ctx.respond(f"Successfully set {mod_type} for {user.mention}!", ephemeral=True)
    elif mod_type in ["big", "small", "hush", "backwards", "eternal", "nickname"]:
        if content is not None or chance is not None or whitespace is not None or replacement is not None:
            await ctx.respond("You don't need to provide any values for this modifier!", ephemeral=True)
            return
        if data[mod_type]:
            await ctx.respond(f"{user.mention} already has the {mod_type} modifier set!", ephemeral=True)
            return
        if mod_type == "eternal":
            if data['claim'] == 0:
                await ctx.respond(f"{user.mention} isn't owned by anyone! Claim them to eternally transform them!",
                                  ephemeral=True)
                return
            utils.write_tf(user, ctx.guild, eternal=True)
            await ctx.respond(f"{user.mention} is now eternally transformed!")
        elif mod_type == "big":
            utils.write_tf(user, ctx.guild, big=True)
            await ctx.respond(f"{user.mention} will now speak in big text!")
        elif mod_type == "small":
            utils.write_tf(user, ctx.guild, small=True)
            await ctx.respond(f"{user.mention} will now speak in small text!")
        elif mod_type == "hush":
            utils.write_tf(user, ctx.guild, hush=True)
            await ctx.respond(f"{user.mention} will now be hushed!")
        elif mod_type == "backwards":
            utils.write_tf(user, ctx.guild, backwards=True)
            await ctx.respond(f"{user.mention} will now speak backwards!")
        elif mod_type == "nickname":
            await user.edit(nick=data['into'])
            await ctx.respond(f"{user.mention}'s nickname has been set to their transformed name!")
    elif mod_type in ["sprinkle", "muffle", "alt_muffle"]:
        if content is None or chance is None or not 0 < chance < 100 or whitespace is not None or replacement is not None:
            await ctx.respond("Please provide valid settings for this modifier!", ephemeral=True)
            return
        if mod_type == "sprinkle":
            utils.write_tf(user, ctx.guild, sprinkle=content, chance=chance)
            await ctx.respond(f"{user.mention} will now have the word \"{content}\" sprinkled in their messages!")
        elif mod_type == "muffle":
            utils.write_tf(user, ctx.guild, muffle=content, chance=chance)
            await ctx.respond(f"{user.mention} will now have their words muffled with \"{content}\"!")
        elif mod_type == "alt_muffle":
            utils.write_tf(user, ctx.guild, alt_muffle=content, chance=chance)
            await ctx.respond(f"{user.mention} will now have their words muffled with \"{content}\"!")
    elif mod_type == "censor":
        if content is None or chance is not None or whitespace is not None or replacement is None:
            await ctx.respond("Please provide valid settings for this modifier!", ephemeral=True)
            return
        utils.write_tf(user, ctx.guild, censor=content, censor_replacement=replacement)
        await ctx.respond(f"{user.mention} will now have the word \"{content}\" censored to \"{replacement}\"!")
    elif mod_type == "stutter":
        if content is not None or chance is None or not 0 < chance < 100 or whitespace is not None or replacement is not None:
            await ctx.respond("Please provide valid settings for this modifier!", ephemeral=True)
            return
        utils.write_tf(user, ctx.guild, stutter=chance)
        await ctx.respond(f"{user.mention} will now stutter in their messages!")
    elif mod_type == "bio":
        if content is None or chance is not None or whitespace is not None or replacement is not None:
            await ctx.respond("Please provide valid settings for this modifier!", ephemeral=True)
            return
        utils.write_tf(user, ctx.guild, bio=content)
        await ctx.respond(f"{user.mention}'s biography has been set!")
    else:
        await ctx.respond("Please provide a valid modifier type to set!", ephemeral=True)


@bot.slash_command(description="Clear settings for transformed users")
async def clear(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User,
                                     "User to apply modifier to, defaults to executor") = None,
                mod_type: discord.Option(str,
                                         "Type of the modifier to set",
                                         choices=[
                                             "all", "prefix", "suffix", "big", "small", "hush", "backwards", "eternal",
                                             "censor", "sprinkle", "muffle", "alt_muffle", "stutter", "bio", "nickname"
                                         ]) = None,
                content: discord.Option(str, "Content of modifier to remove") = "") -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user)
    if not valid:
        return
    if mod_type == "all":
        utils.write_tf(user,
                       ctx.guild,
                       claim_user=None, eternal=False,
                       prefix="", suffix="",
                       big=False, small=False, hush=False, backwards=False,
                       censor="",
                       sprinkle="",
                       muffle="",
                       alt_muffle="",
                       bio="")
        await ctx.respond(f"{user.mention} has been cleared of all settings!")
        return
    if not data[mod_type] or data[mod_type] == {}:
        await ctx.respond(f"{user.mention} doesn't have the \"{mod_type}\" modifier set!")
        return
    if mod_type in ["prefix", "suffix"]:
        if content != "":
            if not content in data[mod_type]:
                if (" " + content) in data[mod_type]:
                    content = " " + content
                elif (content + " ") in data[mod_type]:
                    content = content + " "
                else:
                    await ctx.respond(f"{user.mention} doesn't have that {mod_type} set!")
                    return
            content = "$/-" + content
        utils.write_tf(user, ctx.guild, **{mod_type: content})
    elif mod_type in ["big", "small", "hush", "backwards", "eternal"]:
        utils.write_tf(user, ctx.guild, **{mod_type: False})
    elif mod_type in ["sprinkle", "muffle", "alt_muffle", "censor"]:
        if content != "":
            if not content in data[mod_type]:
                await ctx.respond(f"{user.mention} doesn't have that {mod_type} set!")
                return
            content = "$/-" + content
        utils.write_tf(user, ctx.guild, **{mod_type: content})
    elif mod_type == "stutter":
        utils.write_tf(user, ctx.guild, stutter=0)
    elif mod_type == "bio":
        utils.write_tf(user, ctx.guild, bio="")
    elif mod_type == "nickname":
        await user.edit(nick=None)
    await ctx.respond(f"{" ".join(mod_type.split("_")).capitalize()} for {user.mention} has been cleared!")


@bot.slash_command(description="Get settings for transformed users")
async def get(ctx: discord.ApplicationContext,
              user: discord.Option(discord.User,
                                   "User to get modifier from, defaults to executor") = None,
              mod_type: discord.Option(str,
                                       "The setting to get",
                                       choices=[
                                           "all", "claim", "censor", "sprinkle", "muffle", "prefix", "suffix", "bio",
                                           "image", "tfed_users"
                                       ]) = None) -> None:
    valid, data, user = await utils.extract_tf_data(ctx, user, True)
    if not valid:
        return

    if mod_type == "all":
        embed = utils.get_embed_base(f"Settings for {user.name}:")
        embed.add_field(name="Prefix", value="Yes" if data['prefix'] != {} else "No")
        embed.add_field(name="Suffix", value="Yes" if data['suffix'] != {} else "No")
        embed.add_field(name="Big Text", value="Yes" if data['big'] else "No")
        embed.add_field(name="Small Text", value="Yes" if data['small'] else "No")
        embed.add_field(name="Hush", value="Yes" if data['hush'] else "No")
        embed.add_field(name="Backwards", value="Yes" if data['backwards'] else "No")
        embed.add_field(name="Censor", value="Yes" if data['censor'] != {} else "No")
        embed.add_field(name="Sprinkle", value="Yes" if data['sprinkle'] != {} else "No")
        embed.add_field(name="Muffle", value="Yes" if data['muffle'] != {} else "No")
        embed.add_field(name="Alt Muffle", value="Yes" if data['alt_muffle'] != {} else "No")
        embed.add_field(name="Stutter", value=f"{data['stutter']}%")
        await ctx.respond(embed=embed)
    elif mod_type == "claim":
        response: str = "isn't claimed by anyone!" if data['claim'] == 0 else f"is claimed by <@!{data['claim']}>!"
        await ctx.respond(f"{user.mention} {response}")
    elif mod_type in ["censor", "sprinkle", "muffle", "prefix", "suffix"]:
        mod_name: str = mod_type.capitalize() + ("es" if mod_type in ["prefix", "suffix"] else "s")
        if not data[mod_type]:
            await ctx.respond(f"{user.mention} has no {mod_name} at the moment!")
            return

        desc_list: list[str] = []
        for mod in data[mod_type]:
            desc_list.append(f"**{mod}**: {data[mod_type][mod]}{"" if mod_type == "censor" else "%"}")

        view: PageView | None = None
        footer: str | None = None
        mod_size: int = len(data[mod_type])
        if mod_size > MAX_ITEMS_PER_PAGE:
            view = PageView(f"{mod_name} for {user.name}:", desc_list, mod_size)
            footer = f"Page 1 of {(mod_size - 1) // MAX_ITEMS_PER_PAGE + 1}"
        await ctx.respond(embed=utils.get_embed_base(f"{mod_name} for {user.name}:",
                                                     "\n\n".join(desc_list[:MAX_ITEMS_PER_PAGE]),
                                                     footer), view=view)
    elif mod_type == "bio":
        if data['bio'] in ["", None]:
            await ctx.respond(f"{user.mention} has no biography set!")
            return
        await ctx.respond(embed=utils.get_embed_base(f"Biography for {user.name}:", data['bio']))
    elif mod_type == "image":
        await ctx.respond(f"{user.mention}'s image for [{data['into']}]({data['image_url']}):")
    elif mod_type == "tfed_users":
        tfee_data = utils.load_transformed(ctx.guild)['transformed_users']
        if tfee_data == {}:
            await ctx.respond("No one is transformed in this server, at the moment!")
            return

        users: int = 0
        desc: str = ""
        for tfee in tfee_data:
            transformed_data = utils.load_tf(int(tfee), ctx.guild)
            if transformed_data == {}:
                continue
            desc += f"<@!{tfee}> is \"{transformed_data['into']}\"\n\n"
            users += 1

        view: PageView | None = None
        footer: str | None = None
        if users > MAX_ITEMS_PER_PAGE:
            view = PageView("Transformed Users", desc, users)
            footer = f"Page 1 of {(users - 1) // MAX_ITEMS_PER_PAGE + 1}"
        desc = "\n\n".join(desc.split("\n\n")[:MAX_ITEMS_PER_PAGE])
        await ctx.respond(embed=utils.get_embed_base("Transformed Users", desc, footer), view=view)

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
    await ctx.channel.delete_messages([response]) # Delete confirmation message, for privacy

    embed = utils.get_embed_base(title="RECEIVED A REPORT", color=discord.Color.dark_red())
    embed.add_field(name="Reported User", value=user.mention)
    embed.add_field(name="Reporter", value=ctx.author.mention)
    embed.add_field(name="Reason", value=reason)
    await ctx.guild.owner.send(embed=embed)

    # Dev data
    embed.add_field(name=f"Reported on: **{ctx.guild.name}**", value=str(ctx.guild.id))
    embed.add_field(name="Server Owner", value=ctx.guild.owner.mention)
    await bot.get_channel(USER_REPORTS_CHANNEL_ID).send(embed=embed)

    # Print to console
    print(f"[REPORT] User {user} reported by {ctx.author} on server {ctx.guild.name} for reason: {reason}")

    await ctx.respond("Report sent! Thank you for helping us keep this bot safe!", ephemeral=True)


@bot.slash_command(description="See information about the bot")
async def info(ctx: discord.ApplicationContext) -> None:
    embed = utils.get_embed_base("Info", "> \"Let's get transforming!\"")
    embed.add_field(name="Original Creators", value="<@770662556456976415>\n<@250982256976330754>")
    embed.add_field(name="Logo by", value="<@317115440180494337>")
    embed.add_field(name="Source Code", value="[GitHub](https://github.com/dorythecat/transformate)")
    embed.add_field(name="Official Documentation", value="https://dorythecat.github.io/TransforMate/")
    embed.add_field(name="Official Discord Server", value="[Join here!](https://discord.gg/uGjWk2SRf6)")
    embed.add_field(name="Support the project!", value="[Patreon](https://www.patreon.com/dorythecat) | "
                                                       "[Official Shop](https://shop.transformate.live/)")
    await ctx.respond(embed=embed)

@bot.slash_command(description="Legal stuff, so fun!")
async def legal(ctx: discord.ApplicationContext) -> None:
    desc = "By using this bot you agree to our "
    desc += "[Terms of Service](https://dorythecat.github.io/TransforMate/legal/tos) and our "
    desc += "[Privacy Policy](https://dorythecat.github.io/TransforMate/legal/privacy_policy)"
    await ctx.respond(embed=utils.get_embed_base(title="Legal Stuff",desc=desc))

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

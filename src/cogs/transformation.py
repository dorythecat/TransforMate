import os

import discord
from discord.ext import commands

import utils
from config import BLOCKED_USERS


# Helper function
async def transform_function(ctx: discord.ApplicationContext,
                             user: discord.User,
                             into: str | None = None,
                             image_url: str | None = None,
                             channel: discord.TextChannel | None = None,
                             brackets: list[str] | None = None,
                             copy: discord.User | None = None,
                             merge: bool | None = None) -> bool:
    if copy is not None:
        new_data = utils.load_tf(copy, ctx.guild)
        if new_data == {} or new_data['all'] == {}:
            await ctx.respond("That user can't be copied, since hey don't have any transformation available!")
            return False
        if merge in [False, None]:
            new_data['all']['into'] += "឵឵ᅟ"
        if into:
            # Webhook username cannot contain "discord", or it will return a 400 error
            # TODO: Find a better fix, perhaps?
            if into.lower().__contains__("discord"):
                into = into.lower().replace("discord", "Disc0rd")
            new_data['all']['into'] = into
        if image_url:
            image_url = image_url.strip()
            if image_url[:4] != "http":
                await ctx.respond("Invalid Image URL! Please provide a valid image URL!")
                return False
            if "?" in image_url:  # Prune url, if possible, to preserve space
                image_url = image_url[:image_url.index("?")]
            new_data['all']['image_url'] = image_url
        utils.write_tf(user, ctx.guild, new_data=new_data)
        utils.write_transformed(ctx.guild, user, channel)
        return True
    if not into:
        await ctx.send("Please specify a name!")
        return False
    if not image_url:
        image_url = user.avatar.url if user.avatar is not None else "https://cdn.discordapp.com/embed/avatars/1.png"
    image_url = image_url.strip()
    if image_url[:4] != "http":
        await ctx.respond("Invalid Image URL! Please provide a valid image URL!")
        return False
    if "?" in image_url:  # Prune url, if possible, to preserve space
        image_url = image_url[:image_url.index("?")]

    # Webhook username cannot contain "discord", or it will return a 400 error
    # TODO: Find a better fix, perhaps?
    if into.lower().__contains__("discord"):
        into = into.lower().replace("discord", "Disc0rd")

    utils.write_tf(user,
                   ctx.guild,
                   channel,
                   transformed_by=str(ctx.author.id),
                   into=into.strip(),
                   image_url=image_url,
                   proxy_prefix=brackets[0] if brackets is not None else None,
                   proxy_suffix=brackets[1] if brackets is not None else None)
    utils.write_transformed(ctx.guild, user, channel)

    transformed_data = utils.load_transformed(ctx.guild)
    if transformed_data['logs'][2]:
        embed = discord.Embed(title="Transformed User", color=discord.Color.green())
        embed.add_field(name="User", value=user.mention)
        embed.add_field(name="Transformed By", value=ctx.author.mention)
        embed.add_field(name="Into", value=into)
        if brackets is not None:
            embed.add_field(name="Brackets", value=f"{brackets[0]}text{brackets[1]}")
        embed.set_image(url=image_url)
        await ctx.guild.get_channel(transformed_data['logs'][2]).send(embed=embed)

    return True


class Transformation(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @discord.slash_command(description="Transform someone")
    async def transform(self,
                        ctx: discord.ApplicationContext,
                        user: discord.Option(discord.User,
                                             description="Who to transform") = None,
                        into: discord.Option(discord.SlashCommandOptionType.string,
                                             description="What to trasnform them into") = None,
                        image_url: discord.Option(discord.SlashCommandOptionType.string,
                                                  description="Image URL to use") = None,
                        channel: discord.Option(discord.TextChannel,
                                                description="Transform the user only on this channel") = None,
                        brackets: discord.Option(discord.SlashCommandOptionType.string,
                                                 description="What brackets to use for this proxy."
                                                             "Ex: \"text\", Abc:text, etc."
                                                             "(Only available in certain servers)") = None,
                        copy: discord.Option(discord.User,
                                             description="Copy another user") = None,
                        merge: discord.Option(discord.SlashCommandOptionType.boolean,
                                              description="Whether to merge or not the user's messages to the"
                                                          "original transformed user's when copying") = None) -> None:
        if not user:
            user = ctx.author

        data = utils.load_tf(user, ctx.guild)
        transformed_data = utils.load_transformed(ctx.guild)
        channel_id = str(ctx.channel.id if not channel else channel.id)

        # Blocked users (globally)
        if ctx.user.id in BLOCKED_USERS:
            await ctx.respond(f"You're blocked from using this bot at all! You must've done something very bad..."
                              f"You might wanna appeal your ban in our Discord server, but, don't get your hopes up..."
                              f"||https://discord.gg/uGjWk2SRf6||", ephemeral=True)
            return
        if user.id in BLOCKED_USERS:
            await ctx.respond(f"You can't transform that user at all! They've been very naughty...", ephemeral=True)
            return

        # Blocked channels (user)
        if data != {}:
            if channel_id in data['blocked_channels']:
                await ctx.respond(f"You can't transform {user.mention} in this channel!"
                                  f"They have blocked the bot here!", ephemeral=True)
                return

        if transformed_data != {}:
            # Blocked channels (server)
            if channel_id in transformed_data['blocked_channels']:
                await ctx.respond(f"You can't use the bot, at least on this channel!", ephemeral=True)
                return

            # Blocked users (server)
            if str(ctx.user.id) in transformed_data['blocked_users']:
                await ctx.respond(f"You can't use the bot, at least on this server!", ephemeral=True)
                return
            if str(user.id) in transformed_data['blocked_users']:
                await ctx.respond(f"That user can't use the bot, at least on this server!", ephemeral=True)
                return

        if utils.is_transformed(user, ctx.guild):
            if channel_id in data:
                data = data[channel_id]
            elif 'all' in data:
                data = data['all']
            elif transformed_data != {} and transformed_data['affixes']:
                data = {'claim': None}  # Empty data so we can do multiple tfs
            elif data == {}:
                # This is to avoid https://github.com/dorythecat/TransforMate/issues/25
                data = { 'claim': None }
            else:
                await ctx.respond(f"{user.mention} is already transformed at the moment!")
                return
            if data['claim'] is not None and int(data['claim']) != ctx.author.id and data['eternal']:
                if ctx.author.name != user.name:
                    await ctx.respond(f"You can't do that! {user.mention} is eternally transformed by "
                                      f"{ctx.guild.get_member(int(data['claim'])).mention}!")
                    return
                await ctx.respond(f"Your master can't allow you to transform, at least for now...")
                return

        if transformed_data != {} and transformed_data['affixes']:
            if not brackets:
                await ctx.respond(f"Please provide brackets for this transformation!")
                return
            brackets = brackets.split("text")
            if len(brackets) > 2:
                await ctx.respond(f"Invalid brackets! Please provide valid brackets for this transformation!")
                return
        else:
            if brackets is not None:
                await ctx.respond(f"This server does not allow brackets for transformations!")
                return

        if into:
            if len(into) <= 1:
                await ctx.respond("Please provide a name longer than 1 character!")
            elif await transform_function(ctx, user, into, image_url, channel, brackets, None):
                await ctx.respond(f'You have transformed {user.mention} into "{into}"!')
            return

        if copy:
            if not utils.is_transformed(copy, ctx.guild):
                if await transform_function(ctx, user, into, image_url, channel, brackets, None, merge):
                    await ctx.respond(f'You have transformed {user.mention} into a copy of "{copy.mention}"!')
            elif await transform_function(ctx, user, into, image_url, channel, brackets, copy, merge):
                await ctx.respond(f'You have transformed {user.mention} into a copy of "{copy.name}"!')
            return

        # This avoids a bug with avatar images (See https://github.com/dorythecat/TransforMate/issues/16)
        # TODO: Find a better fix, perhaps?
        # IDEA: Make the bot use a "buffer channel", where it sends the image before the transformation is done.
        # This might be a horrible idea, or a great one, idk!
        if utils.is_transformed(ctx.author, ctx.guild):
            await ctx.respond(f"You can't transform someone (using this method) whilst you're transformed yourself!")
            return

        await ctx.respond(f"What do we want to transform {user.mention} into? (Send CANCEL to cancel)")
        response = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
        if response.content.strip() == "CANCEL":
            await ctx.respond("Cancelled the transformation!")
            return
        if len(response.content.strip()) <= 1:
            await ctx.respond("Please provide a name longer than 1 character!")
            return
        if await transform_function(ctx,
                                    user,
                                    response.content,
                                    response.attachments[0].url if response.attachments else None,
                                    channel,
                                    brackets,
                                    None):
            await ctx.respond(f'You have transformed {user.mention} into "{response.content}"!')

    @discord.slash_command(description="Return someone to their previous state")
    async def goback(self,
                     ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None) -> None:
        if user is None:
            user = ctx.author
        data = utils.load_tf(user, ctx.guild)
        transformed_data = utils.load_transformed(ctx.guild)
        channel = None
        if str(ctx.channel.id) in data:
            data = data[str(ctx.channel.id)]
            channel = ctx.channel
        elif 'all' in data:
            data = data['all']
        elif transformed_data != {} and not transformed_data['affixes']:
            await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to! "
                              f"(At least on this channel)")
            return
        else:
            data = {'claim': None, 'eternal': None, 'into': 'all'}  # Empty data so we can do multiple tfs

        if not utils.is_transformed(user, ctx.guild, ctx.channel) and not utils.is_transformed(user, ctx.guild):
            if data['into'] in ["", None]:
                await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to!")
                return
            utils.write_transformed(ctx.guild, user, channel)
            await ctx.respond(f"{user.mention} has been turned back to their last form!")

            transformed_data = utils.load_transformed(ctx.guild)
            if transformed_data['logs'][2]:
                embed = utils.get_embed_base(title="Transformed User", color=discord.Color.green())
                embed.add_field(name="User", value=user.mention)
                embed.add_field(name="Transformed By", value=ctx.author.mention)
                embed.add_field(name="Into", value="Their last form")
                await ctx.guild.get_channel(transformed_data['logs'][2]).send(embed=embed)

            return

        if data['eternal'] and int(data['claim']) != ctx.author.id:
            if ctx.author.name != user.name:
                await ctx.respond(f"You can't do that! {user.mention} is eternally transformed by "
                                  f"{ctx.guild.get_member(int(data['claim'])).mention}!")
                return
            await ctx.respond(f"Your master won't allow you to turn back, at least for now...")
            return

        utils.remove_transformed(user, ctx.guild, None if utils.is_transformed(user, ctx.guild) else ctx.channel)
        await ctx.respond(f"{user.mention} has been turned back to normal!")

        transformed_data = utils.load_transformed(ctx.guild)
        if transformed_data['logs'][2]:
            embed = utils.get_embed_base(title="Transformed User", color=discord.Color.green())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Transformed By", value=ctx.author.mention)
            embed.add_field(name="Into", value="Their normal self")
            await ctx.guild.get_channel(transformed_data['logs'][2]).send(embed=embed)

    @discord.slash_command(description="Claim a transformed user")
    async def claim(self,
                    ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User)) -> None:
        if user == ctx.author:
            await ctx.respond(f"You can't claim yourself!")
            return
        if not utils.is_transformed(user, ctx.guild, ctx.channel):
            await ctx.respond(f"{user.mention} is not transformed at the moment, you can't claim them!")
            return
        data = utils.load_tf(user, ctx.guild)
        channel = None
        if str(ctx.channel) in data:
            data = data[str(ctx.channel)]
            channel = ctx.channel
        elif 'all' in data:
            data = data['all']
        else:
            await ctx.respond("This user isn't transformed in this channel! Please try again in the proper channel!")
            return
        if data['claim'] is not None and int(data['claim']) != ctx.author.id:
            await ctx.respond(f"You can't do that! {user.mention} has been claimed already by "
                              f"{ctx.guild.get_member(int(data['claim'])).mention}!")
            return
        utils.write_tf(user, ctx.guild, channel, claim_user=ctx.author.id)
        await ctx.respond(f"You have successfully claimed {user.mention} for yourself! Hope you enjoy!")

        transformed_data = utils.load_transformed(ctx.guild)
        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Claimed", color=discord.Color.gold())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Claimed User", value=ctx.message.author.mention)
            embed.add_field(name="Channel", value=ctx.message.channel.mention)
            await ctx.guild.get_channel(transformed_data['logs'][3]).send(embed=embed)

    @discord.slash_command(description="Unclaim a transformed user")
    async def unclaim(self,
                      ctx: discord.ApplicationContext,
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
        if data['claim'] is None:
            await ctx.respond(f"{user.mention} is currently not claimed by anyone (yet)!")
            return
        if int(data['claim']) != ctx.author.id:
            await ctx.respond(f"You can't do that! {user.mention} is claimed by "
                              f"{ctx.guild.get_member(int(data['claim'])).mention}, not you!")
            return
        utils.write_tf(user, ctx.guild, channel, claim_user=None, eternal=0)
        await ctx.respond(f"You have successfully unclaimed {user.mention}! They are now free from your grasp!")

        transformed_data = utils.load_transformed(ctx.guild)
        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Unclaimed", color=discord.Color.gold())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Unclaimed User", value=ctx.message.author.mention)
            embed.add_field(name="Channel", value=ctx.message.channel.mention)
            await ctx.guild.get_channel(transformed_data['logs'][3]).send(embed=embed)

    @discord.slash_command(description="Safeword command. Use in case of abuse or incommodity, to unclaim yourself.")
    async def safeword(self,
                       ctx: discord.ApplicationContext) -> None:
        data = utils.load_tf(ctx.author, ctx.guild)
        channel = None
        if str(ctx.channel) in data:
            data = data[str(ctx.channel)]
            channel = ctx.channel
        else:
            data = data['all']
        # We have to check if they are claimed OR eternally transformed. If both are false, safeword does nothing.
        # If either are true, we need to keep going, otherwise we can just return.
        if data['claim'] is not None and not data['eternal']:
            await ctx.respond(f"You can't do that! You are not claimed by anyone! Stop trying to abuse! >:(")
            return
        utils.write_tf(ctx.author, ctx.guild, channel, claim_user=None, eternal=0)
        await ctx.respond(f"You have successfully activated the safeword command.\n"
                          f"Please, sort out any issues with your rp partner(s) before you continue using the bot .\n"
                          f"Use \"/goback\" to return to your normal self.")

        transformed_data = utils.load_transformed(ctx.guild)
        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Safeworded", color=discord.Color.gold())
            embed.add_field(name="User", value=ctx.author.mention)
            embed.add_field(name="Channel", value=ctx.message.channel.mention)
            await ctx.guild.get_channel(transformed_data['logs'][3]).send(embed=embed)

    # TF EXPORTING/IMPORTING
    @discord.slash_command(description="Export your transformation to a shareable file or text string")
    async def export_tf(self,
                     ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None,
                     file: discord.Option(discord.SlashCommandOptionType.boolean,
                                          description="Whether the output is a .tf file or a string") = True) -> None:
        if user is None:
            user = ctx.author

        # Blocked users (globally)
        if ctx.user.id in BLOCKED_USERS:
            await ctx.respond(f"You're blocked from using this bot at all! You must've done something very bad..."
                                f"You might wanna appeal your ban in our Discord server, but, don't get your hopes up..."
                                f"||https://discord.gg/uGjWk2SRf6||", ephemeral=True)
            return
        if user.id in BLOCKED_USERS:
            await ctx.respond(f"You can't transform that user at all! They've been very naughty...", ephemeral=True)
            return

        data = utils.load_tf(user, ctx.guild)
        transformed_data = utils.load_transformed(ctx.guild)

        # Blocked channels (user)
        if data != {}:
            if str(ctx.channel.id) in data['blocked_channels']:
                await ctx.respond(f"You can't transform {user.mention} in this channel!"
                                    f"They have blocked the bot here!", ephemeral=True)
                return

            if transformed_data != {}:
                # Blocked channels (server)
                if str(ctx.channel.id) in transformed_data['blocked_channels']:
                    await ctx.respond(f"You can't use the bot, at least on this channel!", ephemeral=True)
                    return

                # Blocked users (server)
                if str(ctx.user.id) in transformed_data['blocked_users']:
                    await ctx.respond(f"You can't use the bot, at least on this server!", ephemeral=True)
                    return
                if str(user.id) in transformed_data['blocked_users']:
                    await ctx.respond(f"That user can't use the bot, at least on this server!", ephemeral=True)
                    return

        data = utils.load_tf(user, ctx.guild)
        version = utils.get_data_version(user)
        channel = None
        if str(ctx.channel) in data:
            data = data[str(ctx.channel)]
            channel = ctx.channel
        else:
            data = data['all']

        # Basic stuff
        output = str(version) + ";"
        output += data['into'] + ";"
        output += data['image_url'] + ";"

        # Booleans
        output += "1;" if data['big'] else "0;"
        output += "1;" if data['small'] else "0;"
        output += "1;" if data['hush'] else "0;"
        output += "1;" if data['backwards'] else "0;"

        # "Easy Stuff"
        output += str(data['stutter']) + ";"
        output += (data['proxy_prefix'] if data['proxy_prefix'] else "") + ";"
        output += (data['proxy_suffix'] if data['proxy_suffix'] else "") + ";"
        output += (data['bio'] if data['bio'] else "") + ";"

        # Prefix
        output += "1;" if data['prefix']['active'] else "0;"
        match version:
            case 14:
                output += (",".join(data['prefix']['contents']) if data['prefix']['active'] else "") + ";"
                output += (str(data['prefix']['chance']) if data['prefix']['active'] else "") + ";"
            case 15:
                output += (",".join([key + "|" + str(value) for key, value in data['prefix']['contents'].items()])
                           if data['prefix']['active'] else "") + ";"

        # Suffix
        output += "1;" if data['suffix']['active'] else "0;"
        match version:
            case 14:
                output += (",".join(data['suffix']['contents']) if data['suffix']['active'] else "") + ";"
                output += (str(data['suffix']['chance']) if data['suffix']['active'] else "") + ";"
            case 15:
                output += (",".join([key + "|" + str(value) for key, value in data['suffix']['contents'].items()])
                           if data['suffix']['active'] else "") + ";"

        # Sprinkle
        output += "1;" if data['sprinkle']['active'] else "0;"
        match version:
            case 14:
                output += (",".join(data['sprinkle']['contents']) if data['sprinkle']['active'] else "") + ";"
                output += (str(data['sprinkle']['chance']) if data['sprinkle']['active'] else "") + ";"
            case 15:
                output += (",".join([key + "|" + str(value) for key, value in data['sprinkle']['contents'].items()])
                           if data['sprinkle']['active'] else "") + ";"

        # Muffle
        output += "1;" if data['muffle']['active'] else "0;"
        match version:
            case 14:
                output += (",".join(data['muffle']['contents']) if data['muffle']['active'] else "") + ";"
                output += (str(data['muffle']['chance']) if data['muffle']['active'] else "") + ";"
            case 15:
                output += (",".join([key + "|" + str(value) for key, value in data['muffle']['contents'].items()])
                           if data['muffle']['active'] else "") + ";"

        # Alt Muffle
        output += "1;" if data['alt_muffle']['active'] else "0;"
        match version:
            case 14:
                output += (",".join(data['alt_muffle']['contents']) if data['alt_muffle']['active'] else "") + ";"
                output += (str(data['alt_muffle']['chance']) if data['alt_muffle']['active'] else "") + ";"
            case 15:
                output += (",".join([key + "|" + str(value) for key, value in data['alt_muffle']['contents'].items()])
                           if data['alt_muffle']['active'] else "") + ";"

        # Censor
        output += "1;" if data['censor']['active'] else "0;"
        output += (",".join([key + "|" + value for key, value in data['censor']['contents'].items()])
                                                                 if data['censor']['active'] else "")

        if file:
            # Encode the URL
            output = output.split(";")
            output = ";".join(output)

            with open("tf_cache.tf", "w") as f:
                f.write(output)

            await ctx.respond(file=discord.File("tf_cache.tf", f"{data['into']}.tf"))
            os.remove("tf_cache.tf")
            return

        await ctx.respond(output)

    @discord.slash_command(description="Import your saved transformations")
    async def import_tf(self,
                     ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None) -> None:
        if user is None:
            user = ctx.author

        # Blocked users (globally)
        if ctx.user.id in BLOCKED_USERS:
            await ctx.respond(f"You're blocked from using this bot at all! You must've done something very bad..."
                              f"You might wanna appeal your ban in our Discord server, but, don't get your hopes up..."
                              f"||https://discord.gg/uGjWk2SRf6||", ephemeral=True)
            return
        if user.id in BLOCKED_USERS:
            await ctx.respond(f"You can't transform that user at all! They've been very naughty...", ephemeral=True)
            return

        data = utils.load_tf(user, ctx.guild)
        transformed_data = utils.load_transformed(ctx.guild)

        # Blocked channels (user)
        if data != {}:
            if str(ctx.channel.id) in data['blocked_channels']:
                await ctx.respond(f"You can't transform {user.mention} in this channel!"
                                  f"They have blocked the bot here!", ephemeral=True)
                return

            if transformed_data != {}:
                # Blocked channels (server)
                if str(ctx.channel.id) in transformed_data['blocked_channels']:
                    await ctx.respond(f"You can't use the bot, at least on this channel!", ephemeral=True)
                    return

                # Blocked users (server)
                if str(ctx.user.id) in transformed_data['blocked_users']:
                    await ctx.respond(f"You can't use the bot, at least on this server!", ephemeral=True)
                    return
                if str(user.id) in transformed_data['blocked_users']:
                    await ctx.respond(f"That user can't use the bot, at least on this server!", ephemeral=True)
                    return

        await ctx.respond(f"Please send the saved transformation you want to apply to {user.mention}?"
                          f"(Send CANCEL to cancel)")
        response = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
        if response.content.strip() == "CANCEL":
            await ctx.respond("Cancelled the transformation!")
            return

        if response.attachments:
            await response.attachments[0].save(f"tf_cache.tf")
            with open("tf_cache.tf") as f:
                data = f.read().split(";")
            os.remove("tf_cache.tf")
        else:
            data = response.content.split(";")

        version = 14 # Version where files where added, but it didn't originally have the version identifier so
        if len(data) not in [23, 27]:
            await ctx.send("Invalid transformation data!")
            return
        if len(data) == 23: # Version 15 and above
            version = int(data[0])
            data = data[1:]

        if version not in [14, 15]:
            await ctx.send("The version of this file isn't supported! Please contact support for more information!")

        # Basic stuff
        await transform_function(ctx, user, data[0], data[1])

        # More-or-less-basic stuff
        utils.write_tf(user,
                       ctx.guild,
                       big=int(data[2]),
                       small=int(data[3]),
                       hush=int(data[4]),
                       backwards=int(data[5]),
                       stutter=int(data[6]),
                       proxy_prefix=data[7],
                       proxy_suffix=data[8],
                       bio=data[9])

        # Prefix
        if data[10] == "1":
            prefixes = data[11].split(",")
            match version:
                case 14:
                    for prefix in prefixes:
                        utils.write_tf(user, ctx.guild, prefix=prefix, chance=int(data[12]))
                case 15:
                    for prefix in prefixes:
                        prefix = prefix.split("|")
                        utils.write_tf(user, ctx.guild, prefix=prefix[0], chance=int(prefix[1]))

        # Suffix
        match version:
            case 14:
                if data[13] == "1":
                    suffixes = data[14].split(",")
                    for suffix in suffixes:
                        utils.write_tf(user, ctx.guild, suffix=suffix, chance=int(data[15]))
            case 15:
                if data[12] == "1":
                    suffixes = data[13].split(",")
                    for suffix in suffixes:
                        suffix = suffix.split("|")
                        utils.write_tf(user, ctx.guild, suffix=suffix[0], chance=int(suffix[1]))

        # Sprinkle
        match version:
            case 14:
                if data[16] == "1":
                    sprinkles = data[17].split(",")
                    for sprinkle in sprinkles:
                        utils.write_tf(user, ctx.guild, sprinkle=sprinkle, chance=int(data[18]))
            case 15:
                if data[14] == "1":
                    sprinkles = data[15].split(",")
                    for sprinkle in sprinkles:
                        sprinkle = sprinkle.split("|")
                        utils.write_tf(user, ctx.guild, sprinkle=sprinkle[0], chance=int(sprinkle[1]))

        # Muffle
        match version:
            case 14:
                if data[19] == "1":
                    muffles = data[20].split(",")
                    for muffle in muffles:
                        utils.write_tf(user, ctx.guild, muffle=muffle, chance=int(data[21]))
            case 15:
                if data[16] == "1":
                    muffles = data[17].split(",")
                    for muffle in muffles:
                        muffle = muffle.split("|")
                        utils.write_tf(user, ctx.guild, muffle=muffle[0], chance=int(muffle[1]))

        # Alt Muffle
        match version:
            case 14:
                if data[22] == "1":
                    alt_muffles = data[23].split(",")
                    for alt_muffle in alt_muffles:
                        utils.write_tf(user, ctx.guild, alt_muffle=alt_muffle, chance=int(data[24]))
            case 15:
                if data[18] == "1":
                    alt_muffles = data[19].split(",")
                    for alt_muffle in alt_muffles:
                        alt_muffle = alt_muffle.split("|")
                        utils.write_tf(user, ctx.guild, alt_muffle=alt_muffle[0], chance=int(alt_mufffle[1]))

        # Censor
        match version:
            case 14:
                if data[25] == "1":
                    censors = data[26].split(",")
                    for censor in censors:
                        censor = censor.split("|")
                        utils.write_tf(user, ctx.guild, censor=censor[0], censor_replacement=censor[1])
            case 15:
                if data[20] == "1":
                    censors = data[21].split(",")
                    for censor in censors:
                        censor = censor.split("|")
                        utils.write_tf(user, ctx.guild, censor=censor[0], censor_replacement=censor[1])

        await ctx.send(f"Transformed {user.mention} successfully into {data[0]}!")


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Transformation(bot))

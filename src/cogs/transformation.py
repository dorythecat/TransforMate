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
                             copy: discord.User | None = None,
                             merge: bool | None = None) -> bool:
    if into:
        # Webhook names should be more than two characters
        if len(into) <= 1:
            await ctx.respond("Please provide a name longer than 1 character!")
            return False

        # Webhook names cannot contain "discord", will return a 400 error
        if "discord" in into.lower():
            await ctx.respond("You cannot use that as a name!")
            return False

    if image_url:
        image_url = utils.check_url(image_url)
        if image_url == "":
            await ctx.respond("Invalid Image URL! Please provide a valid image URL!")
            return False

    if copy is not None:
        old_data = utils.load_tf(user, ctx.guild)
        new_data = utils.load_tf(copy, ctx.guild)
        if new_data == {}:
            return await transform_function(ctx, user, copy.display_name, copy.avatar.url)
        new_data['blocked_channels'] = old_data['blocked_channels'] if 'blocked_channels' in old_data else []
        new_data['blocked_users'] = old_data['blocked_users'] if 'blocked_users' in old_data else []
        if merge in [False, None]:
            new_data['into'] += "឵ᅟ"
        if into:
            new_data['into'] = into
        if image_url:
            new_data['image_url'] = image_url
        new_data['transformed_by'] = ctx.author.id
        new_data['claim'] = 0
        new_data['eternal'] = False
        utils.write_tf(user, ctx.guild, new_data=new_data)
        utils.write_transformed(ctx.guild, user)
        return True

    if not into:
        # Defaults to their name
        into = user.name
    if not image_url:
        # Defaults to their avatar, or, if they lack one, to the default Discord avatar
        image_url = user.avatar.url if user.avatar is not None else "https://cdn.discordapp.com/embed/avatars/1.png"

    utils.write_tf(user,
                   ctx.guild,
                   transformed_by=ctx.author,
                   into=into.strip(),
                   image_url=image_url)
    utils.write_transformed(ctx.guild, user)

    transformed_data = utils.load_transformed(ctx.guild)
    if transformed_data['logs'][2]:
        embed = discord.Embed(title="Transformed User", color=discord.Color.green())
        embed.add_field(name="User", value=user.mention)
        embed.add_field(name="Transformed By", value=ctx.author.mention)
        embed.add_field(name="Into", value=into)
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
                        copy: discord.Option(discord.User,
                                             description="Copy another user") = None,
                        merge: discord.Option(discord.SlashCommandOptionType.boolean,
                                              description="Whether to merge or not the user's messages to the"
                                                          "original transformed user's when copying") = None,
                        change_nickname: discord.Option(discord.SlashCommandOptionType.boolean,
                                                        description="Change the user's nickname?") = True) -> None:
        if not user:
            user = ctx.author

        if ctx.user.id in BLOCKED_USERS: # Blocked users (globally)
            await ctx.respond(f"You're blocked from using this bot at all! You must've done something very bad..."
                              f"You might wanna appeal your ban in our Discord server, but, don't get your hopes up..."
                              f"||https://discord.gg/uGjWk2SRf6||", ephemeral=True)
            return
        if user.id in BLOCKED_USERS:
            await ctx.respond(f"You can't transform that user at all! They've been very naughty...", ephemeral=True)
            return

        data = utils.load_tf(user, ctx.guild)
        if data != {} and str(ctx.channel.id) in data['blocked_channels']: # Blocked channels (user)
            await ctx.respond(f"You can't transform {user.mention} in this channel!"
                              f"They have blocked the bot here!", ephemeral=True)
            return

        transformed_data = utils.load_transformed(ctx.guild)
        if transformed_data == {}:
            utils.write_transformed(ctx.guild)
            transformed_data = utils.load_transformed(ctx.guild)
        if str(ctx.channel.id) in transformed_data['blocked_channels']: # Blocked channels (server)
            await ctx.respond(f"You can't use the bot, at least on this channel!", ephemeral=True)
            return

        if str(ctx.user.id) in transformed_data['blocked_users']: # Blocked users (server)
            await ctx.respond(f"You can't use the bot, at least on this server!", ephemeral=True)
            return
        if str(user.id) in transformed_data['blocked_users']:
            await ctx.respond(f"That user can't use the bot, at least on this server!", ephemeral=True)
            return

        if utils.is_transformed(user, ctx.guild):
            if data == {}: # This is to avoid https://github.com/dorythecat/TransforMate/issues/25
                data = { 'claim': 0 }
            if data['claim'] != 0 and int(data['claim']) != ctx.author.id and data['eternal']:
                if ctx.author.name != user.name:
                    await ctx.respond(f"You can't do that! {user.mention} is eternally transformed by "
                                      f"{ctx.guild.get_member(int(data['claim'])).mention}!")
                    return
                await ctx.respond(f"Your master can't allow you to transform, at least for now...")
                return

        if into:
            if await transform_function(ctx, user, into, image_url, None):
                if change_nickname:
                    try:
                        await user.edit(nick=into)
                    except Exception:
                        await ctx.respond("Could not change nickname of user! Please check the permissions of the bot!",
                                          ephemeral=True)
                await ctx.respond(f'You have transformed {user.mention} into "{into}"!')
            return

        if copy:
            if await transform_function(ctx, user, into, image_url, copy, merge):
                if change_nickname:
                    try:
                        await user.edit(nick=into)
                    except Exception:
                        await ctx.respond("Could not change nickname of user! Please check the permissions of the bot!",
                                          ephemeral=True)
                await ctx.respond(f'You have transformed {user.mention} into a copy of "{copy.mention}"!')
            return

        await ctx.respond(f"What do we want to transform {user.mention} into? (Send CANCEL to cancel)")
        response = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)

        # Get any attached image, if given
        file_url = None
        if response.attachments:
            file_url = response.attachments[0].url
            if utils.is_transformed(ctx.author, ctx.guild):
                # Solution to https://github.com/dorythecat/TransforMate/issues/16
                image_channel = transformed_data['images']
                if not image_channel:
                    await ctx.respond(f"You can't transform the other user whilst transformed yourself!\n"
                                      f"There's no image buffer channel in this server!")
                    return
                file = await response.attachments[0].to_file()
                file_message = await ctx.guild.get_channel(transformed_data['images']).send(file=file)
                file_url = file_message.attachments[0].url

        if response.content.lower().strip() == "cancel":
            await ctx.respond("Cancelled the transformation!")
            return
        if await transform_function(ctx,
                                    user,
                                    response.content,
                                    file_url,
                                    None):
            if change_nickname:
                try:
                    await user.edit(nick=into)
                except Exception:
                    await ctx.respond("Could not change nickname of user! Please check the permissions of the bot!",
                                      ephemeral=True)
            await ctx.respond(f'You have transformed {user.mention} into "{response.content}"!')

    @discord.slash_command(description="Return someone to their previous state")
    async def goback(self,
                     ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None) -> None:
        if user is None:
            user = ctx.author

        transformed_data = utils.load_transformed(ctx.guild)
        if transformed_data == {}:
            await ctx.respond(f"{user.mention} is not transformed at the moment!")
            return

        data = utils.load_tf(user, ctx.guild)
        channel = None
        if data == {}:
            await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to! "
                              f"(At least on this channel)")
            return

        if not utils.is_transformed(user, ctx.guild):
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

        utils.remove_transformed(user, ctx.guild)
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
        if not utils.is_transformed(user, ctx.guild,):
            # TODO: https://github.com/dorythecat/TransforMate/issues/35
            await ctx.respond(f"{user.mention} is not transformed at the moment, you can't claim them!")
            return
        data = utils.load_tf(user, ctx.guild)
        if data == {}:
            await ctx.respond("This user isn't transformed in this channel! Please try again in the proper channel!")
            return
        if data['claim'] != 0:
            if int(data['claim']) == ctx.author.id:
                await ctx.respond(f"You can't do that! You already claimed {user.mention}!")
                return
            await ctx.respond(f"You can't do that! {user.mention} has been claimed already by "
                              f"{ctx.guild.get_member(int(data['claim'])).mention}!")
            return
        utils.write_tf(user, ctx.guild, claim_user=ctx.author.id)
        await ctx.respond(f"You have successfully claimed {user.mention} for yourself! Hope you enjoy!")

        transformed_data = utils.load_transformed(ctx.guild)
        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Claimed", color=discord.Color.gold())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Claimed User", value=ctx.author.mention)
            embed.add_field(name="Channel", value=ctx.channel.mention)
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
        if data == {} or data['claim'] == 0:
            await ctx.respond(f"{user.mention} is currently not claimed by anyone (yet)!")
            return
        if int(data['claim']) != ctx.author.id:
            await ctx.respond(f"You can't do that! {user.mention} is claimed by "
                              f"{ctx.guild.get_member(int(data['claim'])).mention}, not you!")
            return
        utils.write_tf(user, ctx.guild, channel, claim_user=0, eternal=False)
        await ctx.respond(f"You have successfully unclaimed {user.mention}! They are now free from your grasp!")

        transformed_data = utils.load_transformed(ctx.guild)
        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Unclaimed", color=discord.Color.gold())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Unclaimed User", value=ctx.author.mention)
            embed.add_field(name="Channel", value=ctx.channel.mention)
            await ctx.guild.get_channel(transformed_data['logs'][3]).send(embed=embed)

    @discord.slash_command(description="Safeword command. Use in case of abuse or incommodity, to unclaim yourself.")
    async def safeword(self,
                       ctx: discord.ApplicationContext) -> None:
        data = utils.load_tf(ctx.author, ctx.guild)
        channel = None
        # We have to check if they are claimed OR eternally transformed. If both are false, safeword does nothing.
        # If either are true, we need to keep going, otherwise we can just return.
        if data == {} or data['claim'] == 0:
            await ctx.respond(f"You can't do that! You are not claimed by anyone! Stop trying to abuse! >:(")
            return
        utils.write_tf(ctx.author, ctx.guild, channel, claim_user=0, eternal=False)
        await ctx.respond(f"You have successfully activated the safeword command.\n"
                          f"Please, sort out any issues with your rp partner(s) before you continue using the bot .\n"
                          f"Use \"/goback\" to return to your normal self.")

        transformed_data = utils.load_transformed(ctx.guild)
        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Safeworded", color=discord.Color.gold())
            embed.add_field(name="User", value=ctx.author.mention)
            embed.add_field(name="Channel", value=ctx.channel.mention)
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

        if data == {}:
            await ctx.respond(f"{user.mention} is not transformed at the moment!")
            return

        # Blocked channels (user)
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

        output = utils.encode_tsf(data)

        if file:
            try:
                with open("tf_cache", "w", encoding='utf-8') as f:
                    f.write(output)
            except OSError as e:
                print(f"Error writing to file:")
                print(f"{str(type(e))}: {e}")

            await ctx.respond(file=discord.File("tf_cache", f"{data['into']}.tsf"))
            try:
                os.remove("tf_cache")
            except OSError as e:
                print(f"Error removing file:")
                print(f"{str(type(e))}: {e}")
            return

        await ctx.respond("```" + output + "```")

    @discord.slash_command(description="Import your saved transformations")
    async def import_tf(self,
                        ctx: discord.ApplicationContext,
                        user: discord.Option(discord.User) = None,
                        change_nickname: discord.Option(discord.SlashCommandOptionType.boolean,
                                                        description="Change the user's nickname?") = True) -> None:
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
            if str(ctx.user.id) in data['blocked_users']:
                await ctx.respond(f"{user.mention} has blocked you from transforming them!", ephemeral=True)
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

        if utils.is_transformed(user, ctx.guild):
            if data == {}:
                # This is to avoid https://github.com/dorythecat/TransforMate/issues/25
                data = { 'claim': 0 }
            if data['claim'] != 0 and int(data['claim']) != ctx.author.id and data['eternal']:
                if ctx.author.name != user.name:
                    await ctx.respond(f"You can't do that! {user.mention} is eternally transformed by "
                                      f"{ctx.guild.get_member(int(data['claim'])).mention}!")
                    return
                await ctx.respond(f"Your master can't allow you to transform, at least for now...")
                return

        await ctx.respond(f"Please send the saved transformation you want to apply to {user.mention}?"
                          f"(Send CANCEL to cancel)")
        response = await self.bot.wait_for('message',
                                           check=lambda m: m.author == ctx.author and m.guild == ctx.guild)
        if response.content.lower().strip() == "cancel":
            await ctx.respond("Cancelled the transformation!")
            return

        tsf_string = response.content
        if response.attachments:
            await response.attachments[0].save(f"tf_cache")
            try:
                with open("tf_cache", encoding='utf-8') as f:
                    tsf_string = f.read()
                os.remove("tf_cache")
            except OSError as e:
                print(f"Error reading from file or removing file:")
                print(f"{str(type(e))}: {e}")

        new_data = utils.decode_tsf(tsf_string)
        new_data['transformed_by'] = ctx.author.id

        data = utils.load_tf(user, ctx.guild)
        new_data['blocked_users'] = data['blocked_users'] if 'blocked_users' in data else []
        new_data['blocked_channels'] = data['blocked_channels'] if 'blocked_channels' in data else []
        new_data['claim'] = data['claim'] if 'claim' in data else 0
        new_data['eternal'] = data['eternal'] if 'eternal' in data else False
        utils.write_tf(user, ctx.guild, new_data)
        utils.write_transformed(ctx.guild, user)

        if change_nickname:
            try:
                await user.edit(nick=new_data['into'])
            except Exception:
                await ctx.respond("Could not change nickname of user! Please check the permissions of the bot!",
                                  ephemeral=True)

        await ctx.send(f"Transformed {user.mention} successfully into {new_data['into']}!")


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Transformation(bot))

import discord
from discord.ext import commands

import src.utils as utils
from src.config import BLOCKED_USERS


# Helper function
async def transform_function(ctx: discord.ApplicationContext,
                             user: discord.User,
                             into: str,
                             image_url: str,
                             channel: discord.TextChannel,
                             brackets: list[str] | None) -> bool:
    if not image_url:
        image_url = user.avatar.url
    image_url = image_url.strip()
    if image_url[:4] != "http":
        await ctx.send("Invalid Image URL! Please provide a valid image URL!")
        return False
    if "?" in image_url:  # Prune url, if possible, to preserve space
        image_url = image_url[:image_url.index("?")]

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
                        user: discord.Option(discord.User) = None,
                        into: discord.Option(discord.SlashCommandOptionType.string,
                                             description="Who to transform") = None,
                        image_url: discord.Option(discord.SlashCommandOptionType.string,
                                                  description="Image URL to use") = None,
                        channel: discord.Option(discord.TextChannel,
                                                description="Transform the user only on this channel") = None,
                        brackets: discord.Option(discord.SlashCommandOptionType.string,
                                                 description="What brackets to use for this proxy."
                                                             "Ex: \"text\", Abc:text, etc."
                                                             "(Only available in certain servers)") = None) -> None:
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
                data = {'claim': None} # Empty data so we can do multiple tfs
            else:
                await ctx.respond(f"{user.mention} is already transformed at the moment!")
                return
            if data['claim'] not in ["", None] and data['claim'] != ctx.author.name and data['eternal']:
                if ctx.author.name != user.name:
                    await ctx.respond(f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
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
                await ctx.send("Please provide a name longer than 1 character!")
                return
            if await transform_function(ctx, user, into, image_url, channel, brackets):
                await ctx.respond(f'You have transformed {user.mention} into "{into}"!')
            return

        await ctx.respond(f"What do we want to transform {user.mention} into? (Send CANCEL to cancel)")
        response = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
        if response.content.strip() == "CANCEL":
            await ctx.respond("Cancelled the transformation!")
            return
        if len(response.content.strip()) <= 1:
            await ctx.send("Please provide a name longer than 1 character!")
            return
        if await transform_function(ctx,
                                    user,
                                    response.content,
                                    response.attachments[0].url if response.attachments else None,
                                    channel,
                                    brackets):
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

        if data['eternal'] and data['claim'] != ctx.author.name:
            if ctx.author.name != user.name:
                await ctx.respond(f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
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
        if not utils.is_transformed(user, ctx.guild):
            await ctx.respond(f"{user.mention} is not transformed at the moment, you can't claim them!")
            return
        data = utils.load_tf(user, ctx.guild)
        channel = None
        if str(ctx.channel) in data:
            data = data[str(ctx.channel)]
            channel = ctx.channel
        else:
            data = data['all']
        if data['claim'] not in ["", None] and data['claim'] != ctx.author.name:
            await ctx.respond(f"You can't do that! {user.mention} has been claimed already by {data['claim']}!")
            return
        utils.write_tf(user, ctx.guild, channel, claim_user=ctx.author.name)
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
        if data['claim'] in ["", None]:
            await ctx.respond(f"{user.mention} is currently not claimed by anyone!")
            return
        if data['claim'] != ctx.author.name:
            await ctx.respond(f"You can't do that! {user.mention} is claimed by {data['claim']}, not you!")
            return
        utils.write_tf(user, ctx.guild, channel, claim_user="", eternal=0)
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
        if data['claim'] in ["", None] and not data['eternal']:
            await ctx.respond(f"You can't do that! You are not claimed by anyone! Stop trying to abuse! >:(")
            return
        utils.write_tf(ctx.author, ctx.guild, channel, claim_user="", eternal=0)
        await ctx.respond(f"You have successfully activated the safeword command.\n"
                          f"Please, sort out any issues with your rp partner(s) before you continue using the bot .\n"
                          f"Use \"/goback\" to return to your normal self.")

        transformed_data = utils.load_transformed(ctx.guild)
        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Safeworded", color=discord.Color.gold())
            embed.add_field(name="User", value=ctx.author.mention)
            embed.add_field(name="Channel", value=ctx.message.channel.mention)
            await ctx.guild.get_channel(transformed_data['logs'][3]).send(embed=embed)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Transformation(bot))

import discord
from discord.ext import commands

import src.utils as utils
from src.config import BLOCKED_USERS


# Helper function
async def transform_function(ctx: discord.ApplicationContext,
                             user: discord.User,
                             into: str,
                             image_url: str,
                             channel: discord.TextChannel) -> bool:
    if not image_url:
        image_url = user.avatar.url
    image_url = image_url.strip()
    if image_url[:4] != "http":
        await ctx.send("Invalid Image URL! Please provide a valid image URL!")
        return False
    if "?" in image_url:  # Prune url, if possible, to preserve space
        image_url = image_url[:image_url.index("?")]

    utils.write_tf(user, ctx.guild, channel, transformed_by=str(ctx.author.id), into=into.strip(), image_url=image_url)
    utils.write_transformed(ctx.guild, user, channel)
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
                                                description="Transform the user only on this channel") = None) -> None:
        if not user:
            user = ctx.author

        data = utils.load_tf(user, ctx.guild)
        transformed_data = utils.load_transformed(ctx.guild)
        channel_id = str(ctx.channel.id if not channel else channel.id)

        # Blocked users (globally)
        if ctx.user.id in BLOCKED_USERS:
            await ctx.respond(f"You're blocked from using this bot at all! You must've done something very bad...")
            return
        if user.id in BLOCKED_USERS:
            await ctx.respond(f"You can't transform that user at all! They've been very naughty...")
            return

        # Blocked channels (user)
        if data not in [None, {}]:
            if channel_id in data['blocked_channels']:
                await ctx.respond(
                    f"You can't transform {user.mention} in this channel! They have blocked the bot here!")
                return

        if transformed_data not in [None, {}]:
            # Blocked channels (server)
            if channel_id in transformed_data['blocked_channels']:
                await ctx.respond(f"You can't use the bot on this channel!")
                return

            # Blocked users (server)
            if str(ctx.user.id) in transformed_data['blocked_users']:
                await ctx.respond(f"You can't use the bot on this server!")
                return
            if str(user.id) in transformed_data['blocked_users']:
                await ctx.respond(f"That user can't use the bot on this server!")
                return

        if utils.is_transformed(user, ctx.guild):
            if channel_id in data:
                data = data[channel_id]
            elif 'all' in data:
                data = data['all']
            else:
                return
            if data['claim'] not in ["", None] and data['claim'] != ctx.author.name and data['eternal']:
                if ctx.author.name != user.name:
                    await ctx.respond(f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
                    return
                await ctx.respond(f"Your master can't allow you to transform, at least for now...")
                return

        if into:
            if len(into) <= 1:
                await ctx.send("Please provide a name longer than 1 character!")
                return
            if await transform_function(ctx, user, into, image_url, channel):
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
                                    channel):
            await ctx.respond(f'You have transformed {user.mention} into "{response.content}"!')

    @discord.slash_command(description="Return someone to their previous state")
    async def goback(self,
                     ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None) -> None:
        if user is None:
            user = ctx.author
        data = utils.load_tf(user, ctx.guild)
        channel = None
        if str(ctx.channel.id) in data:
            data = data[str(ctx.channel.id)]
            channel = ctx.channel
        elif 'all' in data:
            data = data['all']
        else:
            await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to! "
                              f"(At least on this channel)")
            return

        if not utils.is_transformed(user, ctx.guild, ctx.channel) and not utils.is_transformed(user, ctx.guild):
            if data['into'] in ["", None]:
                await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to!")
                return
            utils.write_transformed(ctx.guild, user, channel)
            await ctx.respond(f"{user.mention} has been turned back to their last form!")
            return

        if data['eternal'] and data['claim'] != ctx.author.name:
            if ctx.author.name != user.name:
                await ctx.respond(f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
                return
            await ctx.respond(f"Your master won't allow you to turn back, at least for now...")
            return

        utils.remove_transformed(user, ctx.guild, None if utils.is_transformed(user, ctx.guild) else ctx.channel)
        await ctx.respond(f"{user.mention} has been turned back to normal!")

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


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Transformation(bot))

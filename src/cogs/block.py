import discord
from discord.ext import commands

import utils


class Block(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    block_command = discord.SlashCommandGroup("block", "Block certain users and channels")

    @block_command.command(description="Set a channel where you just wanna be yourself")
    async def channel(self,
                      ctx: discord.ApplicationContext,
                      channel: discord.TextChannel = None,
                      invert: discord.Option(bool,
                                             "Inverts the current blocked status of ALL channels"
                                             ) = False,
                      all_channels: discord.Option(bool,
                                                   "Blocks all channels on this server" +
                                                   "(does not unvblock any channels)") = False) -> None:
        if all_channels:
            blocked_channels = utils.load_tf(ctx.user, ctx.guild)['blocked_channels']
            for channel in ctx.guild.text_channels:
                if channel.id not in blocked_channels:
                    utils.write_tf(ctx.author, ctx.guild, block_channel=channel)
            await ctx.respond("Blocked all channels on this server!")
            return
        if invert:
            for channel in ctx.guild.text_channels:
               utils.write_tf(ctx.author, ctx.guild, block_channel=channel)
            await ctx.respond("Inverted your blocked channels!")
            return
        if channel is None:
            channel = ctx.channel
        utils.write_tf(ctx.author, ctx.guild, block_channel=channel)
        word = "yourself" if str(channel.id) in utils.load_tf(ctx.user, ctx.guild)['blocked_channels'] else "transformed"
        channel_word = "this channel" if channel == ctx.channel else channel.mention
        await ctx.respond(f"You will now be {word} in {channel_word}! (Use this same command to revert this)")

    @block_command.command(description="Block a user from interacting with you")
    async def user(self,
                   ctx: discord.ApplicationContext,
                   user: discord.User = None,
                   invert: discord.Option(bool,
                                          "Inverts the current blocked status of ALL users"
                                          ) = False,
                   all_users: discord.Option(bool,
                                                "Blocks all users on this server" +
                                                "(does not unvblock any users)") = False) -> None:
        if all_users:
            blocked_users = utils.load_tf(ctx.user, ctx.guild)['blocked_users']
            for member in ctx.guild.members:
                if member.id not in blocked_users:
                    utils.write_tf(ctx.author, ctx.guild, block_user=member)
            await ctx.respond("Blocked all users on this server!")
            return
        if invert:
            for member in ctx.guild.members:
               utils.write_tf(ctx.author, ctx.guild, block_user=member)
            await ctx.respond("Inverted your blocked users!")
            return
        if user is None:
            await ctx.respond("You must specify a user to (un)block!", ephemeral=True)
        utils.write_tf(ctx.author, ctx.guild, block_user=user)
        word = "unblocked" if user.id in utils.load_tf(ctx.user, ctx.guild)['blocked_users'] else "blocked"
        await ctx.respond(f"{user.mention} has been {word} from interacting with you! (Use this same command to revert this)")

    @block_command.command(description="Set a channel category where you just wanna be yourself")
    async def category(self,
                       ctx: discord.ApplicationContext,
                       category: discord.CategoryChannel = None) -> None:
        if category is None:
            category = ctx.channel.category
        for channel in category.channels:
            utils.write_tf(ctx.author, ctx.guild, block_channel=channel)
        word = "yourself" if str(category.channels[0].id) in utils.load_tf(ctx.user, ctx.guild)['blocked_channels'] else "transformed"
        category_word = "this channel" if category == ctx.channel.category else category.mention
        await ctx.respond(f"You will now be {word} in {category_word}! (Use this same command to revert this)")


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Block(bot))

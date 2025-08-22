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
                      channel: discord.TextChannel = None) -> None:
        if channel is None:
            channel = ctx.channel
        utils.write_tf(ctx.author, ctx.guild, block_channel=channel)
        word = "yourself" if str(channel.id) in utils.load_tf(ctx.user, ctx.guild)[
            'blocked_channels'] else "transformed"
        channel_word = "this channel" if channel == ctx.channel else channel.mention
        await ctx.respond(f"You will now be {word} in {channel_word}!")

    @block_command.command(description="Block a user from interacting with you")
    async def user(self,
                   ctx: discord.ApplicationContext,
                   user: discord.User) -> None:
        if user == ctx.author:
            await ctx.respond("You can't block yourself!")
            return
        utils.write_tf(ctx.author, ctx.guild, block_user=user)
        word = "blocked" if user.id in utils.load_tf(ctx.user)['blocked_users'] else "unblocked"
        await ctx.respond(f"{user.mention} has been {word} from interacting with you!")


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Block(bot))

import discord
from discord.ext import commands

import src.utils as utils


WEBHOOK_NAME: str = "TransforMate Webhook"  # Name to use for the webhooks

class Admin(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot


    admin_command = discord.SlashCommandGroup("admin", "Admin commands for the bot")

    @admin_command.command(description="Kill all webhooks, and let the bot regenerate them")
    @discord.default_permissions(administrator=True)
    async def killhooks(self,
                        ctx: discord.ApplicationContext) -> None:
        for wh in await ctx.guild.webhooks():
            if wh.name == WEBHOOK_NAME:  # Delete only our webhooks, which all *should* have the same name
                await wh.delete()
        await ctx.respond("All webhooks have been deleted! The bot will regenerate them as needed.", ephemeral=True)

    @admin_command.command(description="(Un)block a channel from being users being transformed in")
    @discord.default_permissions(administrator=True)
    async def block_channel(self,
                            ctx: discord.ApplicationContext,
                            channel: discord.TextChannel = None) -> None:
        if channel is None:
            channel = ctx.channel
        utils.write_transformed(ctx.guild, block_channel=channel)
        data = utils.load_transformed(ctx.guild)['blocked_channels']
        word = "blocked" if str(channel.id) in data else "unblocked"
        await ctx.respond(f"{channel.mention} has been {word}!", ephemeral=True)

    @admin_command.command(description="(Un)block a user from being transformed in this server")
    @discord.default_permissions(administrator=True)
    async def block_user(self,
                         ctx: discord.ApplicationContext,
                         user: discord.User) -> None:
        utils.write_transformed(ctx.guild, block_user=user)
        data = utils.load_transformed(ctx.guild)['blocked_users']
        word = "blocked" if str(user.id) in data else "unblocked"
        await ctx.respond(f"{user.mention} has been {word}!", ephemeral=True)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Admin(bot))
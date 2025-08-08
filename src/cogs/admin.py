import discord
from discord.ext import commands

import utils
from config import WEBHOOK_NAME, MAX_REGEN_USERS


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
                            channel: discord.Option(discord.TextChannel) = None) -> None:
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
                         user: discord.Option(discord.User)) -> None:
        utils.write_transformed(ctx.guild, block_user=user)
        data = utils.load_transformed(ctx.guild)['blocked_users']
        word = "blocked" if str(user.id) in data else "unblocked"
        await ctx.respond(f"{user.mention} has been {word}!", ephemeral=True)

    @admin_command.command(description="List all blocked channels")
    @discord.default_permissions(administrator=True)
    async def list_blocked_channels(self,
                                    ctx: discord.ApplicationContext) -> None:
        data = utils.load_transformed(ctx.guild)
        blocked_channels = [ctx.guild.get_channel(int(channel)).mention for channel in data['blocked_channels']]

        embed = utils.get_embed_base(title="Blocked Channels",
                                     desc="\n".join(blocked_channels) if blocked_channels else "No blocked channels",
                                     color=discord.Color.red())
        await ctx.respond(embed=embed, ephemeral=True)

    @admin_command.command(description="List all blocked users")
    @discord.default_permissions(administrator=True)
    async def list_blocked_users(self,
                                 ctx: discord.ApplicationContext) -> None:
        data = utils.load_transformed(ctx.guild)
        blocked_users = [ctx.guild.get_member(int(user)).mention for user in data['blocked_users']]

        embed = utils.get_embed_base(title="Blocked Users",
                                     desc="\n".join(blocked_users) if blocked_users else "No blocked users",
                                     color=discord.Color.red())
        await ctx.respond(embed=embed, ephemeral=True)

    @admin_command.command(description="Set up log channels for the bot")
    @discord.default_permissions(administrator=True)
    async def setup_logs(self,
                         ctx: discord.ApplicationContext,
                         all: discord.Option(discord.TextChannel) = None,
                         edit: discord.Option(discord.TextChannel) = None,
                         delete: discord.Option(discord.TextChannel) = None,
                         transform: discord.Option(discord.TextChannel) = None,
                         claim: discord.Option(discord.TextChannel) = None) -> None:
        if all is None:
            logs = [edit.id if edit is not None else None,
                    delete.id if delete is not None else None,
                    transform.id if transform is not None else None,
                    claim.id if claim is not None else None]
        else:
            logs = [all.id, all.id, all.id, all.id]
        utils.write_transformed(ctx.guild, logs=logs)
        await ctx.respond("Log channels have been set up!", ephemeral=True)

    @admin_command.command(description="Update the bot's settings")
    @discord.default_permissions(administrator=True)
    async def update_settings(self,
                              ctx: discord.ApplicationContext,
                              clean_logs: discord.Option(discord.SlashCommandOptionType.boolean,
                                                         description="Should the bot clean up the logs"
                                                                     "made by other bots?") = False,
                              brackets: discord.Option(discord.SlashCommandOptionType.boolean,
                                                       description="Do we use brackets for"
                                                                   "transformations?") = False) -> None:
        utils.write_transformed(ctx.guild, clear_other_logs=clean_logs, affixes=brackets)
        await ctx.respond("Bot settings have been updated!\n-# We recommend running /admin regen_server_files after "
                          "updating your settings, but BE CAREFUL, since this command REMOVES ALL TRANSFORMED USERS "
                          "DATA IN YOUR SERVER.", ephemeral=True)

    @admin_command.command(description="Regenerate all files for this server")
    @discord.default_permissions(administrator=True)
    async def regen_server_tfs(self,
                               ctx: discord.ApplicationContext,
                               sure: bool = False,
                               really_sure: bool = False,
                               really_really_sure: bool = False,
                               fully_sure: bool = False) -> None:
        if (ctx.guild.member_count > MAX_REGEN_USERS):
            await ctx.respond(f"You're trying to regenerate all transformed users for a server with {ctx.guild.member_count} members!\n\n"
                              f"This operation cannot be fulfilled manually, and you should contact the bot's owner to take this action!")
        if not (sure and really_sure and really_really_sure and fully_sure):
            await ctx.respond("You haven't verified that you're *actually* sure about doing this! Please try again!")
            return
        for user in ctx.guild.members:
            utils.remove_all_server_tf(user, ctx.guild)
        await ctx.respond("Server TFs have been regenerated!")

    @admin_command.command(description="Regenerate a user's tf for this server")
    @discord.default_permissions(administrator=True)
    async def regen_user_tfs(self,
                             ctx: discord.ApplicationContext,
                             user: discord.Member,
                             sure: bool = False,
                             really_sure: bool = False) -> None:
        if not (sure and really_sure):
            await ctx.respond("You haven't verified that you're *actually* sure about doing this! Please try again!")
            return
        utils.remove_all_server_tf(user, ctx.guild)
        await ctx.respond(f"Server TFs have been regenerated for {user.mention}!")


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Admin(bot))

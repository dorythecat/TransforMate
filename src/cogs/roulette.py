import os

import discord
from discord.ext import commands

import utils
from config import BLOCKED_USERS


class Roulette(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    roulette_command = discord.SlashCommandGroup("roulette", "LETS GO GAMBLING")

    @roulette_command.command(description="Create a new roulette (or reset an existing one)")
    async def create(self,
                     ctx: discord.ApplicationContext,
                     name: discord.Option(discord.SlashCommandOptionType.string,
                                          description="The name of the roulette to add.") = "Default") -> None:
        if await utils.is_blocked(ctx):
            return

        utils.add_roulette(name, ctx.guild)
        await ctx.respond(f'Roulette "{name}" has been created!')


    @roulette_command.command(description="Remove a roulette")
    async def remove(self,
                     ctx: discord.ApplicationContext,
                     name: discord.Option(discord.SlashCommandOptionType.string,
                                          description="The name of the roulet to be removed.") = "Default") -> None:
        if await utils.is_blocked(ctx):
            return

        utils.remove_roulette(name, ctx.guild)
        await ctx.respond(f'Roulette "{name}" has been removed!')


    @roulette_command.command(description="Add an item to a roulette")
    async def add_item(self,
                       ctx: discord.ApplicationContext,
                       item: discord.Option(discord.SlashCommandOptionType.string,
                                            description="The TSF-compliant transformation string for the item.") = None,
                       name: discord.Option(discord.SlashCommandOptionType.string,
                                            description="The name of the roulette to add an item to.") = "Default") -> None:
        if utils.load_roulette(name, ctx.guild) == {}:
            await ctx.respond(f'Roulette "{name}" does not exist!')
            return

        if await utils.is_blocked(ctx):
            return

        if item is None:
            await ctx.respond("Please send your TSF-compliant file or string, or any other message to cancel")
            item = await self.bot.wait_for("message",
                                            check=lambda: m.author == ctx.author and m.channel == ctx.channel)
            if item.attachments:
                await item.attachments[0].save(f"tf_cache")
                try:
                    with open("tf_cache") as f:
                        item = f.read()
                    os.remove("tf_cache")
                except OSError as e:
                    print(f"Error reading from file or removing file:")
                    print(e)
                    await ctx.respond("Error reading file! Cancelling!")
            else:
                item = item.content

        utils.add_roulette_item(name, ctx.guild, item)
        await ctx.respond(f'Item "{item}" has been added to roulette "{name}"!')


    @roulette_command.command(description="Remove an item from a roulette")
    async def remove_item(self,
                          ctx: discord.ApplicationContext,
                          item: discord.Option(discord.SlashCommandOptionType.string,
                                               description="The name of the item to be removed.") = None,
                          name: discord.Option(discord.SlashCommandOptionType.string,
                                               description="The name of the roulette to add an item to.") = "Default") -> None:
        if await utils.is_blocked(ctx):
            return

        utils.remove_roulette_item(name, ctx.guild, item)
        await ctx.respond(f'Item "{item}" has been removed from roulette "{name}"!')


    @roulette_command.command(description="Roll a roulette")
    async def roll(self,
                   ctx: discord.ApplicationContext,
                   name: discord.Option(discord.SlashCommandOptionType.string,
                                        description="The name of the roulette to roll.") = "Default") -> None:
        if utils.load_roulette(name, ctx.guild) == {}:
            await ctx.respond(f'Roulette "{name}" does not exist!')
            return

        if await utils.is_blocked(ctx):
            return

        new_data = utils.decode_tsf(utils.roll_roulette(name, ctx.guild))
        new_data['transformed_by'] = ctx.author.id
        new_data['claim'] = 0
        new_data['eternal'] = False

        data['all'] = new_data
        utils.write_tf(ctx.user, ctx.guild, None, data)

        await ctx.respond(f"Transformed {ctx.user.mention} successfully into {new_data['into']}!")


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Roulette(bot))

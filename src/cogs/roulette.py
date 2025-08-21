import discord
from discord.ext import commands

import utils


class Roulette(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    roulette_command = discord.SlashCommandGroup("roulette", "LETS GO GAMBLING")

    @roulette_command.command(description="Create a new roulette (or reset an existing one)")
    async def create(self,
                     ctx: discord.ApplicationContext,
                     name: discord.Option(discord.SlashCommandOptionType.string,
                                          description="The name of the roulette to add.") = "Default") -> None:
        utils.add_roulette(name, ctx.guild)
        await ctx.respond(f'Roulette "{name}" has been created!')


    @roulette_command.command(description="Add an item to a roulette")
    async def add_item(self,
                       ctx: discord.ApplicationContext,
                       item: discord.Option(discord.SlashCommandOptionType.string,
                                            description="The TSF-compliant transformation string for the item."),
                       name: discord.Option(discord.SlashCommandOptionType.string,
                                            description="The name of the roulette to add an item to.") = "Default") -> None:
        if utils.load_roulette(name, ctx.guild) == {}:
            await ctx.respond(f'Roulette "{name}" does not exist!')
            return
        utils.add_roulette_item(name, ctx.guild, item)
        await ctx.respond(f'Item "{item}" has been added to roulette "{name}"!')


    @roulette_command.command(description="Roll a roulette")
    async def roll(self,
                   ctx: discord.ApplicationContext,
                   name: discord.Option(discord.SlashCommandOptionType.string,
                                        description="The name of the roulette to roll.") = "Default") -> None:
        if utils.load_roulette(name, ctx.guild) == {}:
            await ctx.respond(f'Roulette "{name}" does not exist!')
            return
        result = utils.roll_roulette(name, ctx.guild)
        await ctx.respond(f'You rolled: "{result}"!')


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Roulette(bot))

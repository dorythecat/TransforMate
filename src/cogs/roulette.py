import os

import discord
from discord.ext import commands

import utils
from config import BLOCKED_USERS, PATREON_SERVERS


class Roulette(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    roulette_command = discord.SlashCommandGroup("roulette", "LETS GO GAMBLING")

    @roulette_command.command(description="Create a new roulette (or reset an existing one)")
    async def create(self,
                     ctx: discord.ApplicationContext,
                     name: discord.Option(discord.SlashCommandOptionType.string,
                                          description="The name of the roulette to add.") = "Default") -> None:
        if not ctx.guild_id in PATREON_SERVERS and len(utils.get_roulettes(ctx.guild)) != 0:
            await ctx.respond('The maximum number of roulettes for this server is 1!\n'
                              'Subscribe to the Patreon to remove this limit!')
            return

        if name in utils.get_roulettes(ctx.guild):
            await ctx.respond(f'Roulette "{name}" already exists!')

        if await utils.is_blocked(ctx):
            return

        utils.add_roulette(name, ctx.guild)
        await ctx.respond(f'Roulette "{name}" has been created!')


    @roulette_command.command(description="Remove a roulette")
    async def remove(self,
                     ctx: discord.ApplicationContext,
                     sure: discord.Option(discord.SlashCommandOptionType.boolean) = False,
                     name: discord.Option(discord.SlashCommandOptionType.string,
                                          description="The name of the roulet to be removed.") = "Default") -> None:
        if await utils.is_blocked(ctx):
            return

        if not sure:
            await ctx.respond(f'Are you sure you want to remove roulette "{name}"? (Send YES, in all caps, to confirm)')
            sure = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author)
            if sure.content != "YES":
                await ctx.respond("Cancelling!")

        if name not in utils.get_roulettes(ctx.guild):
            await ctx.respond(f'Roulette "{name}" does not exist!')
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

        if not ctx.guild_id in PATREON_SERVERS and len(utils.load_roulette(name, ctx.guild)['items']) >= 30:
            await ctx.respond(f'The maximum number of items for roulette "{name}" is 30!\n'
                              f'Subscribe to the Patreon to remove this limit!')
            return

        if await utils.is_blocked(ctx):
            return

        if item is None:
            await ctx.respond("Please send your TSF-compliant file or string, or any other message to cancel")
            item = await self.bot.wait_for("message",
                                            check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
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
        await ctx.respond(f'Item "{item.split(";")[1]}" has been added to roulette "{name}"!')


    @roulette_command.command(description="Remove an item from a roulette")
    async def remove_item(self,
                          ctx: discord.ApplicationContext,
                          item: discord.Option(discord.SlashCommandOptionType.string,
                                               description="The name of the item to be removed."),
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
        roulette = utils.load_roulette(name, ctx.guild)
        if roulette == {}:
            await ctx.respond(f'Roulette "{name}" does not exist!')
            return

        if await utils.is_blocked(ctx):
            return

        if len(roulette['items']) == 0:
            await ctx.respond(f'There are no items left to roll for in roulette "{name}"!')
            return

        new_data = utils.decode_tsf(utils.roll_roulette(name, ctx.guild))
        new_data['transformed_by'] = ctx.author.id
        new_data['claim'] = 0
        new_data['eternal'] = False

        data = utils.load_tf(ctx.user, ctx.guild)
        data['all'] = new_data
        utils.write_tf(ctx.user, ctx.guild, None, data)

        await ctx.respond(f"Transformed {ctx.user.mention} successfully into {new_data['into']}!")


    @roulette_command.command(description="Get a roulette's info")
    async def info(self,
                   ctx: discord.ApplicationContext,
                   name: discord.Option(discord.SlashCommandOptionType.string,
                                        description="The name of the roulette to get info for.") = "Default") -> None:
        roulette = utils.load_roulette(name, ctx.guild)
        if roulette == {}:
            await ctx.respond(f'Roulette "{name}" does not exist!')
            return

        desc = "**Pulling method:** " + ("Normal\n\n" if roulette['type'] == 0 else "Gacha\n\n")
        for item in roulette['items']:
            desc += f"- {item}\n"

        await ctx.respond(embed=utils.get_embed_base(f'Roulette "{name}" info:', desc))


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Roulette(bot))

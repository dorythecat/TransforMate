import discord
from discord.ext import commands

import src.utils as utils


class Get(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    get_command = discord.SlashCommandGroup("get", "Get to know various things about transformed users")

    @get_command.command(description="List the settings for the transformed user")
    async def settings(self,
                       ctx: discord.ApplicationContext,
                       user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, True)
        if not valid:
            return
        embed = utils.get_embed_base(title=f"Settings for {user.name}")
        embed.add_field(name="Prefix", value=f"{data['prefix']['chance']}%" if data['prefix'] else "None")
        embed.add_field(name="Suffix", value=f"{data['suffix']['chance']}%" if data['suffix'] else "None")
        embed.add_field(name="Big Text", value="Yes" if data['big'] else "No")
        embed.add_field(name="Small Text", value="Yes" if data['small'] else "No")
        embed.add_field(name="Hush", value="Yes" if data['hush'] else "No")
        embed.add_field(name="Censor", value="Yes" if data['censor']['active'] else "No")
        embed.add_field(name="Sprinkle", value=f"{data['sprinkle']['chance']}%" if data['sprinkle'] else "None")
        embed.add_field(name="Muffle", value=f"{data['muffle']['chance']}%" if data['muffle'] else "None")
        await ctx.respond(embed=embed)

    @get_command.command(description="List the censors for the transformed user")
    async def censors(self,
                      ctx: discord.ApplicationContext,
                      user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, True)
        if not valid:
            return
        if not data['censor']['active']:
            await ctx.respond(f"{user.mention} is not censored at the moment!")
            return
        embed = utils.get_embed_base(title=f"Censors for {user.name}")
        for word in data['censor']['contents']:
            embed.add_field(name=word, value=data['censor']['contents'][word])
        await ctx.respond(embed=embed)

    @get_command.command(description="List the sprinkles for the transformed user")
    async def sprinkles(self,
                        ctx: discord.ApplicationContext,
                        user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, True)
        if not valid:
            return
        if not data['sprinkle']:
            await ctx.respond(f"{user.mention} has no sprinkles at the moment!")
            return
        embed = utils.get_embed_base(title=f"Sprinkles for {user.name}")
        embed.add_field(name='Sprinkle(s)', value=data['sprinkle']['contents'])
        await ctx.respond(embed=embed)

    @get_command.command(description="List the muffle for the transformed user")
    async def muffle(self,
                     ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, True)
        if not valid:
            return
        if not data['muffle']:
            await ctx.respond(f"{user.mention} has no muffles at the moment!")
            return
        embed = utils.get_embed_base(title=f"Muffle for {user.name}")
        embed.add_field(name='Muffle(s)', value=data['muffle']['contents'])
        await ctx.respond(embed=embed)

    @get_command.command(description="List the prefixes for the transformed user")
    async def prefixes(self,
                       ctx: discord.ApplicationContext,
                       user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, True)
        if not valid:
            return
        if not data['prefix']:
            await ctx.respond(f"{user.mention} has no prefixes at the moment!")
            return
        embed = utils.get_embed_base(title=f"Prefixes for {user.name}")
        embed.add_field(name='Prefix', value='\n'.join(data['prefix']['contents']))
        await ctx.respond(embed=embed)

    @get_command.command(description="List the suffixes for the transformed user")
    async def suffixes(self,
                       ctx: discord.ApplicationContext,
                       user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, True)
        if not valid:
            return
        if not data['suffix']:
            await ctx.respond(f"{user.mention} has no suffixes at the moment!")
            return
        embed = utils.get_embed_base(title=f"Suffixes for {user.name}")
        embed.add_field(name='Suffix', value='\n'.join(data['suffix']['contents']))
        await ctx.respond(embed=embed)

    @get_command.command(description="Get the biography of a transformed user")
    async def bio(self,
                  ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, True)
        if not valid:
            return
        if data['bio'] in ["", None]:
            await ctx.respond(f"{user.mention} has no biography set!")
            return
        embed = utils.get_embed_base(title=f"Biography for {user.name}")
        embed.add_field(name="", value=data['bio'])
        await ctx.respond(embed=embed)

    @get_command.command(description="Get a list of transformed users")
    async def transformed(self,
                          ctx: discord.ApplicationContext) -> None:
        tfee_data = utils.load_transformed(ctx.guild)['transformed_users']
        if tfee_data == {}:
            await ctx.respond("No one is transformed in this server, at the moment!")
            return
        description = ""
        for tfee in tfee_data:
            transformed_data = utils.load_tf_by_id(tfee, ctx.guild)
            transformed_data = transformed_data[
                str(ctx.channel.id) if str(ctx.channel.id) in transformed_data else 'all']
            into = transformed_data['into']
            description += f"{ctx.guild.get_member(int(tfee)).mention} is \"{into}\"\n\n"
        # Take off the last two new lines
        description = description[:-2]
        await ctx.respond(embed=utils.get_embed_base(title="Transformed Users", desc=description))


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Get(bot))

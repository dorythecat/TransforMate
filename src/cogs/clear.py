import discord
from discord.ext import commands

import src.utils as utils


class Clear(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    clear_command = discord.SlashCommandGroup("clear", "Clear various things about transformed users")

    @clear_command.command(description="Clear all settings for the transformed user")
    async def all_fields(self,
                         ctx: discord.ApplicationContext,
                         user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        utils.write_tf(user,
                       ctx.guild,
                       claim_user=None,
                       eternal=0,
                       prefix="",
                       suffix="",
                       big=0,
                       small=0,
                       hush=0,
                       backwards=0,
                       censor="",
                       sprinkle="",
                       muffle="",
                       alt_muffle="",
                       bio="")
        await ctx.respond(f"{user.mention} has been cleared of all settings!")

    @clear_command.command(description="Clear the prefix for the transformed messages")
    async def prefix(self,
                     ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        if not data['prefix']['active']:
            await ctx.respond(f"{user.mention} doesn't have a prefix set!")
            return
        utils.write_tf(user, ctx.guild, prefix="")
        await ctx.respond(f"Prefix for {user.mention} has been cleared!")

    @clear_command.command(description="Clear the suffix for the transformed messages")
    async def suffix(self,
                     ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        if not data['suffix']['active']:
            await ctx.respond(f"{user.mention} doesn't have a suffix set!")
            return
        utils.write_tf(user, ctx.guild, suffix="")
        await ctx.respond(f"Suffix for {user.mention} has been cleared!")

    @clear_command.command(description="Clear the big text setting for the transformed messages")
    async def big(self,
                  ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        if not data['big']:
            await ctx.respond(f"{user.mention} doesn't have big text set!")
            return
        utils.write_tf(user, ctx.guild, big=0)
        await ctx.respond(f"{user.mention} will no longer speak in big text!")

    @clear_command.command(description="Clear the small text setting for the transformed messages")
    async def small(self,
                    ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        if not data['small']:
            await ctx.respond(f"{user.mention} doesn't have small text set!")
            return
        utils.write_tf(user, ctx.guild, small=0)
        await ctx.respond(f"{user.mention} will no longer speak in small text!")

    @clear_command.command(description="Clear hush setting")
    async def hush(self,
                   ctx: discord.ApplicationContext,
                   user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        if not data['hush']:
            await ctx.respond(f"{user.mention} doesn't have hush text set!")
            return
        utils.write_tf(user, ctx.guild, hush=0)
        await ctx.respond(f"{user.mention} will no longer hush!")

    @clear_command.command(description="Clear backwards setting")
    async def backwards(self,
                        ctx: discord.ApplicationContext,
                        user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        if not data['backwards']:
            await ctx.respond(f"{user.mention} doesn't have backwards text set!")
            return
        utils.write_tf(user, ctx.guild, backwards=0)
        await ctx.respond(f"{user.mention} will no longer speak backwards!")

    @clear_command.command(description="Clear censor setting")
    async def censor(self,
                     ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None,
                     censor_word: discord.Option(discord.SlashCommandOptionType.string,
                                                 description="Word to clear") = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        if not data['censor']['active']:
            await ctx.respond(f"{user.mention} is not censored at the moment!")
            return
        if censor_word not in ["", None]:
            if censor_word not in data['censor']['contents']:
                await ctx.respond(f"{user.mention} is not censored with the word \"{censor_word}\"!")
                return
            data['censor']['contents'].remove(censor_word)
            utils.write_tf(user, ctx.guild, censor=data['censor'])
            return
        utils.write_tf(user, ctx.guild, censor="")
        await ctx.respond(f"{user.mention} will no longer have a censor set!")

    @clear_command.command(description="Clear sprinkle setting")
    async def sprinkle(self,
                       ctx: discord.ApplicationContext,
                       user: discord.Option(discord.User) = None,
                       sprinkle_word: discord.Option(discord.SlashCommandOptionType.string,
                                                     description="Word to clear") = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        # If the user is not sprinkled, we can just return
        if not data['sprinkle']['active']:
            await ctx.respond(f"{user.mention} is not sprinkled at the moment!")
            return
        # If a word is provided, we can check if it is in the contents array
        if sprinkle_word not in ["", None]:
            if sprinkle_word not in data['sprinkle']['contents']:
                await ctx.respond(f"{user.mention} is not sprinkled with the word \"{sprinkle_word}\"!")
                return
            data['sprinkle']['contents'].remove(sprinkle_word)
            utils.write_tf(user, ctx.guild, sprinkle=data['sprinkle'])
            await ctx.respond(f"{user.mention} will no longer have the word \"{sprinkle_word}\" sprinkled!")
            return
        utils.write_tf(user, ctx.guild, sprinkle="")
        await ctx.respond(f"{user.mention} will no longer have a sprinkle set!")

    @clear_command.command(description="Clear muffle settings")
    async def muffle(self,
                     ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None,
                     muffle_word: discord.Option(discord.SlashCommandOptionType.string,
                                                 description="Word to clear") = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        # If the user is not muffled, we can just return
        if not (data['muffle']['active'] or data['alt_muffle']['active']):
            await ctx.respond(f"{user.mention} is not muffled at the moment!")
            return
        # If a word is provided, we can check if it is in the contents array of both muffle and alt muffle fields
        muffle_type = 'muffle'
        if muffle_word not in ["", None]:
            if muffle_word not in data['muffle']['contents']:
                if muffle_word not in data['alt_muffle']['contents']:
                    await ctx.respond(f"{user.mention} is not muffled with the word \"{muffle_word}\"!")
                    return
                muffle_type = 'alt_muffle'
            data[muffle_type]['contents'].remove(muffle_word)
            if muffle_type == 'muffle':
                utils.write_tf(user, ctx.guild, muffle=data['muffle'])
            else:
                utils.write_tf(user, ctx.guild, alt_muffle=data['alt_muffle'])
            await ctx.respond(f"{user.mention} will no longer have the word \"{muffle_word}\" muffled!")
            return
        utils.write_tf(user, ctx.guild, muffle="", alt_muffle="")
        await ctx.respond(f"{user.mention} will no longer have a muffle set!")

    @clear_command.command(description="Clear eternal setting")
    async def eternal(self,
                      ctx: discord.ApplicationContext,
                      user: discord.Option(discord.User)) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        if not data['eternal']:
            await ctx.respond(f"{user.mention} isn't eternally transformed!")
            return
        utils.write_tf(user, ctx.guild, eternal=0)
        await ctx.respond(f"{user.mention} is no longer eternally transformed!")

    @clear_command.command(description="Clear a user's biography")
    async def bio(self,
                  ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, channel=ctx.channel)
        if not valid:
            return
        if data['bio'] in ["", None]:
            await ctx.respond(f"{user.mention} doesn't have a biography set!")
            return
        utils.write_tf(user, ctx.guild, bio="")
        await ctx.respond(f"{user.mention}'s biography has been cleared!")


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Clear(bot))

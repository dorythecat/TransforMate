import discord
from discord.ext import commands

import utils


class Set(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    set_command = discord.SlashCommandGroup("set", "Set various things about transformed users.")

    @set_command.command(description="Set a prefix for the transformed messages")
    async def prefix(self,
                     ctx: discord.ApplicationContext,
                     prefix: discord.Option(discord.SlashCommandOptionType.string,
                                            description="Prefix to add"),
                     chance: discord.Option(discord.SlashCommandOptionType.number,
                                            description="Chance for prefix to go off") = 30,
                     user: discord.Option(discord.User) = None,
                     whitespace: discord.Option(discord.SlashCommandOptionType.boolean,
                                                description="Add a space after the prefix "
                                                            "(defaults true)") = True) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        prefix += (" " * whitespace)
        utils.write_tf(user, ctx.guild, prefix=prefix, chance=chance)
        await ctx.respond(f"Prefix for {user.mention} set to \"{prefix.strip()}\"!")

    @set_command.command(description="Set a suffix for the transformed messages")
    async def suffix(self,
                     ctx: discord.ApplicationContext,
                     suffix: discord.Option(discord.SlashCommandOptionType.string,
                                            description="Suffix to add"),
                     chance: discord.Option(discord.SlashCommandOptionType.number,
                                            description="Chance for suffix to go off") = 30,
                     user: discord.Option(discord.User) = None,
                     whitespace: discord.Option(discord.SlashCommandOptionType.boolean,
                                                description="Add a space before the suffix (defaults true)") = True) \
            -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        suffix = (" " * whitespace) + suffix
        utils.write_tf(user, ctx.guild, suffix=suffix, chance=chance)
        await ctx.respond(f"Suffix for {user.mention} set to \"{suffix.strip()}\"!")

    @set_command.command(description="Set the transformed user to speak in big text")
    async def big(self,
                  ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        if data['big']:
            await ctx.respond(f"{user.mention} is already speaking big!")
            return
        utils.write_tf(user, ctx.guild, big=True)
        await ctx.respond(f"{user.mention} will now speak in big text!")

    @set_command.command(description="Set the transformed user to speak in small text")
    async def small(self,
                    ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        if data['small']:
            await ctx.respond(f"{user.mention} is already speaking small!")
            return
        utils.write_tf(user, ctx.guild, small=True)
        await ctx.respond(f"{user.mention} will now speak in small text!")

    @set_command.command(description="Set the transformed user to hush")
    async def hush(self,
                   ctx: discord.ApplicationContext,
                   user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        if data['hush']:
            await ctx.respond(f"{user.mention} is already hushed!")
            return
        utils.write_tf(user, ctx.guild, hush=True)
        await ctx.respond(f"{user.mention} will now hush!")

    @set_command.command(description="Set the transformed user to speak backwards")
    async def backwards(self,
                        ctx: discord.ApplicationContext,
                        user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        if data['backwards']:
            await ctx.respond(f"{user.mention} is already speaking backwards!")
            return
        utils.write_tf(user, ctx.guild, backwards=True)
        await ctx.respond(f"{user.mention} will now speak backwards!")

    @set_command.command(description="Set the transformed user to be eternally transformed")
    async def eternal(self,
                      ctx: discord.ApplicationContext,
                      user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        if data['claim'] == 0:
            await ctx.respond(f"{user.mention} isn't owned by anyone! Claim them to eternally transform them!")
            return
        if data['eternal']:
            await ctx.respond(f"{user.mention} is already eternally transformed!")
            return
        utils.write_tf(user, ctx.guild, eternal=True)
        await ctx.respond(f"{user.mention} is now eternally transformed!")

        transformed_data = utils.load_transformed(ctx.guild)
        if transformed_data['logs'][3]:
            embed = utils.get_embed_base(title="User Eternally Transformed", color=discord.Color.gold())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Eternally Transformed User", value=ctx.message.author.mention)
            embed.add_field(name="Channel", value=ctx.message.channel.mention)
            await ctx.guild.get_channel(transformed_data['logs'][3]).send(embed=embed)

    @set_command.command(description="Set the transformed user to be censored")
    async def censor(self,
                     ctx: discord.ApplicationContext,
                     censor: discord.Option(discord.SlashCommandOptionType.string,
                                            description="Text to censor"),
                     replacement: discord.Option(discord.SlashCommandOptionType.string,
                                                 description="Text to replace with"),
                     user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        utils.write_tf(user, ctx.guild, censor=censor, censor_replacement=replacement)
        await ctx.respond(f"{user.mention} will now have the word \"{censor}\" censored to \"{replacement}\"!")

    @set_command.command(description="Set the transformed user to have specific words sprinkled in their messages")
    async def sprinkle(self,
                       ctx: discord.ApplicationContext,
                       sprinkle: discord.Option(discord.SlashCommandOptionType.string,
                                                description="Text to sprinkle"),
                       chance: discord.Option(discord.SlashCommandOptionType.number,
                                              description='Chance for sprinkle to go off') = 30,
                       user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        utils.write_tf(user, ctx.guild, sprinkle=sprinkle, chance=chance)
        await ctx.respond(f"{user.mention} will now have the word \"{sprinkle}\" sprinkled in their messages!")

    @set_command.command(description="Set the transformed user to have their words/messages randomly replaced with a "
                                     "specific set of words")
    async def muffle(self,
                     ctx: discord.ApplicationContext,
                     muffle: discord.Option(discord.SlashCommandOptionType.string,
                                            description="Text that will replace others"),
                     chance: discord.Option(discord.SlashCommandOptionType.number,
                                            description='Chance for muffle to go off') = 30,
                     alt: discord.Option(discord.SlashCommandOptionType.boolean,
                                         description="Muffle full messages, instead of a per-word muffle.") = False,
                     user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        if alt:
            utils.write_tf(user, ctx.guild, alt_muffle=muffle, chance=chance)
            await ctx.respond(f"{user.mention} will now have their messages muffled with \"{muffle}\"!")
            return
        utils.write_tf(user, ctx.guild, muffle=muffle, chance=chance)
        await ctx.respond(f"{user.mention} will now have their words muffled with \"{muffle}\"!")

    @set_command.command(description="Set the transformed user to stutter on random words, with a certain chance")
    async def stutter(self,
                      ctx: discord.ApplicationContext,
                      chance: discord.Option(discord.SlashCommandOptionType.number,
                                             description="Chance to stutter") = 30,
                      user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        utils.write_tf(user, ctx.guild, stutter=chance)
        await ctx.respond(f"{user.mention} will now stutter when talking!")

    @set_command.command(description="Set a biography for the transformed user")
    async def bio(self,
                  ctx: discord.ApplicationContext,
                  biography: discord.Option(discord.SlashCommandOptionType.string,
                                            description="Biography for the transformed user"),
                  user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        utils.write_tf(user, ctx.guild, bio=biography)
        await ctx.respond(f"{user.mention}'s biography has been set!")

    @set_command.command(description="Set the nickname for the transformed user to their transformed name")
    async def nickname(self,
                       ctx: discord.ApplicationContext,
                       user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user)
        if not valid:
            return
        await user.edit(nick=data['into'])
        await ctx.respond(f"{user.mention}'s nickname has been set to their transformed name!")


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Set(bot))

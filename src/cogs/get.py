import discord
from discord.ext import commands

import utils

MAX_ITEMS_PER_PAGE: int = 10 # Max items per page for views

class PageView(discord.ui.View):
    embed_title: str = ""
    desc: str = ""
    total: int = 0
    offset: int = 0

    def __init__(self, embed_title: str, desc: str, total: int, offset: int = MAX_ITEMS_PER_PAGE) -> None:
        super().__init__(timeout=None)
        self.embed_title = embed_title
        self.desc = desc
        self.total = total
        self.offset = offset

    @discord.ui.button(label="⬅️ Previous Page", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_button_callback(self, button: discord.Button, interaction: discord.Interaction) -> None:
        if self.offset <= MAX_ITEMS_PER_PAGE:
            return
        self.next_button_callback.disabled = False
        self.offset -= MAX_ITEMS_PER_PAGE * 2
        desc = "\n\n".join(self.desc.split("\n\n")[self.offset:self.offset + MAX_ITEMS_PER_PAGE])
        footer = f"Page {self.offset // MAX_ITEMS_PER_PAGE + 1} of {(self.total - 1) // MAX_ITEMS_PER_PAGE + 1}"
        self.offset += MAX_ITEMS_PER_PAGE
        await interaction.response.edit_message(embed=utils.get_embed_base(self.embed_title, desc, footer), view=self)
        if self.offset <= MAX_ITEMS_PER_PAGE:
            button.disabled = True
            await interaction.message.edit(view=self)

    @discord.ui.button(label="Next Page ➡️", style=discord.ButtonStyle.primary)
    async def next_button_callback(self, button: discord.Button, interaction: discord.Interaction) -> None:
        if self.offset >= self.total:
            return
        self.previous_button_callback.disabled = False
        desc = "\n\n".join(self.desc.split("\n\n")[self.offset:self.offset + MAX_ITEMS_PER_PAGE])
        footer = f"Page {self.offset // MAX_ITEMS_PER_PAGE + 1} of {(self.total - 1) // MAX_ITEMS_PER_PAGE + 1}"
        self.offset += MAX_ITEMS_PER_PAGE
        await interaction.response.edit_message(embed=utils.get_embed_base(self.embed_title, desc, footer), view=self)
        if self.offset >= self.total:
            button.disabled = True
            await interaction.message.edit(view=self)

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
        embed = utils.get_embed_base(f"Settings for {user.name}:")
        embed.add_field(name="Prefix", value="Yes" if data['prefix'] != {} else "No")
        embed.add_field(name="Suffix", value="Yes" if data['suffix'] != {} else "No")
        embed.add_field(name="Big Text", value="Yes" if data['big'] else "No")
        embed.add_field(name="Small Text", value="Yes" if data['small'] else "No")
        embed.add_field(name="Hush", value="Yes" if data['hush'] else "No")
        embed.add_field(name="Backwards", value="Yes" if data['backwards'] else "No")
        embed.add_field(name="Censor", value="Yes" if data['censor'] != {} else "No")
        embed.add_field(name="Sprinkle", value="Yes" if data['sprinkle'] != {} else "No")
        embed.add_field(name="Muffle", value="Yes" if data['muffle'] != {} else "No")
        embed.add_field(name="Alt Muffle", value="Yes" if data['alt_muffle'] != {} else "No")
        embed.add_field(name="Stutter", value=f"{data['stutter']}%")
        await ctx.respond(embed=embed)


    @get_command.command(description="Get who has claimed this transformed user")
    async def claim(self,
                    ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, True)
        if not valid:
            return
        if data['claim'] == 0:
            await ctx.respond(f"{user.mention} hasn't been claimed by anyone (yet)!")
            return
        await ctx.respond(f"{user.mention} is claimed by {ctx.guild.get_member(data['claim']).mention}!")

    @get_command.command(description="List the censors for the transformed user")
    async def censors(self,
                      ctx: discord.ApplicationContext,
                      user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, True)
        if not valid:
            return
        if data['censor'] == {}:
            await ctx.respond(f"{user.mention} is not censored at the moment!")
            return

        desc: str = ""
        for censor in data['censor']:
            desc += f"**{censor}**: {data['censor'][censor]}\n\n"

        view: PageView | None = None
        footer: str | None = None
        if len(data['censor']) > MAX_ITEMS_PER_PAGE:
            view = PageView(f"Censors for {user.name}:", desc, len(data['censor']))
            footer = f"Page 1 of {(len(data['censor']) - 1) // MAX_ITEMS_PER_PAGE + 1}"
        desc = "\n\n".join(desc.split("\n\n")[:MAX_ITEMS_PER_PAGE])
        await ctx.respond(embed=utils.get_embed_base(f"Censors for {user.name}:", desc, footer), view=view)

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

        desc: str = ""
        for sprinkle in data['sprinkle']:
            desc += f"**{sprinkle}**: {data['sprinkle'][sprinkle]}%\n\n"

        view: PageView | None = None
        footer: str | None = None
        if len(data['sprinkle']) > MAX_ITEMS_PER_PAGE:
            view = PageView(f"Sprinkles for {user.name}:", desc, len(data['sprinkle']))
            footer = f"Page 1 of {(len(data['sprinkle']) - 1) // MAX_ITEMS_PER_PAGE + 1}"
        desc = "\n\n".join(desc.split("\n\n")[:MAX_ITEMS_PER_PAGE])
        await ctx.respond(embed=utils.get_embed_base(f"Sprinkles for {user.name}:", desc, footer), view=view)

    @get_command.command(description="List the muffle for the transformed user")
    async def muffle(self,
                     ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, True)
        if not valid:
            return
        if not (data['muffle'] or data['alt_muffle']):
            await ctx.respond(f"{user.mention} has no muffles at the moment!")

        if data['muffle']:
            desc: str = ""
            for muffle in data['muffle']:
                desc += f"**{muffle}**: {data['muffle'][muffle]}%\n\n"

            view: PageView | None = None
            footer: str | None = None
            if len(data['muffle']) > MAX_ITEMS_PER_PAGE:
                view = PageView(f"Muffles for {user.name}:", desc, len(data['muffle']))
                footer = f"Page 1 of {(len(data['muffle']) - 1) // MAX_ITEMS_PER_PAGE + 1}"
            desc = "\n\n".join(desc.split("\n\n")[:MAX_ITEMS_PER_PAGE])
            await ctx.respond(embed=utils.get_embed_base(f"Muffles for {user.name}:", desc, footer), view=view)

        if data['alt_muffle']:
            desc: str = ""
            for alt_muffle in data['alt_muffle']:
                desc += f"**{alt_muffle}**: {data['alt_muffle'][alt_muffle]}%\n\n"

            view: PageView | None = None
            footer: str | None = None
            if len(data['alt_muffle']) > MAX_ITEMS_PER_PAGE:
                view = PageView(f"Alternative muffles for {user.name}:", desc, len(data['alt_muffle']))
                footer = f"Page 1 of {(len(data['alt_muffle']) - 1) // MAX_ITEMS_PER_PAGE + 1}"
            desc = "\n\n".join(desc.split("\n\n")[:MAX_ITEMS_PER_PAGE])
            await ctx.respond(embed=utils.get_embed_base(f"Alternative muffles for {user.name}:", desc, footer), view=view)

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

        desc: str = ""
        for prefix in data['prefix']:
            desc += f"**{prefix}**: {data['prefix'][prefix]}%\n\n"

        view: PageView | None = None
        footer: str | None = None
        if len(data['prefix']) > MAX_ITEMS_PER_PAGE:
            view = PageView(f"Prefixes for {user.name}:", desc, len(data['prefix']))
            footer = f"Page 1 of {(len(data['prefix']) - 1) // MAX_ITEMS_PER_PAGE + 1}"
        desc = "\n\n".join(desc.split("\n\n")[:MAX_ITEMS_PER_PAGE])
        await ctx.respond(embed=utils.get_embed_base(f"Prefixes for {user.name}:", desc, footer), view=view)

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

        desc: str = ""
        for suffix in data['suffix']:
            desc += f"**{suffix}**: {data['suffix'][suffix]}%\n\n"

        view: PageView | None = None
        footer: str | None = None
        if len(data['suffix']) > MAX_ITEMS_PER_PAGE:
            view = PageView(f"Suffixes for {user.name}:", desc, len(data['suffix']))
            footer = f"Page 1 of {(len(data['suffix']) - 1) // MAX_ITEMS_PER_PAGE + 1}"
        desc = "\n\n".join(desc.split("\n\n")[:MAX_ITEMS_PER_PAGE])
        await ctx.respond(embed=utils.get_embed_base(f"Suffixes for {user.name}:", desc, footer), view=view)

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
        await ctx.respond(embed=utils.get_embed_base(f"Biography for {user.name}:", data['bio']))

    @get_command.command(description="Get a list of transformed users")
    async def transformed(self,
                          ctx: discord.ApplicationContext) -> None:
        tfee_data = utils.load_transformed(ctx.guild)['transformed_users']
        if tfee_data == {}:
            await ctx.respond("No one is transformed in this server, at the moment!")
            return

        users: int = 0
        desc: str = ""
        for tfee in tfee_data:
            transformed_data = utils.load_tf(int(tfee), ctx.guild)
            if transformed_data == {}:
                continue
            into = transformed_data['into']
            desc += f"<@{tfee}> is \"{into}\"\n\n"
            users += 1

        view: PageView | None = None
        footer: str | None = None
        if users > MAX_ITEMS_PER_PAGE:
            view = PageView("Transformed Users", desc, users)
            footer = f"Page 1 of {(users - 1) // MAX_ITEMS_PER_PAGE + 1}"
        desc = "\n\n".join(desc.split("\n\n")[:MAX_ITEMS_PER_PAGE])
        await ctx.respond(embed=utils.get_embed_base("Transformed Users", desc, footer), view=view)

    @get_command.command(description="Get the profile image of a transformed user")
    async def image(self,
                    ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None) -> None:
        valid, data, user = await utils.extract_tf_data(ctx, user, True)
        if not valid:
            return
        await ctx.respond(f"{user.mention}'s image for [{data['into']}]({data['image_url']})")


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Get(bot))

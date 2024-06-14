import os
import utils

from dotenv import load_dotenv

import discord

intents = discord.Intents.all()

bot = discord.Bot(intents=intents)


# Transformation functions
async def transform_function(ctx: discord.ApplicationContext,
                             user: discord.User,
                             into: str,
                             image_url: str,
                             channel: discord.TextChannel):
    if not image_url:
        image_url = user.avatar.url
    if image_url[:4] != "http":
        return await ctx.send("Invalid URL! Please provide a valid image URL!")
    if "?" in image_url:
        image_url = image_url[:image_url.index("?")]  # Prune url

    utils.write_tf(user, ctx.guild, channel, ctx.author.name, into, image_url)
    utils.write_transformed(user, ctx.guild)


# Bot startup
@bot.event
async def on_ready():
    print(f'\nSuccessfully logged into Discord as "{bot.user}"\n')
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.watching,
                                                        name="people get transformed"))


# Message sent
@bot.event
async def on_message(message: discord.Message):
    # Check if the message is sent by the bot, we don't want an endless loop that ends on an error/crash, do we?
    if message.author == bot.user:
        return

    # Check if user is transformed, and send their messages as webhooks, deleting the original
    if utils.is_transformed(message.author, message.guild):
        if message.content.startswith('('):
            return
        data = utils.load_tf(message.author, message.guild)
        if str(message.channel.id) in data:
            data = data[str(message.channel.id)]
        elif 'all' in data:
            data = data['all']
        else:
            return
        name = data['into']
        image_url = data['image_url']

        webhook = utils.get_webhook_by_name(await message.channel.webhooks(), name)
        if not webhook:
            webhook = await message.channel.create_webhook(name=name)

        if message.content:  # If there's no content, and we try to send it, it will trigger a 400 error
            if message.reference:
                await webhook.send(f"**Replying to {message.reference.resolved.author.mention}:**\n",
                                   avatar_url=image_url)
                if message.reference.resolved.content:
                    await webhook.send(f">>> {message.reference.resolved.content}",
                                       avatar_url=image_url, wait=True)
            await webhook.send(utils.transform_text(data, message.content), avatar_url=image_url, wait=True)
        for attachment in message.attachments:
            if (attachment.url[:attachment.url.index("?")] if "?" in attachment.url else attachment.url) == image_url:
                return
            await webhook.send(file=await attachment.to_file(), avatar_url=image_url)
        await message.delete()

        if message.stickers:
            await message.author.send("Sorry, but we don't support stickers, at the moment! :(")


# Reaction added
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    # Check if reaction is reacting to a message sent by a transformed user
    if str(reaction.emoji) == "❓":
        transformed = utils.load_transformed(reaction.message.guild)
        for tfed in transformed:
            data = utils.load_tf_by_name(tfed, reaction.message.guild)
            if str(reaction.message.channel.id) in data:
                data = data[str(reaction.message.channel.id)]
            elif 'all' in data:
                data = data['all']
            else:
                return
            if data['into'] == reaction.message.author.name:
                await user.send(f"*{reaction.message.author.name}* is, in fact, *{tfed}*!\n"
                                f"(Transformed by *{data['transformed_by']}*)")
                await reaction.remove(user)


# Transformation commands
@bot.slash_command(description="Transform someone")
async def transform(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None,
                    into: discord.Option(discord.SlashCommandOptionType.string,
                                         description="Who to transform") = None,
                    image_url: discord.Option(discord.SlashCommandOptionType.string,
                                              description="Image URL to use") = None,
                    channel: discord.Option(discord.TextChannel,
                                            description="Transform the user only on this channel") = None):
    if not user:
        user = ctx.author

    if utils.is_transformed(user, ctx.guild):
        data = utils.load_tf(user, ctx.guild)
        channel_id = ctx.channel.id if not channel else channel.id
        if str(channel_id) in data:
            data = data[str(ctx.channel.id)]
        elif 'all' in data:
            data = data['all']
        else:
            return
        if data['claim'] is not None and data['claim'] != ctx.author.name:
            return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}!")
        if data['eternal'] and ctx.author.name != data['claim'] and data['claim'] is not None:
            if ctx.author.name != user.name:
                return await ctx.respond(
                    f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
            return await ctx.respond(f"Your master can't allow you to transform, at least for now...")

    if into:
        if len(into.strip()) <= 1:
            return await ctx.send("Please provide a name longer than 1 character!")
        await transform_function(ctx, user, into, image_url, channel)
        await ctx.respond(f'You have transformed {user.mention} into "{into}"!')
        return

    await ctx.respond(f"What do we want to transform {user.mention} into? (Send CANCEL to cancel)")
    response = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    if response.content.strip() == "CANCEL":
        return await ctx.respond("Cancelled the transformation!")
    if len(response.content.strip()) <= 1:
        return await ctx.send("Please provide a name longer than 1 character!")
    await transform_function(ctx,
                             user,
                             response.content,
                             response.attachments[0].url if response.attachments else None,
                             channel)
    await ctx.respond(f'You have transformed {user.mention} into "{response.content}"!')


@bot.slash_command(description="Return someone to their previous state")
async def goback(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    data = utils.load_tf(user, ctx.guild)
    if str(ctx.channel.id) in data:
        data = data[str(ctx.channel.id)]
    elif 'all' in data:
        data = data['all']
    else:
        return await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to!"
                                 f"(At least on this channel)")
    into = data['into']

    if not utils.is_transformed(user, ctx.guild):
        if into == "":
            return await ctx.respond(f"{user.mention} is not transformed at the moment, and has no form to go back to!")
        utils.write_transformed(user, ctx.guild)
        return await ctx.respond(f"{user.mention} has been turned back to their last form!")

    if data['eternal'] and ctx.author.name != data['claim']:
        if ctx.author.name != user.name:
            return await ctx.respond(
                f"You can't do that! {user.mention} is eternally transformed by {data['claim']}!")
        return await ctx.respond(f"Your master won't allow you to turn back, at least for now...")

    utils.remove_transformed(user, ctx.guild)

    # Delete all webhooks with the same name
    # This can lead to deleting more webhooks than we need to, but it shouldn't cause too much of a performance hit
    for wh in await ctx.guild.webhooks():
        if wh.name == into:
            await wh.delete()
    await ctx.respond(f"{user.mention} has been turned back to normal!")


@bot.slash_command(description="Claim a transformed user")
async def claim(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User)):
    if user == ctx.author:
        return await ctx.respond(f"You can't claim yourself!")
    if not utils.is_transformed(user, ctx.guild):
        return await ctx.respond(f"{user.mention} is not transformed at the moment, you can't claim them!")
    data = utils.load_tf(user, ctx.guild)
    channel = None
    if str(ctx.channel) in data:
        data = data[str(ctx.channel)]
        channel = ctx.channel
    else:
        data = data['all']
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} has been claimed already by {data['claim']}!")
    utils.write_tf(user, ctx.guild, channel, claim_user=ctx.author.name)
    await ctx.respond(f"You have successfully claimed {user.mention} for yourself! Hope you enjoy!")


@bot.slash_command(description="Unclaim a transformed user")
async def unclaim(ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User)):
    if user == ctx.author:
        return await ctx.respond(f"You can't unclaim yourself! Only your master can do that!\n"
                                 f"||Use \"/safeword\", if you actually want to unclaim yourself.||")
    data = utils.load_tf(user, ctx.guild)
    channel = None
    if str(ctx.channel) in data:
        data = data[str(ctx.channel)]
        channel = ctx.channel
    else:
        data = data['all']
    if data['claim'] is None:
        return await ctx.respond(f"{user.mention} is currently not claimed by anyone!")
    if data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is claimed by {data['claim']}, not you!")
    utils.write_tf(user, ctx.guild, channel, claim_user="", eternal=0)
    await ctx.respond(f"You have successfully unclaimed {user.mention}! They are now free from your grasp!")


@bot.slash_command(description="Safeword command. Use in case of abuse or incomodity, to unclaim yourself.")
async def safeword(ctx: discord.ApplicationContext):
    data = utils.load_tf(ctx.author, ctx.guild)
    channel = None
    if str(ctx.channel) in data:
        data = data[str(ctx.channel)]
        channel = ctx.channel
    else:
        data = data['all']
    # We have to check if they are claimed OR eternally transformed. If both are false, safeword does nothing.
    # If either are true, we need to keep going, otherwise we can just return.
    if data['claim'] is None and not data['eternal']:
        return await ctx.respond(f"You can't do that! You are not claimed by anyone!")
    utils.write_tf(ctx.author, ctx.guild, channel, claim_user="", eternal=0)
    await ctx.respond(f"You have successfully activated the safeword command.\n"
                      f"Please, sort out any issues with your rp partner(s) before you continue using the bot .\n"
                      f"Use \"/goback\" to return to your normal self.")


# "Set" Commands
set_command = bot.create_group("set", "Set various things about transformed users")


@set_command.command(description="Set a prefix for the transformed messages")
async def prefix(ctx: discord.ApplicationContext,
                 prefix: discord.Option(discord.SlashCommandOptionType.string,
                                        description="Prefix to add"),
                 prefix_chance: discord.Option(discord.SlashCommandOptionType.integer, description="Chance for prefix to go off") = 30,
                 user: discord.Option(discord.User) = None,
                 whitespace: discord.Option(discord.SlashCommandOptionType.boolean,
                                            description="Add a space after the prefix (defaults true)") = True):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    if whitespace:
        prefix = prefix + " "
    utils.write_tf(user, ctx.guild, prefix=prefix, type="prefix", chance=prefix_chance)
    await ctx.respond(f"Prefix for {user.mention} set to \"*{prefix}*\"!")


@set_command.command(description="Set a suffix for the transformed messages")
async def suffix(ctx: discord.ApplicationContext,
                 suffix: discord.Option(discord.SlashCommandOptionType.string,
                                        description="Suffix to add"),
                 suffix_chance: discord.Option(discord.SlashCommandOptionType.integer, description="Chance for suffix to go off") = 30,
                 user: discord.Option(discord.User) = None,
                 whitespace: discord.Option(discord.SlashCommandOptionType.boolean,
                                            description="Add a space before the suffix (defaults true)") = True):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    if whitespace:
        suffix = " " + suffix
    utils.write_tf(user, ctx.guild, suffix=suffix, type="suffix", chance=suffix_chance)
    await ctx.respond(f"Suffix for {user.mention} set to \"*{suffix}*\"!")


@set_command.command(description="Set the transformed user to speak in big text")
async def big(ctx: discord.ApplicationContext,
              user: discord.Option(discord.User) = None):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if data['big']:
        return await ctx.respond(f"{user.mention} is already speaking big!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, big=1)
    await ctx.respond(f"{user.mention} will now speak in big text!")


@set_command.command(description="Set the transformed user to speak in small text")
async def small(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User) = None):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if data['small']:
        return await ctx.respond(f"{user.mention} is already speaking small!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, small=1)
    await ctx.respond(f"{user.mention} will now speak in small text!")


@set_command.command(description="Set the transformed user to hush")
async def hush(ctx: discord.ApplicationContext,
               user: discord.Option(discord.User) = None):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if data['hush']:
        return await ctx.respond(f"{user.mention} is already hushed!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, hush=1)
    await ctx.respond(f"{user.mention} will now hush!")


@set_command.command(description="Set the transformed user to be eternally transformed")
async def eternal(ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User)):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if data['eternal']:
        return await ctx.respond(f"{user.mention} is already eternally transformed!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, eternal=1)
    await ctx.respond(f"{user.mention} is now eternally transformed!")


@set_command.command(description="Set the transformed user to be censored")
async def censor(ctx: discord.ApplicationContext,
                    censor: discord.Option(discord.SlashCommandOptionType.string,
                                            description="Word to censor"),
                    replacement: discord.Option(discord.SlashCommandOptionType.string,
                                                description="Word to replace with"),
                    user: discord.Option(discord.User) = None):
        valid, data, user = await utils.logic_command(ctx, user)
        if not valid:
            return
        if data['claim'] is not None and data['claim'] != ctx.author.name:
            return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
        utils.write_tf(user, ctx.guild, censor=censor, censor_replacement=replacement)
        await ctx.respond(f"{user.mention} will now have the word \"{censor}\" censored to \"{replacement}\"!")

@set_command.command(description="Set the transformed user to have specific words sprinkled in their messages")
async def sprinkle(ctx: discord.ApplicationContext,
                   sprinkle: discord.Option(discord.SlashCommandOptionType.string,
                                            description="Word to sprinkle"),
                    sprinkle_chance: discord.Option(discord.SlashCommandOptionType.integer,
                                                    description='Chance for sprinkle to go off') = 30,
                    user: discord.Option(discord.User) = None):
        valid, data, user = await utils.logic_command(ctx, user)
        if not valid:
            return
        if data['claim'] is not None and data['claim'] != ctx.author.name:
            return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
        utils.write_tf(user, ctx.guild, sprinkle=sprinkle, type="sprinkle", chance=sprinkle_chance)
        await ctx.respond(f"{user.mention} will now have the word \"{sprinkle}\" sprinkled in their messages!")

@set_command.command(description="Set the transformed user to have their words randomly replaced with a specific set of words")
async def muffle(ctx: discord.ApplicationContext,
                    muffle: discord.Option(discord.SlashCommandOptionType.string,
                                            description="Word that will replace words"),
                    chance: discord.Option(discord.SlashCommandOptionType.integer,
                                           description='Chance for muffle to go off') = 30,
                    user: discord.Option(discord.User) = None):
        valid, data, user = await utils.logic_command(ctx, user)
        if not valid:
            return
        if data['claim'] is not None and data['claim'] != ctx.author.name:
            return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
        utils.write_tf(user, ctx.guild, muffle=muffle, type="muffle", chance=chance)
        await ctx.respond(f"{user.mention} will now have their words muffled with \"{muffle}\"!")

# 'List' commands
list_command = bot.create_group("list", "List various things about transformed users")


@list_command.command(description="List the settings for the transformed user")
async def settings(ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None):
     valid, data, user = await utils.logic_command(ctx, user)
     if not valid:
        return
     # Create embed
     embed = discord.Embed(title=f"Settings for {user.name}",
                        description="Here are the settings for the transformed user",
                        color=discord.Color.blue())
     embed.add_field(name="Prefix", value=f"{data['prefix']['chance']}%" if data['prefix'] else "None")
     embed.add_field(name="Suffix", value=f"{data['suffix']['chance']}%" if data['suffix'] else "None")
     embed.add_field(name="Big Text", value="Yes" if data['big'] else "No")
     embed.add_field(name="Small Text", value="Yes" if data['small'] else "No")
     embed.add_field(name="Hush", value="Yes" if data['hush'] else "No")
     embed.add_field(name="Censor", value="Yes" if data['censor']['active'] else "No")
     embed.add_field(name="Sprinkle", value=f"{data['sprinkle']['chance']}%" if data['sprinkle'] else "None")
     embed.add_field(name="Muffle", value=f"{data['muffle']['chance']}%" if data['muffle'] else "None")
     await ctx.respond(embed=embed)

@list_command.command(description="List the censors for the transformed user")
async def censors(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None):
     valid, data, user = await utils.logic_command(ctx, user)
     if not valid:
        return
     # Create embed
     embed = discord.Embed(title=f"Censors for {user.name}",
                        description="Here are the censors for the transformed user",
                        color=discord.Color.blue())
     if data['censor']['active']:
          for word in data['censor']['contents']:
               embed.add_field(name=word, value=data['censor']['contents'][word])
     else:
          return await ctx.respond(f"{user.mention} is not censored at the moment!")
     await ctx.respond(embed=embed)

@list_command.command(description="List the sprinkles for the transformed user")
async def sprinkles(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None):
     valid, data, user = await utils.logic_command(ctx, user)
     if not valid:
        return
     # Create embed
     embed = discord.Embed(title=f"Sprinkles for {user.name}",
                        description="Here are the sprinkles for the transformed user",
                        color=discord.Color.blue())
     if data['sprinkle']:
            embed.add_field(name='Sprinkle(s)', value=data['sprinkle']['contents'])
     else:
          return await ctx.respond(f"{user.mention} has no sprinkles at the moment!")
     await ctx.respond(embed=embed)

@list_command.command(description="List the muffle for the transformed user")
async def muffle(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User) = None):
        valid, data, user = await utils.logic_command(ctx, user)
        if not valid:
            return
        # Create embed
        embed = discord.Embed(title=f"Muffle for {user.name}",
                        description="Here are the muffles the transformed user has",
                        color=discord.Color.blue())
        if data['muffle']:
            embed.add_field(name='Muffle(s)', value=data['muffle']['contents'])
        else:
            return await ctx.respond(f"{user.mention} has no muffles at the moment!")
        await ctx.respond(embed=embed)

@list_command.command(description="List the prefixes for the transformed user")
async def prefixes(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None):
     valid, data, user = await utils.logic_command(ctx, user)
     if not valid:
        return
     # Create embed
     embed = discord.Embed(title=f"Prefixes for {user.name}",
                        description="Here are the prefixes for the transformed user",
                        color=discord.Color.blue())
     if data['prefix']:
          embed.add_field(name='Prefix', value='\n'.join(data['prefix']['contents']))
     else:
          return await ctx.respond(f"{user.mention} has no prefixes at the moment!")
     await ctx.respond(embed=embed)
    
@list_command.command(description="List the suffixes for the transformed user")
async def suffixes(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None):
     valid, data, user = await utils.logic_command(ctx, user)
     if not valid:
        return
     # Create embed
     embed = discord.Embed(title=f"Suffixes for {user.name}",
                        description="Here are the suffixes for the transformed user",
                        color=discord.Color.blue())
     if data['suffix']:
          # Make field value all suffixes, with a new line in between
            embed.add_field(name='Suffix', value='\n'.join(data['suffix']['contents']))
     else:
          return await ctx.respond(f"{user.mention} has no suffixes at the moment!")
     await ctx.respond(embed=embed)

@list_command.command(description="Get a list of transformed users")
async def transformed(ctx: discord.ApplicationContext):
    transformed = utils.load_transformed(ctx.guild)
    if not transformed:
        return await ctx.respond("No one is transformed (globally) at the moment!")
    description = ""
    for user in transformed:
        # get their transformed name
        transformed_data = utils.load_tf_by_name(user, ctx.guild)
        if 'all' in transformed_data:
            transformed_data = transformed_data['all']
        else:
            transformed_data = transformed_data[str(ctx.channel.id)]
        into = transformed_data['into']
        description += f"**{user}** -> *{into}*\n\n"
    # Take off the last two new lines
    description = description[:-2]
    embed = discord.Embed(title="Transformed Users",
                          description=description,
                          color=discord.Color.blue())
    await ctx.respond(embed=embed)
    

# "Clear" commands
clear_command = bot.create_group("clear", "Clear various things about transformed users")


@clear_command.command(description="Clear all settings for the transformed user")
async def all_fields(ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User) = None):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user,
                   ctx.guild,
                   claim_user="",
                   eternal=0,
                   prefix="",
                   suffix="",
                   big=0,
                   small=0,
                   hush=0,
                   censor="",
                   sprinkle="",
                   muffle="",
                   clear_contents=True)
    await ctx.respond(f"{user.mention} has been cleared of all settings!")


@clear_command.command(description="Clear the prefix for the transformed messages")
async def prefix(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if data['prefix'] is None:
        return await ctx.respond(f"{user.mention} doesn't have a prefix set!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, prefix="")
    await ctx.respond(f"Prefix for {user.mention} has been cleared!")


@clear_command.command(description="Clear the suffix for the transformed messages")
async def suffix(ctx: discord.ApplicationContext,
                 user: discord.Option(discord.User) = None):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if data['suffix'] is None:
        return await ctx.respond(f"{user.mention} doesn't have a suffix set!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, suffix="")
    await ctx.respond(f"Suffix for {user.mention} has been cleared!")


@clear_command.command(description="Clear the big text setting for the transformed messages")
async def big(ctx: discord.ApplicationContext,
              user: discord.Option(discord.User) = None):
    if user is None:
        user = ctx.author
    transformed = utils.load_transformed(ctx.guild)
    if user.name not in transformed:
        return await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
    data = utils.load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if not data['big']:
        return await ctx.respond(f"{user.mention} doesn't have big text set!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, big=0)
    await ctx.respond(f"{user.mention} will no longer speak in big text!")


@clear_command.command(description="Clear the small text setting for the transformed messages")
async def small(ctx: discord.ApplicationContext,
                user: discord.Option(discord.User) = None):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if not data['small']:
        return await ctx.respond(f"{user.mention} doesn't have small text set!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, small=0)
    await ctx.respond(f"{user.mention} will no longer speak in small text!")


@clear_command.command(description="Clear hush setting")
async def hush(ctx: discord.ApplicationContext,
               user: discord.Option(discord.User) = None):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if not data['hush']:
        return await ctx.respond(f"{user.mention} doesn't have hush set!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, hush=0)
    await ctx.respond(f"{user.mention} will no longer hush!")

@clear_command.command(description="Clear censor setting")
async def censor(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.User) = None,
                    censor_word: discord.Option(discord.SlashCommandOptionType.string,
                                                description="Word to clear") = None):
        valid, data, user = await utils.logic_command(ctx, user)
        if not valid:
            return
        
        if data['claim'] is not None and data['claim'] != ctx.author.name:
            return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
        # If the user is not censored, we can just return
        if data['censor']['active'] == 0:
            return await ctx.respond(f"{user.mention} is not censored at the moment!")
        # If a word is provided, we can check if it is in the contents array
        if censor_word is not None:
            if censor_word not in data['censor']['contents']:
                return await ctx.respond(f"{user.mention} is not censored with the word \"{censor_word}\"!")
            data['censor']['contents'].remove(censor_word)
            utils.write_tf(user, ctx.guild, censor=data['censor'])
            return await ctx.respond(f"{user.mention} will no longer have the word \"{censor_word}\" censored!")

        # If no word is provided, we can just clear the censor contents completely
        utils.write_tf(user, ctx.guild, censor_bool=0)
        await ctx.respond(f"{user.mention} will no longer have a censor set!")

@clear_command.command(description="Clear sprinkle setting")
async def sprinkle(ctx: discord.ApplicationContext,
                   user: discord.Option(discord.User) = None,
                     sprinkle_word: discord.Option(discord.SlashCommandOptionType.string,
                                                  description="Word to clear") = None):
        valid, data, user = await utils.logic_command(ctx, user)
        if not valid:
            return
        if data['claim'] is not None and data['claim'] != ctx.author.name:
            return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
        # If the user is not sprinkled, we can just return
        if data['sprinkle']['active'] == 0:
            return await ctx.respond(f"{user.mention} is not sprinkled at the moment!")
        # If a word is provided, we can check if it is in the contents array
        if sprinkle_word is not None:
            if sprinkle_word not in data['sprinkle']['contents']:
                return await ctx.respond(f"{user.mention} is not sprinkled with the word \"{sprinkle_word}\"!")
            data['sprinkle']['contents'].remove(sprinkle_word)
            utils.write_tf(user, ctx.guild, sprinkle=data['sprinkle'])
            return await ctx.respond(f"{user.mention} will no longer have the word \"{sprinkle_word}\" sprinkled!")
        utils.write_tf(user, ctx.guild, sprinkle_bool=0)
        await ctx.respond(f"{user.mention} will no longer have a sprinkle set!")

@clear_command.command(description="Clear muffle setting")
async def muffle(ctx: discord.ApplicationContext,
                   user: discord.Option(discord.User) = None,
                     muffle_word: discord.Option(discord.SlashCommandOptionType.string,
                                                  description="Word to clear") = None):
        valid, data, user = await utils.logic_command(ctx, user)
        if not valid:
            return
        if data['claim'] is not None and data['claim'] != ctx.author.name:
            return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
        # If the user is not muffled, we can just return
        if data['muffle']['active'] == 0:
            return await ctx.respond(f"{user.mention} is not muffled at the moment!")
        # If a word is provided, we can check if it is in the contents array
        if muffle_word is not None:
            if muffle_word not in data['muffle']['contents']:
                return await ctx.respond(f"{user.mention} is not muffled with the word \"{muffle_word}\"!")
            data['muffle']['contents'].remove(muffle_word)
            utils.write_tf(user, ctx.guild, muffle=data['muffle'])
            return await ctx.respond(f"{user.mention} will no longer have the word \"{muffle_word}\" muffled!")
        utils.write_tf(user, ctx.guild, muffle_bool=0)
        await ctx.respond(f"{user.mention} will no longer have a muffle set!")

@clear_command.command(description="Clear eternal setting")
async def eternal(ctx: discord.ApplicationContext,
                  user: discord.Option(discord.User)):
    valid, data, user = await utils.logic_command(ctx, user)
    if not valid:
        return
    if not data['eternal']:
        return await ctx.respond(f"{user.mention} isn't eternally transformed!")
    if data['claim'] is not None and data['claim'] != ctx.author.name:
        return await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}! You can't do that!")
    utils.write_tf(user, ctx.guild, eternal=0)
    await ctx.respond(f"{user.mention} is no longer eternally transformed!")


# Misc commands
@bot.slash_command(description="Replies with the bot's latency.")
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond(f"Pong! ({bot.latency * 1000:.0f}ms)")

# @bot.slash_command(description="Get the bot's invite link")

@bot.slash_command(description="See information about the bot")
async def info(ctx: discord.ApplicationContext):
    embed = discord.Embed(title="Transformation Bot",
                          description="A bot that transforms users into other users, and lets them speak as them!",
                          color=discord.Color.blue())
    embed.add_field(name="Creators", value="dorythecat\nipabapi")
    embed.add_field(name="Library", value="pycord")
    embed.add_field(name="Source Code", value="[GitHub](https://github.com/dorythecat/transformate)")
    await ctx.respond(embed=embed)


@bot.slash_command(description="Kill all webhooks, and let the bot regenerate them")
@discord.default_permissions(administrator=True)
async def killhooks(ctx: discord.ApplicationContext):
    for wh in await ctx.guild.webhooks():
        await wh.delete()
    await ctx.respond("All webhooks have been deleted! The bot will regenerate them as needed.")


# Start the bot up
load_dotenv()
bot.run(os.getenv("BOT_TOKEN"))

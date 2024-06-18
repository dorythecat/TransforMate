import json
import os
import random

import discord

# SETTINGS
CLEAR_OLD_TFEE_DATA = True  # If a file is from a previous version, should it be cleared out?
CLEAR_OLD_TRANSFORMED_DATA = True  # Same as above

# DATA VERSIONS
# REMEMBER TO REGENERATE ALL TRANSFORMATION DATA IF YOU CHANGE THE VERSION
# VERSION 7: Added "bio" field
# VERSION 6: Added "blocked_channels" field
# VERSION 5: Fixing the fields to accept multiple values as well as a percentage chance for each field.
# VERSION 4: Reworked to work with per-channel data. - DROPPED SUPPORT FOR TRANSLATING PREVIOUS VERSIONS
# VERSION 3: Added "big", "small", and "hush" fields, and changed "eternal" from bool to int
# VERSION 2: Added guild specific data
# VERSION 1: Base version
CURRENT_TFEE_DATA_VERSION = 7

# VERSION 4: Each user now stores the channels they're transformed on
# VERSION 3: Added "blocked_users" field
# VERSION 2: Added "blocked_channels" and "transformed_users" fields
# VERSION 1: Base version
CURRENT_TRANSFORMED_DATA_VERSION = 4


# USER TRANSFORMATION DATA UTILS
# TODO: Why can't we just return an empty dict???
def load_tf_by_id(user_id: str, guild: discord.Guild = None) -> dict:
    if f"{user_id}.json" not in os.listdir("cache/people"):
        return {}
    with open(f"cache/people/{user_id}.json", "r") as f:
        contents = f.read()
        if contents.strip() == "":
            return {}
        data = json.loads(contents)
        if guild is None:
            return data
        else:
            if str(guild.id) in data:
                return data[str(guild.id)]
            return {}


def load_tf(user: discord.User, guild: discord.Guild = None) -> dict:
    return load_tf_by_id(str(user.id), guild)


def write_tf(user: discord.User,
             guild: discord.Guild,
             channel: discord.TextChannel = None,
             block_channel: discord.TextChannel = None,
             transformed_by: str = None,
             into: str = None,
             image_url: str = None,
             claim_user: str = None,
             eternal: int = None,
             prefix: str = None,
             suffix: str = None,
             big: int = None,
             small: int = None,
             hush: int = None,
             censor: str = None,
             censor_replacement: str = None,
             sprinkle: str = None,
             muffle: str = None,
             chance: int = None,
             mod_type: str = None,
             bio: str = None) -> None:
    data = load_tf(user)
    if data == {}:  # If the file is empty, we need to add the version info
        data['version'] = CURRENT_TFEE_DATA_VERSION
    elif data['version'] != CURRENT_TFEE_DATA_VERSION:
        if CLEAR_OLD_TFEE_DATA:
            data = {}  # Clear data
        data['version'] = CURRENT_TFEE_DATA_VERSION
    channel_id = 'all' if channel is None else str(channel.id)
    if into not in ["", None]:
        if str(guild.id) not in data:
            data[str(guild.id)] = {}
        if channel_id not in data[str(guild.id)]:
            data[str(guild.id)]['blocked_channels'] = []
            data[str(guild.id)][channel_id] = {
                'transformed_by': transformed_by,
                'into': into,
                'image_url': image_url,
                'claim': None,
                'eternal': False,
                'prefix': {
                    'active': False,
                    'contents': [],
                    'chance': 0
                },
                'suffix': {
                    'active': False,
                    'contents': [],
                    'chance': 0
                },
                'big': False,
                'small': False,
                'hush': False,
                'censor': {
                    'active': False,
                    'contents': {}
                },
                'sprinkle': {
                    'active': False,
                    'contents': [],
                    'chance': 0
                },
                'muffle': {
                    'active': False,
                    'contents': [],
                    'chance': 0
                },
                'bio': None
            }
        else:
            data[str(guild.id)][channel_id]['transformed_by'] = transformed_by
            data[str(guild.id)][channel_id]['into'] = into
            data[str(guild.id)][channel_id]['image_url'] = image_url
    else:
        if transformed_by is not None and transformed_by != "":
            data[str(guild.id)][channel_id]['transformed_by'] = transformed_by
        if image_url is not None and image_url != "":
            data[str(guild.id)][channel_id]['image_url'] = image_url
        data[str(guild.id)][channel_id]['claim'] = claim_user.strip() if claim_user is not None and claim_user != "" \
            else None
        if eternal is not None:
            data[str(guild.id)][channel_id]['eternal'] = False if eternal == 0 else True
        if block_channel is not None:
            if str(block_channel.id) not in data[str(guild.id)]['blocked_channels']:
                data[str(guild.id)]['blocked_channels'].append(str(block_channel.id))
            else:
                data[str(guild.id)]['blocked_channels'].remove(str(block_channel.id))
        if prefix is not None:
            data[str(guild.id)][channel_id]['prefix']['active'] = True if prefix != "" else False
            data[str(guild.id)][channel_id]['prefix']['contents'] += [prefix.strip()] if prefix != "" else []
            data[str(guild.id)][channel_id]['prefix']['chance'] = 100 if prefix != "" else 0
        if suffix is not None:
            data[str(guild.id)][channel_id]['suffix']['active'] = True if suffix != "" else False
            data[str(guild.id)][channel_id]['suffix']['contents'] += [suffix.strip()] if suffix != "" else []
            data[str(guild.id)][channel_id]['suffix']['chance'] = 100 if suffix != "" else 0
        if big is not None:
            data[str(guild.id)][channel_id]['big'] = False if big == 0 else True
        if small is not None:
            data[str(guild.id)][channel_id]['small'] = False if small == 0 else True
        if hush is not None:
            data[str(guild.id)][channel_id]['hush'] = False if hush == 0 else True
        if censor is not None:
            data[str(guild.id)][channel_id]['censor']['active'] = True if censor != "" else False
            if censor != "":
                if censor_replacement is not None and censor_replacement != "":
                    if data[str(guild.id)][channel_id]['censor']['contents'] is None:
                        data[str(guild.id)][channel_id]['censor']['contents'] = {}
                    data[str(guild.id)][channel_id]['censor']['contents'][censor.strip().lower()] = \
                        censor_replacement.strip()
        if sprinkle is not None:
            data[str(guild.id)][channel_id]['sprinkle']['active'] = True if sprinkle != "" else False
            data[str(guild.id)][channel_id]['sprinkle']['contents'] += [sprinkle.strip()] if sprinkle != "" else []
            data[str(guild.id)][channel_id]['sprinkle']['chance'] = 30 if sprinkle != "" else 0
        if muffle is not None:
            data[str(guild.id)][channel_id]['muffle']['active'] = True if muffle != "" else False
            data[str(guild.id)][channel_id]['muffle']['contents'] += [muffle.strip()] if muffle != "" else []
            data[str(guild.id)][channel_id]['muffle']['chance'] = 30 if muffle != "" else 0
        if mod_type is not None and chance and mod_type in ['prefix', 'suffix', 'sprinkle', 'muffle']:
            data[str(guild.id)][channel_id][mod_type]['chance'] = chance
        if bio is not None:
            data[str(guild.id)][channel_id]['bio'] = None if bio == "" else bio
    with open(f"cache/people/{str(user.id)}.json", "w+") as f:
        f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.


def remove_tf(user: discord.User, guild: discord.Guild, channel: discord.TextChannel = None) -> None:
    data = load_tf(user)
    if not str(guild.id) in data or \
            (channel is not None and not str(channel.id) in data[str(guild.id)]) or \
            (channel is None and "all" not in data[str(guild.id)]):
        return
    if channel is None:
        del data[str(guild.id)]["all"]
    else:
        del data[str(guild.id)][str(channel.id)]
    with open(f"cache/people/{str(user.id)}.json", "w+") as f:
        f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.


def remove_all_tf(user: discord.User) -> None:
    os.remove(f"cache/people/{str(user.id)}.json")


# TRANSFORMED DATA UTILS
def load_transformed(guild: discord.Guild = None) -> dict:
    if "transformed.json" not in os.listdir("cache"):
        return {}
    with open("cache/transformed.json", "r") as f:
        contents = f.read()
        if contents == "":
            return {}
        data = json.loads(contents)
        if guild is None:
            return data
        else:
            if str(guild.id) in data:
                return data[str(guild.id)]
            return {}


def write_transformed(guild: discord.Guild,
                      user: discord.User = None,
                      channel: discord.TextChannel = None,
                      block_channel: discord.TextChannel = None,
                      block_user: discord.User = None) -> None:
    data = load_transformed()
    if data == {}:  # If the file is empty, we need to add the version info
        data['version'] = CURRENT_TRANSFORMED_DATA_VERSION
    if data['version'] != CURRENT_TRANSFORMED_DATA_VERSION:
        if CLEAR_OLD_TRANSFORMED_DATA:
            data = {}
        data['version'] = CURRENT_TRANSFORMED_DATA_VERSION
    if str(guild.id) not in data:
        data[str(guild.id)] = {
            'blocked_users': [],
            'blocked_channels': [],
            'transformed_users': {}
        }
    if user is not None:
        if str(user.id) not in data[str(guild.id)]['transformed_users']:
            data[str(guild.id)]['transformed_users'][str(user.id)] = []
        if channel is None:
            data[str(guild.id)]['transformed_users'][str(user.id)].append('all')
        else:
            data[str(guild.id)]['transformed_users'][str(user.id)].append(str(channel.id))
    if block_channel is not None:
        if str(block_channel.id) not in data[str(guild.id)]['blocked_channels']:
            data[str(guild.id)]['blocked_channels'].append(str(block_channel.id))
        else:
            data[str(guild.id)]['blocked_channels'].remove(str(block_channel.id))
    if block_user is not None:
        if str(block_user.id) not in data[str(guild.id)]['blocked_users']:
            data[str(guild.id)]['blocked_users'].append(str(block_user.id))
        else:
            data[str(guild.id)]['blocked_users'].remove(str(block_user.id))
    with open("cache/transformed.json", "w+") as f:
        f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.


def remove_transformed(user: discord.User, guild: discord.Guild, channel: discord.TextChannel) -> None:
    data = load_transformed()
    data[str(guild.id)]['transformed_users'][str(user.id)].remove(str(channel.id) if channel is not None else 'all')
    with open("cache/transformed.json", "w+") as f:
        f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.


def is_transformed(user: discord.User, guild: discord.Guild) -> bool:
    tfee_data = load_transformed(guild)
    if tfee_data == {}:
        return False
    return tfee_data['transformed_users'][str(user.id)] not in [{}, None] \
        if str(user.id) in tfee_data['transformed_users'] else False


# TEXT UTILS
# Apply all necessary modifications to the message, based on the user's transformation data
def transform_text(data: dict, original: str) -> str:
    # Ignore italics messsages
    if (original.startswith("*") and original.endswith("*")) or \
            (original.startswith("_") and original.endswith("_")):
        return original

    transformed = original
    words = transformed.split(" ")

    if data["censor"]["active"]:
        # Ignore italic messages
        # Censor will change the censored word to the word provided in the data
        for i in range(len(words)):
            # Force lowercase and strip punctuation
            word = words[i].lower().strip("*.,!?")
            if word in data["censor"]["contents"].keys():
                to_be = words[i].lower()
                words[i] = to_be.replace(word, data["censor"]["contents"][word])

        transformed = " ".join(words)

    if data["muffle"]["active"]:
        # Muffle will overwrite a word with a word from the data array by random chance
        for i in range(len(words)):
            if random.randint(1, 100) <= data["muffle"]["chance"]:
                words[i] = data["muffle"]["contents"][random.randint(0, len(data["muffle"]["contents"]) - 1)]

        transformed = " ".join(words)

    if data["sprinkle"]["active"]:
        # Sprinkle will add the sprinkled word to the message between words by random chance
        # for each word, if the chance is met, add a sprinkled word before it
        length = len(words)
        for i in range(length):
            if random.randint(1, 100) <= data["sprinkle"]["chance"]:
                words[i] = data["sprinkle"]["contents"][
                               random.randint(0, len(data["sprinkle"]["contents"]) - 1)] + " " + words[i]
        transformed = " ".join(words)

    # Moving these below so text changes are applied before the prefix and suffix so they aren't affected
    # by censors or such
    if data["prefix"]["active"]:
        # Prefix will add the prefix to the message, try the chance of adding it,
        # and then select a random prefix from the list
        if (0 <= data["prefix"]["chance"] < 100 and random.randint(1, 100) <= data["prefix"]["chance"]) or \
                data["prefix"]["chance"] >= 100:
            transformed = data["prefix"]["contents"][
                              random.randint(0, len(data["prefix"]["contents"]) - 1)] + " " + transformed

    if data["suffix"]["active"]:
        # Suffix will add the suffix to the message, try the chance of adding it,
        # and then select a random suffix from the list
        if (0 <= data["suffix"]["chance"] < 100 and random.randint(1, 100) <= data["suffix"]["chance"]) or \
                data["suffix"]["chance"] >= 100:
            transformed = transformed + " " + data["suffix"]["contents"][
                random.randint(0, len(data["suffix"]["contents"]) - 1)]

    if data["big"]:
        transformed = "# " + transformed

    if data["small"]:
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        tiny_alphabet = "ᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻ"
        for i in range(26):  # 26 letters in alphabet
            transformed = transformed.lower().replace(alphabet[i], tiny_alphabet[i])

    if data["hush"]:
        transformed = "||" + transformed + "||"

    return transformed


# ABSTRACTION FUNCTIONS
async def extract_tf_data(ctx: discord.ApplicationContext,
                          user: discord.User, get_command: bool = False) -> [bool, dict, discord.User]:
    if user is None:
        user = ctx.author
    if not is_transformed(user, ctx.guild):
        await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
        return [False, None, None]
    data = load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if not get_command and data['claim'] is not None and data['claim'] != ctx.author.name:
        await ctx.respond(f"You can't do that! {user.mention} is owned by {data['claim']}, and not by you!")
        return [False, None, None]
    return [True, data, user]


# MISCELLANEOUS UTILS
def get_webhook_by_name(webhooks, name) -> discord.Webhook or None:
    for wh in webhooks:
        if wh.name == name:
            return wh
    return


def get_embed_base(title: str, desc: str = None) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=desc,
        color=discord.Color.blue(),
        author=discord.EmbedAuthor(
            name="TransforMate",
            icon_url="https://cdn.discordapp.com/avatars/967123840587141181/46a629c191f53ec9d446ed4b712fb39b.png"
        )
    )

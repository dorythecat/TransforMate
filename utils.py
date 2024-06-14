import json
import os
import random

import discord

# DATA VERSIONS
# REMEMBER TO REGENERATE ALL TRANSFORMATION DATA IF YOU CHANGE THE VERSION
# VERSION 5: Fixing the fields to accept multiple values as well as a percentage chance for each field.
# VERSION 4: Reworked to work with per-channel data. - DROPPED SUPPORT FOR TRANSLATING PREVIOUS VERSIONS
# VERSION 3: Added "big", "small", and "hush" fields, and changed "eternal" from bool to int
# VERSION 2: Added guild specific data
# VERSION 1: Base version
CURRENT_TFEE_DATA_VERSION = 5

# VERSION 1: Base version
CURRENT_TRANSFORMED_DATA_VERSION = 1


# USER TRANSFORMATION DATA UTILS
def load_tf_by_name(name: str, guild: discord.Guild = None) -> dict:
    if f"{name}.json" not in os.listdir("cache/people"):
        return {}
    with open(f"cache/people/{name}.json", "r") as f:
        contents = f.read()
        if contents.strip() == "":
            return {}
        if guild is None:
            return json.loads(contents)
        else:
            data = json.loads(contents)
            if str(guild.id) in data:
                return data[str(guild.id)]
            return {}


def load_tf(user: discord.User, guild: discord.Guild = None) -> dict:
    return load_tf_by_name(user.name, guild)


def write_tf(user: discord.User,
             guild: discord.Guild,
             channel: discord.TextChannel = None,
             transformed_by: str = None,
             into: str = None,
             image_url: str = None,
             claim_user: str = None,
             eternal: int = None,
             prefix_bool: bool = False,
             prefix: str = None,
             suffix_bool: bool = False,
             suffix: str = None,
             big: int = None,
             small: int = None,
             hush: int = None,
             censor_bool: bool = False,
             censor: str = None,
             censor_replacement: str = None,
             sprinkle_bool: bool = False,
             sprinkle: str = None,
             muffle_bool: bool = False,
             muffle: str = None,
             chance: int = None,
             type: int = None,
             clear_contents: bool = None) -> None:
    data = load_tf(user)
    if data == {}:  # If the file is empty, we need to add the version info
        data['version'] = CURRENT_TFEE_DATA_VERSION
    elif data['version'] != CURRENT_TFEE_DATA_VERSION:
        print("Data loaded is from older versions! Beware of monsters!") # Debug message, remove for production
        data['version'] = CURRENT_TFEE_DATA_VERSION
    channel_id = 'all' if channel is None else str(channel.id)
    if into not in ["", None]:
        if str(guild.id) not in data:
            data[str(guild.id)] = {}
        if channel_id not in data[str(guild.id)]:
            data[str(guild.id)][channel_id] = {
                'transformed_by': "",
                'into': "",
                'image_url': "",
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
                }
            }
        if into not in ["", None]:
            if into not in ["", None]:
                data[str(guild.id)][channel_id] = {  # Add guild specific data
                    'transformed_by': transformed_by,
                    'into': into,
                    'image_url': image_url,
                    'claim': data[str(guild.id)][channel_id]['claim'],
                    'eternal': data[str(guild.id)][channel_id]['eternal'],
                    'prefix': {
                        'active': data[str(guild.id)][channel_id]['prefix']['active'],
                        'contents': data[str(guild.id)][channel_id]['prefix']['contents'],
                        'chance': data[str(guild.id)][channel_id]['prefix']['chance']
                    },
                    'suffix': {
                        'active': data[str(guild.id)][channel_id]['suffix']['active'],
                        'contents': data[str(guild.id)][channel_id]['suffix']['contents'],
                        'chance': data[str(guild.id)][channel_id]['suffix']['chance']
                    },
                    'big': data[str(guild.id)][channel_id]['big'],
                    'small': data[str(guild.id)][channel_id]['small'],
                    'hush': data[str(guild.id)][channel_id]['hush'],
                    'censor': {
                        'active': data[str(guild.id)][channel_id]['censor']['active'],
                        'contents': data[str(guild.id)][channel_id]['censor']['contents']
                    },
                    'sprinkle': {
                        'active': data[str(guild.id)][channel_id]['sprinkle']['active'],
                        'contents': data[str(guild.id)][channel_id]['sprinkle']['contents'],
                        'chance': data[str(guild.id)][channel_id]['sprinkle']['chance']
                    },
                    'muffle': {
                        'active': data[str(guild.id)][channel_id]['muffle']['active'],
                        'contents': data[str(guild.id)][channel_id]['muffle']['contents'],
                        'chance': data[str(guild.id)][channel_id]['muffle']['chance']
                    }
                }
            else:
                data[str(guild.id)][channel_id] = {  # Add guild specific data
                    'transformed_by': transformed_by,
                    'into': into,
                    'image_url': image_url,
                    'claim': claim_user,
                    'eternal': False if eternal is None or eternal == 0 else True,
                    'prefix': {
                        'active': False if prefix_bool is None or prefix_bool == 0 else True,
                        'contents': prefix,
                        'chance': 0
                    },
                    'suffix': {
                        'active': False if suffix_bool is None or suffix_bool == 0 else True,
                        'contents': suffix,
                        'chance': 0
                    },
                    'big': False if big is None or big == 0 else True,
                    'small': False if small is None or small == 0 else True,
                    'hush': False if hush is None or hush == 0 else True,
                    'censor': {
                        'active': censor_bool,
                        'contents': {}
                    },
                    'sprinkle': {
                        'active': sprinkle_bool,
                        'contents': sprinkle,
                        'chance': 0
                    },
                    'muffle': {
                        'active': muffle_bool,
                        'contents': muffle,
                        'chance': 0
                    }
                }
    else:
        if transformed_by is not None and transformed_by != "":
            data[str(guild.id)][channel_id]['transformed_by'] = transformed_by
        if image_url is not None and image_url != "":
            data[str(guild.id)][channel_id]['image_url'] = image_url
        if claim_user is not None and claim_user != "":
            data[str(guild.id)][channel_id]['claim'] = claim_user.strip()
        elif claim_user == "":
            data[str(guild.id)][channel_id]['claim'] = None
        if eternal is not None:
            if eternal == 0:
                data[str(guild.id)][channel_id]['eternal'] = False
            else:
                data[str(guild.id)][channel_id]['eternal'] = True
        if prefix is not None:
            if prefix != "":
                data[str(guild.id)][channel_id]['prefix']['active'] = True
                data[str(guild.id)][channel_id]['prefix']['contents'] = data[str(guild.id)][channel_id]['prefix'][
                                                                            'contents'] + [prefix.strip()]
                data[str(guild.id)][channel_id]['prefix']['chance'] = 30
            else:
                data[str(guild.id)][channel_id]['prefix']['active'] = False
                data[str(guild.id)][channel_id]['prefix']['chance'] = 0
        if suffix is not None:
            if suffix != "":
                data[str(guild.id)][channel_id]['suffix']['active'] = True
                data[str(guild.id)][channel_id]['suffix']['contents'] = data[str(guild.id)][channel_id]['suffix'][
                                                                            'contents'] + [suffix.strip()]
                data[str(guild.id)][channel_id]['suffix']['chance'] = 30
            else:
                data[str(guild.id)][channel_id]['suffix']['active'] = False
                data[str(guild.id)][channel_id]['suffix']['chance'] = 0
        if big is not None:
            if big == 0:
                data[str(guild.id)][channel_id]['big'] = False
            else:
                data[str(guild.id)][channel_id]['big'] = True
        if small is not None:
            if small == 0:
                data[str(guild.id)][channel_id]['small'] = False
            else:
                data[str(guild.id)][channel_id]['small'] = True
        if hush is not None:
            if hush == 0:
                data[str(guild.id)][channel_id]['hush'] = False
            else:
                data[str(guild.id)][channel_id]['hush'] = True
        if censor is not None:
            if censor != "":
                data[str(guild.id)][channel_id]['censor']['active'] = True
                if censor_replacement is not None and censor_replacement != "":
                    if data[str(guild.id)][channel_id]['censor']['contents'] is None:
                        data[str(guild.id)][channel_id]['censor']['contents'] = {}
                    data[str(guild.id)][channel_id]['censor']['contents'][
                        censor.strip().lower()] = censor_replacement.strip()
            else:
                data[str(guild.id)][channel_id]['censor']['active'] = False
        if sprinkle is not None:
            if sprinkle != "":
                data[str(guild.id)][channel_id]['sprinkle']['active'] = True
                data[str(guild.id)][channel_id]['sprinkle']['contents'] = data[str(guild.id)][channel_id]['sprinkle'][
                                                                              'contents'] + [sprinkle.strip()]
                data[str(guild.id)][channel_id]['sprinkle']['chance'] = 30
            else:
                data[str(guild.id)][channel_id]['sprinkle']['active'] = False
                data[str(guild.id)][channel_id]['sprinkle']['chance'] = 0
        if muffle is not None:
            if muffle != "":
                data[str(guild.id)][channel_id]['muffle']['active'] = True
                data[str(guild.id)][channel_id]['muffle']['contents'] = data[str(guild.id)][channel_id]['muffle'][
                                                                            'contents'] + [muffle.strip()]
                data[str(guild.id)][channel_id]['muffle']['chance'] = 30
            else:
                data[str(guild.id)][channel_id]['muffle']['active'] = False
                data[str(guild.id)][channel_id]['muffle']['chance'] = 0
        if type and chance is not None:
            if type in ['prefix', 'suffix', 'sprinkle', 'muffle']:
                data[str(guild.id)][channel_id][type]['chance'] = chance
        if clear_contents is not None:
            data[str(guild.id)][channel_id]['prefix']['contents'] = []
            data[str(guild.id)][channel_id]['suffix']['contents'] = []
            data[str(guild.id)][channel_id]['sprinkle']['contents'] = []
            data[str(guild.id)][channel_id]['muffle']['contents'] = []
            data[str(guild.id)][channel_id]['censor']['contents'] = {}
    with open(f"cache/people/{user.name}.json", "w+") as f:
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
    with open(f"cache/people/{user.name}.json", "w+") as f:
        f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.


def remove_all_tf(user: discord.User) -> None:
    os.remove(f"cache/people/{user.name}.json")


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


def write_transformed(user: discord.User, guild: discord.Guild) -> None:
    data = load_transformed()
    if data == {}:  # If the file is empty, we need to add the version info
        data["version"] = CURRENT_TRANSFORMED_DATA_VERSION
    if str(guild.id) not in data:
        data[str(guild.id)] = []
    if user.name not in data[str(guild.id)]:
        data[str(guild.id)].append(user.name)
    with open("cache/transformed.json", "w+") as f:
        f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.


def remove_transformed(user: discord.User, guild: discord.Guild) -> None:
    data = load_transformed()
    data[str(guild.id)].remove(user.name)
    with open("cache/transformed.json", "w+") as f:
        f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.


def is_transformed(user: discord.User, guild: discord.Guild) -> bool: return user.name in load_transformed(guild)


# TEXT UTILS
# Apply all necessary modifications to the message, based on the user's transformation data
def transform_text(data: dict, original: str) -> str:
    transformed = original

    words = transformed.split(" ")
    if data["censor"]["active"]:
        # Censor will change the censored word to the word provided in the data
        words = transformed.split(" ")
        # force lowercase for comparison
        # also strip punctuation
        word = words[0].lower().strip(".,!?")
        for i in range(len(words)):
            if word in data["censor"]["contents"]:
                words[i] = data["censor"]["contents"][words[i].lower()]
        transformed = " ".join(words)
    
    if data["muffle"]["active"]:
        # Muffle will overwrite a word with a word from the data array by random chance
        for i in range(len(words)):
            if random.randint(1, 100) <= data["muffle"]["chance"]:
                words[i] = data["muffle"]["contents"][random.randint(0, len(data["muffle"]["contents"]) - 1)]


        transformed = " ".join(words)
    if data["sprinkle"]["active"]:
        # Sprinkle will add the sprinkled word to the message between words by random chance
        words = transformed.split(" ")
        # for each word, if the chance is met, add a sprinkled word before it
        length = len(words)
        for i in range(length):
            if random.randint(1, 100) <= data["sprinkle"]["chance"]:
                words[i] = data["sprinkle"]["contents"][random.randint(0, len(data["sprinkle"]["contents"]) - 1)] + " " + words[i]
        transformed = " ".join(words) 
        # Moving these below so text changes are applied before the prefix and suffix so they aren't affected by censors or such
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
        for i in range(len(alphabet)):
            transformed = transformed.lower().replace(alphabet[i], tiny_alphabet[i])
    if data["hush"]:
        transformed = "||" + transformed + "||"

    return transformed


# MISCELLANEOUS UTILS
def get_webhook_by_name(webhooks, name) -> discord.Webhook or None:
    for wh in webhooks:
        if wh.name == name:
            return wh
    return None

# Obfuscate Overly Repetitive Code
async def logic_command(ctx: discord.ApplicationContext,
                  user: discord.User,
):
    if user is None:
        user = ctx.author
    transformed = load_transformed(ctx.guild)
    if user.name not in transformed:
        return [await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!"), data, user]
    data = load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    return [True, data, user]

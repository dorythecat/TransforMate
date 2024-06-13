import json
import os

import discord

# DATA VERSIONS
# REMEMBER TO REGENERATE ALL TRANSFORMATION DATA IF YOU CHANGE THE VERSION
# VERSION 4: Reworked to work with per-channel data. - DROPPED SUPPORT FOR TRANSLATING PREVIOUS VERSIONS
# VERSION 3: Added "big", "small", and "hush" fields, and changed "eternal" from bool to int
# VERSION 2: Added guild specific data
# VERSION 1: Base version
CURRENT_TFEE_DATA_VERSION = 4

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
             prefix: str = None,
             suffix: str = None,
             big: int = None,
             small: int = None,
             hush: int = None,
             censor_bool: bool = False,
             censor: str = None,
             sprinkle_bool: bool = False,
             sprinkle: str = None,
             muffle_bool: bool = False,
             muffle: str = None) -> None:
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
            data[str(guild.id)][channel_id] = {}
        data[str(guild.id)][channel_id] = {  # Add guild specific data
            'transformed_by': transformed_by,
            'into': into,
            'image_url': image_url,
            'claim': claim_user,
            'eternal': False if eternal is None or eternal == 0 else True,
            'prefix': prefix,
            'suffix': suffix,
            'big': False if big is None or big == 0 else True,
            'small': False if small is None or small == 0 else True,
            'hush': False if hush is None or hush == 0 else True,
            'censor': {
                'active': censor_bool,
                'contents': censor
            },
            'sprinkle': {
                'active': sprinkle_bool,
                'contents': sprinkle
            },
            'muffle': {
                'active': muffle_bool,
                'contents': muffle
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
                data[str(guild.id)][channel_id]['prefix'] = prefix
            else:
                data[str(guild.id)][channel_id]['prefix'] = None
        if suffix is not None:
            if suffix != "":
                data[str(guild.id)][channel_id]['suffix'] = suffix
            else:
                data[str(guild.id)][channel_id]['suffix'] = None
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
                data[str(guild.id)][channel_id]['censor']['contents'] = censor.strip()
            else:
                data[str(guild.id)][channel_id]['censor']['active'] = False
                data[str(guild.id)][channel_id]['censor']['contents'] = None
        if sprinkle is not None:
            if sprinkle != "":
                data[str(guild.id)][channel_id]['sprinkle']['active'] = True
                data[str(guild.id)][channel_id]['sprinkle']['contents'] = sprinkle.strip()
            else:
                data[str(guild.id)][channel_id]['sprinkle']['active'] = False
                data[str(guild.id)][channel_id]['sprinkle']['contents'] = None
        if muffle is not None:
            if muffle != "":
                data[str(guild.id)][channel_id]['muffle']['active'] = True
                data[str(guild.id)][channel_id]['muffle']['contents'] = muffle.strip()
            else:
                data[str(guild.id)][channel_id]['muffle']['active'] = False
                data[str(guild.id)][channel_id]['muffle']['contents'] = None
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


def get_transformed(guild: discord.Guild) -> dict: return load_transformed(guild)


# TEXT UTILS
# Apply all necessary modifications to the message, based on the user's transformation data
def transform_text(data: dict, original: str) -> str:
    transformed = original
    if data["prefix"]:
        transformed = data["prefix"] + transformed
    if data["suffix"]:
        transformed = transformed + data["suffix"]
    if data["big"]:
        transformed = "# " + transformed
    if data["small"]:
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        tiny_alphabet = "ᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻ"
        for i in range(len(alphabet)):
            transformed = transformed.replace(alphabet[i], tiny_alphabet[i])
    if data["hush"]:
        transformed = "||" + transformed + "||"
    return transformed


# MISCELLANEOUS UTILS
def get_webhook_by_name(webhooks, name) -> discord.Webhook or None:
    for wh in webhooks:
        if wh.name == name:
            return wh
    return None

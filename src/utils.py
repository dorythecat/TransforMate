import json
import os
import random
import math
import re
import requests

from types import NoneType

import discord

from config import CACHE_PATH

# TODO: https://github.com/dorythecat/TransforMate/issues/40

# DATA VERSIONS
# REMEMBER TO REGENERATE (OR UPDATE) ALL TRANSFORMATION DATA IF YOU CHANGE THE VERSION
# VERSION 16: Removed "proxy_prefix" and "proxy_suffix" fields, removed "active" and "contents" subfields from modifiers, and removed per-channel data
# VERSION 15: Added individual chances to all modifiers - ADDENDUM 1: Made the "transformed_by" and "claim" fields be integers now
# VERSION 14: Added "stutter" field
# VERSION 13: Made "claim" field be an integer, instead of a string
# VERSION 12: Added compatibility for multiple characters, when in tupper-like mode (Added "index" field)
# VERSION 11: Added "proxy_prefix" and "proxy_suffix" fields
# VERSION 10: Added "alt_muffle" field
# VERSION 9: Added "blocked_users" field
# VERSION 8: Added "upside_down" and "backwards" fields
# VERSION 7: Added "bio" field
# VERSION 6: Added "blocked_channels" field
# VERSION 5: Fixing the fields to accept multiple values as well as a percentage chance for each field.
# VERSION 4: Reworked to work with per-channel data. - DROPPED SUPPORT FOR TRANSLATING PREVIOUS VERSIONS
# VERSION 3: Added "big", "small", and "hush" fields, and changed "eternal" from bool to int
# VERSION 2: Added guild-specific data
# VERSION 1: Base version
CURRENT_TMUD_VERSION = 16

# VERSION 10: Removed per-channel data
# VERSION 9: Removed "affixes" field
# VERSION 8: Added "images" field
# VERSION 7: Added compatibility with the new multi-character mode for TFee Data v12
# VERSION 6: Added "affixes" field
# VERSION 5: Added "logs" and "clear_other_logs" fields
# VERSION 4: Each user now stores the channels they're transformed on
# VERSION 3: Added "blocked_users" field
# VERSION 2: Added "blocked_channels" and "transformed_users" fields
# VERSION 1: Base version
CURRENT_TRANSFORMED_DATA_VERSION = 10


# USER TRANSFORMATION DATA UTILS
def load_tf(user: discord.User | discord.Member | int, guild: discord.Guild | int | None = None) -> dict:
    """
    Loads the TMUD data of a user. If the `guild` parameter is specified, it loads only that specific server's data.

    :param user: A Discord User or Member object, representing the user whose data is to be loaded.
    :param guild: A Discord Guild object, representing the server in which the user's data is to be loaded. If not specified, loads all the user's data.

    :return: A TMUD-compliant dictionary containing the user's TMUD data.
    """
    return load_file(f'{CACHE_PATH}/people/{str(user if type(user) is int else user.id)}.json',
                     guild if type(guild) in [int, NoneType] else guild.id)


def get_data_version(user: discord.User | discord.Member | int) -> int:
    """
    Gets the version of the TMUD data of a user.

    :param user: A Discord User or Member object, representing the user whose data is to be loaded.

    :return: An integer representing the version of the TMUD data of the user.
    """
    return int(load_file(f'{CACHE_PATH}/people/{str(user if type(user) is int else user.id)}.json')['version'])


def write_tf(user: discord.User | discord.Member | int,
             guild: discord.Guild | int,
             new_data: dict | None = None,
             block_channel: discord.TextChannel | int | None = None,
             block_user: discord.User | discord.Member | int | None = None,
             transformed_by: discord.User | discord.Member | int = None,
             into: str | None = None,
             image_url: str | None = None,
             claim_user: discord.User | discord.Member | int = None,
             eternal: bool | None = None,
             prefix: str | None = None,
             suffix: str | None = None,
             big: bool | None = None,
             small: bool | None = None,
             hush: bool | None = None,
             backwards: bool | None = None,
             censor: str | None = None,
             censor_replacement: str | None = None,
             sprinkle: str | None = None,
             muffle: str | None = None,
             alt_muffle: str | None = None,
             stutter: int | None = None,
             chance: float | None = None,
             bio: str | None = None) -> None:
    """
    This is a utility function with the unique purpose of modifying the TMUD-compliant transformation data of a given
    user, in a given server, in a given channel. It should automatically handle data creation and deletion, as well as
    updates to the TMUD version.

    Every Discord object (User, Member, Guild, and TextChannel) can also be inputted as an integer equaling the ID of
    said objects, and the function will automatically handle it.

    For inputting modifiers (prefix, suffix, sprinkle, muffle, alt_muffle) specify one modifier per function call, and
    remember to always include the chance parameter. In the case of censor, include always a censor_replacement.

    :param user: A Discord User or Member object, representing the user whose data is to be altered.
    :param guild: A Discord Guild object, representing the server in which the user's data is to be altered.
    :param new_data: A TMUD-compliant channel data string that will override any currently present data for the given parameters, without any extra checks from the function.
    :param block_channel: A Discord TextChannel object, representing a channel to block on the specified server.
    :param block_user: A Discord User or Member object, representing a user to block on the specified server.
    :param transformed_by: A Discord User or Member object, representing the user who is applying the transformation.
    :param into: The name of the transformation to apply.
    :param image_url: A valid image URL to use as the user's avatar.
    :param claim_user: A Discord User or Member object, representing the user who is claiming the transformation.
    :param eternal: A boolean indicating whether the transformation should be eternal.
    :param prefix: A string indicating the prefix to apply to the user's name.
    :param suffix: A string indicating the suffix to apply to the user's name.
    :param big: A boolean indicating whether the text the transformed user writes should be made big.
    :param small: A boolean indicating whether the text the transformed user writes should be made small.
    :param hush: A boolean indicating whether the text the transformed user writes should be hushed. (Discord censor)
    :param backwards: A boolean indicating whether the text the transformed user writes should be reversed.
    :param censor: A regex string to censor.
    :param censor_replacement: What to replace the censored text with.
    :param sprinkle: A string to sprinkle randomly throughout the transformed user's text.
    :param muffle: A string that will replace random words on the user's text.
    :param alt_muffle: A string that will replace random messages entirely.
    :param stutter: A value from 0 to 100 indicating the amount of stuttering to apply.
    :param chance: A value from 0 to 100 indicating the chance of the associated modifier being applied.
    :param bio: The biography of the transformed form. Can be used as general storage for strings, as per the TMUD standard.

    :return: This function does not return anything, but it will write the modified data to the cache file.
    """
    data = load_tf(user)
    user_id = str(user if type(user) is int else user.id)
    guild_id = str(guild if type(guild) is int else guild.id)
    if data == {} or data['version'] != CURRENT_TMUD_VERSION:
        if data != {}:
            for server in data:
                if server == 'version':
                    continue
                for channel in data[server]:
                    if channel in ['blocked_channels', 'blocked_users', 'all']:
                        continue
                    del data[server][channel]
                data[server] = data[server]['all']
                del data[server]['all']
                del data[server]['proxy_prefix']
                del data[server]['proxy_suffix']
                for modifier in ['prefix', 'suffix', 'censor', 'sprinkle', 'muffle']:
                    del data[server][modifier]['active']
                    data[server][modifier] = data[server][modifier]['contents']
                    del data[server]['contents']
        data['version'] = CURRENT_TMUD_VERSION
    if load_transformed(guild) == {}:
        write_transformed(guild)
    if new_data is not None:
        new_data['blocked_users'] = [] if 'blocked_users' not in new_data else new_data['blocked_users']
        new_data['blocked_channels'] = [] if 'blocked_channels' not in new_data else new_data['blocked_channels']
        data[guild_id] = new_data
        write_file(f'{CACHE_PATH}/people/{str(user_id)}.json', data)
        write_transformed(guild, user, block_user, block_channel)
        return
    if into not in ["", None]:
        if guild_id not in data:
            data[guild_id] = {}
        data[guild_id] = {
            'blocked_channels': [] if 'blocked_channels' not in data[guild_id] else data[guild_id]['blocked_channels'],
            'blocked_users': [] if 'blocked_users' not in data[guild_id] else data[guild_id]['blocked_users'],
            'transformed_by': transformed_by if type(transformed_by) is int else transformed_by.id,
            'into': into,
            'image_url': image_url,
            'claim': 0 if claim_user is None else (claim_user if type(claim_user) is int else claim_user.id),
            'eternal': eternal is not None and eternal,
            'prefix': {},
            'suffix': {},
            'big': big is not None and big,
            'small': small is not None and small,
            'hush': hush is not None and hush,
            'backwards': backwards is not None and backwards,
            'censor': {},
            'sprinkle': {},
            'muffle': {},
            'alt_muffle': {},
            'stutter': stutter,
            'bio': bio
        }
    else:
        if transformed_by is not None:
            data[guild_id]['transformed_by'] = transformed_by if type(transformed_by) is int else transformed_by.id
        if image_url is not None and image_url != "":
            data[guild_id]['image_url'] = image_url
        if claim_user is not None:
            data[guild_id]['claim'] = claim_user if type(claim_user) is int else claim_user.id
        if eternal is not None:
            data[guild_id]['eternal'] = eternal
        if block_channel is not None:
            block_channel = str(block_channel if type(block_channel) is int else block_channel.id)
            if block_channel not in data[guild_id]['blocked_channels']:
                data[guild_id]['blocked_channels'].append(block_channel)
            else:
                data[guild_id]['blocked_channels'].remove(block_channel)
        if block_user is not None:
            block_user = str(block_user if type(block_user) is int else block_user.id)
            if block_user not in data[guild_id]['blocked_users']:
                data[guild_id]['blocked_users'].append(block_user)
            else:
                data[guild_id]['blocked_users'].remove(block_user)
        if prefix is not None:
            if prefix != "":
                if prefix.startswith("$/-"):
                    data[guild_id]['prefix'].pop(prefix[3:])
                else:
                    data[guild_id]['prefix'][prefix] = chance if chance else 30
            else:
                data[guild_id]['prefix'] = {}
        if suffix is not None:
            if suffix != "":
                if suffix.startswith("$/-"):
                    data[guild_id]['suffix'].pop(suffix[3:])
                else:
                    data[guild_id]['suffix'][suffix] = chance if chance else 30
            else:
                data[guild_id]['suffix'] = {}
        if big is not None:
            data[guild_id]['big'] = big
        if small is not None:
            data[guild_id]['small'] = small
        if hush is not None:
            data[guild_id]['hush'] = hush
        if backwards is not None:
            data[guild_id]['backwards'] = backwards
        if censor is not None:
            if censor != "":
                if censor.startswith("$/-"):
                    data[guild_id]['censor'].pop(censor[3:])
                elif censor_replacement not in ["", None]:
                    if data[guild_id]['censor'] is None:
                        data[guild_id]['censor'] = {}
                    data[guild_id]['censor'][censor] = censor_replacement
            else:
                data[guild_id]['censor'] = {}
        if sprinkle is not None:
            if sprinkle != "":
                if sprinkle.startswith("$/-"):
                    data[guild_id]['sprinkle'].pop(sprinkle[3:])
                else:
                    data[guild_id]['sprinkle'][sprinkle] = chance if chance else 30
            else:
                data[guild_id]['sprinkle'] = {}
        if muffle is not None:
            if muffle != "":
                if muffle.startswith("$/-"):
                    data[guild_id]['muffle'].pop(muffle[3:])
                else:
                    data[guild_id]['muffle'][muffle] = chance if chance else 30
            else:
                data[guild_id]['muffle'] = {}
        if alt_muffle is not None:
            if alt_muffle != "":
                if alt_muffle.startswith("$/-"):
                    data[guild_id]['alt_muffle'].pop(alt_muffle[3:])
                else:
                    data[guild_id]['alt_muffle'][alt_muffle] = chance if chance else 30
            else:
                data[guild_id]['alt_muffle'] = {}

        if stutter is not None:
            data[guild_id]['stutter'] = stutter

        if bio is not None:
            data[guild_id]['bio'] = None if bio == "" else bio
    write_file(f'{CACHE_PATH}/people/{user_id}.json', data)


def remove_tf(user: discord.User | discord.Member | int,
              guild: discord.Guild | int) -> None:
    """
    Removes the transformation data for a user in a server.

    :param user: A Discord user or member object, representing the user whose data will be removed.
    :param guild: A Discord guild object, representing the server from which the data will be removed.

    :return: This function does not return anything.
    """

    data = load_tf(user)
    guild_id = str(guild if type(guild) is int else guild.id)
    if data == {} or not guild_id in data:
        return
    del data[guild_id]
    write_file(f'{CACHE_PATH}/people/{str(user if type(user) is int else user.id)}.json', data)
    remove_transformed(user, guild)


def remove_all_server_tf(user: discord.User | discord.Member | int,
                         guild: discord.Guild | int) -> None:
    """
    Removes all transformation data for a user in a server, including blocked channels and users.

    :param user: A Discord user or member object, representing the user whose data will be removed.
    :param guild: A Discord guild object, representing the server from which the data will be removed.

    :return: This function does not return anything.
    """
    data = load_tf(user)
    guild_id = str(guild if type(guild) is int else guild.id)
    if data == {} or not guild_id in data:
        return
    del data[guild_id]
    write_file(f'{CACHE_PATH}/people/{str(user if type(user) is int else user.id)}.json', data)
    remove_transformed(user, guild)


def remove_all_tf(user: discord.User | discord.Member | int) -> None:
    """
    Fully removes a user's data file from the system.

    :param user: A Discord user or member object, representing the user whose data will be removed.

    :return: This function does not return anything.
    """
    try:
        os.remove(f'{CACHE_PATH}/people/{str(user if type(user) is int else user.id)}.json')
    except OSError as e:
        print(f"Error removing file:\n{str(type(e))}: {e}")


# TRANSFORMED DATA UTILS
def load_transformed(guild: discord.Guild | int | None = None) -> dict:
    """
    Loads the transformation data for a server, or, optionally, the entire server data file, if a server is not specified.

    :param guild: A Discord guild object, representing the server whose data will be loaded.

    :return: A dictionary containing the transformation data for a server, or, optionally, the entire server data file.
    """
    return load_file(f'{CACHE_PATH}/transformed.json',
                     guild if type(guild) in [int, NoneType] else guild.id)


def write_transformed(guild: discord.Guild | int,
                      user: discord.User | discord.Member | int | None = None,
                      block_user: discord.User | discord.Member | int | None = None,
                      block_channel: discord.TextChannel | int | None = None,
                      logs: list[int | None] | None = None,
                      clear_other_logs: bool | None = None,
                      images: discord.TextChannel | int | None = None) -> dict:
    """
    Writes the transformation data for a user in a server, to the server data file. Also
    serves as a utility to write server settings to the file.

    :param guild: A Discord guild object, representing the server to which the data will be written.
    :param user: A Discord user or member object, representing the user whose data will be written.
    :param block_user: A Discord user or member object, representing a user to block in this server.
    :param block_channel: A Discord channel object, representing a channel to block in this server.
    :param logs: A list of four channels, which will become the logging channels, for, in order, edited messages, deleted messages, transformations, and claims.
    :param clear_other_logs: A boolean value indicating whether to clear logs from other bots.
    :param images: A Discord channel object, representing the image buffer channel.

    :return: The updated transformation data for the server.
    """
    data = load_transformed()
    if data == {} or ('version' in data and int(data['version']) != CURRENT_TRANSFORMED_DATA_VERSION):
        if 'version' in data and int(data['version']) == 7:
            for server in data:
                if server == 'version':
                    continue
                data[server]['images'] = None
            data['version'] = 8
        if 'version' in data and int(data['version']) == 8:
            for server in data:
                if server == 'version':
                    continue
                del data[server]['affixes']
            data['version'] = 9
        if 'version' in data and int(data['version']) == 9:
            for server in data:
                if server == 'version':
                    continue
                for user in data[server]['transformed_users']:
                    if data[server]['transformed_users'][user] in [[], None]:
                        del data[server]['transformed_users'][user]
                        continue
                    del data[server]['transformed_users'][user]
                    data[server]['transformed_users'][user] = True
        data['version'] = 10

    guild_id = str(guild if type(guild) is int else guild.id)
    if guild_id not in data:
        data[guild_id] = {
            'blocked_users': [],
            'blocked_channels': [],
            'logs': [None, None, None, None],
            'clear_other_logs': False,
            'transformed_users': {},
            'images': None
        }

    if user is not None:
        user_id = str(user if type(user) is int else user.id)
        if user_id not in data[guild_id]['transformed_users'] or not data[guild_id]['transformed_users'][user_id]:
            data[guild_id]['transformed_users'][user_id] = True

    if block_channel is not None:
        block_channel = str(block_channel if type(block_channel) is int else block_channel.id)
        if block_channel not in data[guild_id]['blocked_channels']:
            data[guild_id]['blocked_channels'].append(block_channel)
        else:
            data[guild_id]['blocked_channels'].remove(block_channel)

    if block_user is not None:
        block_user = str(block_user if type(block_user) is int else block_user.id)
        if block_user not in data[guild_id]['blocked_users']:
            data[guild_id]['blocked_users'].append(block_user)
        else:
            data[guild_id]['blocked_users'].remove(block_user)

    if logs is not None:
        data[guild_id]['logs'] = logs

    if clear_other_logs is not None:
        data[guild_id]['clear_other_logs'] = clear_other_logs

    if images is not None:
        data[guild_id]['images'] = images if type(images) is int else images.id

    write_file(f'{CACHE_PATH}/transformed.json', data)
    return data[guild_id]


def is_transformed(user: discord.User | discord.Member | int,
                   guild: discord.Guild | int) -> bool:
    """
    Check if a user is transformed in a server.

    :param user: A Discord user or member object, representing the user to check.
    :param guild: A Discord guild object, representing the server to check.

    :return: A boolean value indicating whether the user is transformed in the specified server.
    """
    data = load_transformed(guild)
    user_id = str(user if type(user) is int else user.id)
    if data == {} or user_id not in data['transformed_users']:
        return False
    return data['transformed_users'][user_id]


def remove_transformed(user: discord.User | discord.Member | int,
                       guild: discord.Guild | int) -> None:
    """
    Removes a user from the transformation data for a server.

    :param user: A Discord user or member object, representing the user to remove.
    :param guild: A Discord guild object, representing the server from which the user will be removed.

    :return: This function does not return anything.
    """
    data = load_transformed()
    if not is_transformed(user, guild):
        return
    guild_id = str(guild if type(guild) is int else guild.id)
    user_id = str(user if type(user) is int else user.id)
    data[guild_id]['transformed_users'][user_id] = False
    write_file(f'{CACHE_PATH}/transformed.json', data)


def remove_server_from_transformed(guild: discord.Guild | int) -> None:
    """
    Removes a server from the server data file.

    :param guild: A Discord guild object, representing the server to remove.

    :return: This function does not return anything.
    """
    data = load_transformed()
    del data[str(guild if type(guild) is int else guild.id)]
    write_file(f'{CACHE_PATH}/transformed.json', data)


# TEXT UTILS
# Apply all necessary modifications to the message, based on the user's transformation data
def transform_text(data: dict, original: str) -> str:
    # Ignore italics and bold messages
    if ((original.startswith("*") and original.endswith("*")) or
        (original.startswith("_") and original.endswith("_"))):
        return original

    if data['alt_muffle'] != {}:
        # Alternative Muffle will overwrite the entire message with a word from the data array from random chance
        # If we apply this one transformation, that's it. Only this one. That's why it's at the top.
        if original in data['alt_muffle']:
            return original

        for alt_muffle in data['alt_muffle']:
            if random.randint(0, 100) <= int(data['alt_muffle'][alt_muffle]):
                return alt_muffle

    transformed = clear_apple_marks(original)

    if data['censor'] != {}:
        for pattern in data['censor']:
            try:
                if pattern.startswith("-/") and re.search(pattern[2:], transformed):
                    transformed = re.sub(pattern[2:], data['censor'][pattern], transformed)
            except re.PatternError as e:
                return f"```REGEX ERROR with pattern {pattern[2:]}:\n{e}```"

    words = transformed.split(" ")
    for i in range(len(words)):
        # Censor will change a word for another, "censoring" it
        if data['censor'] != {}:
            word = ''.join(e for e in words[i] if e.isalnum()) # Removed special characters

            if word in data['censor']:
                words[i] = words[i].replace(word, data['censor'][word]) # We keep punctuation

            if words[i] in data['censor']:
                words[i] = data['censor'][words[i]] # The entire word should be replaced

            for pattern in data['censor']:
                try:
                    if pattern.startswith("/") and re.search(pattern[1:], words[i]):
                        words[i] = re.sub(pattern[1:], data['censor'][pattern], words[i])
                except re.PatternError as e:
                    return f"```REGEX ERROR with pattern {pattern[1:]}:\n{e}```"


        # Muffle will overwrite a word with a word from the data array by random chance
        if data['muffle'] != {}:
            if words[i].startswith("http"):
                continue

            muffles = list(data['muffle'].keys())
            random.shuffle(muffles)
            for muffle in muffles:
                if random.randint(0, 100) <= int(data['muffle'][muffle]):
                    words[i] = muffle

    # Sprinkle will add the sprinkled word to the message between words by random chance
    # for each word, if the chance is met, add a sprinkled word before it
    if data['sprinkle'] != {}:
        sprinkles = list(data['sprinkle'].keys())
        for i in range(len(words)):
            random.shuffle(sprinkles)
            for sprinkle in sprinkles:
                if random.randint(0, 100) <= int(data['sprinkle'][sprinkle]):
                    words[i] = sprinkle + " " + words[i]

    if data['stutter'] > 0:
        for i in range(len(words)):
            if words[i].startswith("http") or not words[i].isalnum() or words[i] in "0123456789":
                continue

            if random.randint(0, 100) <= int(data['stutter']):
                words[i] = words[i][:random.randint(1, 1 + math.floor(len(words[i]) * int(data['stutter']) / 200))] + "-" + words[i]
    transformed = " ".join(words)

    # Moving these below, so text changes are applied before the prefix and suffix so they aren't affected
    # by censors or such
    if data['prefix'] != {}:
        prefixes = list(data['prefix'].keys())
        random.shuffle(prefixes)
        for prefix in prefixes:
            if random.randint(0, 100) <= int(data['prefix'][prefix]):
                transformed = prefix + transformed

    if data['suffix'] != {}:
        suffixes = list(data['suffix'].keys())
        random.shuffle(suffixes)
        for suffix in suffixes:
            if random.randint(0, 100) <= int(data['suffix'][suffix]):
                transformed += suffix

    # We need to do this now to avoid https://github.com/dorythecat/TransforMate/issues/48
    if data['backwards']:
        transformed = transformed[::-1]

    if data['big']:
        transformed = "# " + transformed

    if data['small']:
        trans_table = str.maketrans("abcdefghijklmnopqrstuvwxyz.0123456789+-=()",
                                    "ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻ·⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")


        transformed_list = transformed.lower().translate(trans_table).splitlines()

        transformed = "\n"
        for text in transformed_list:
            if text.strip() == "":
                transformed += "\n"
                continue
            transformed += f"-# {text.strip()}\n"

        # Make sure mentions work appropriately
        mention_transformed = ""
        for word in transformed.split(" "):
            if word.startswith("<@"):
                word = word.translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789"))
            mention_transformed += word + " "
        transformed = mention_transformed.strip()

    if data['hush']:
        transformed = f"||{transformed}||"

    return transformed


# ABSTRACTION FUNCTIONS
async def extract_tf_data(ctx: discord.ApplicationContext,
                          user: discord.User | discord.Member | None,
                          get_command: bool = False) -> tuple[bool,
                                                              dict | None,
                                                              discord.User | discord.Member | None]:
    if user is None:
        user = ctx.author
    if not is_transformed(user, ctx.guild):
        await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
        return False, None, None
    data = load_tf(user, ctx.guild)
    if not get_command and data['claim'] != 0 and data['claim'] != ctx.author.id:
        await ctx.respond(f"You can't do that! {user.mention} is owned by"
                          f"{ctx.guild.get_member(data['claim']).mention}, and not by you!")
        return False, None, None
    return True, data, user


# FILE UTILS
def load_file(filename: str, guild_id: int | None = None) -> dict:
    try:
        with open(filename) as f:
            contents = f.read().strip()
    except OSError as e:
        print(f"Error loading file:\n{str(type(e))}: {e}")
        return {}
    if contents == "":
        return {}
    data = json.loads(contents)
    if guild_id is None:
        return data
    if str(guild_id) in data:
        return data[str(guild_id)]
    return {}


def write_file(filename: str, data: dict) -> None:
    try:
        with open(filename, "w+") as f:
            f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.
    except OSError as e:
        print(f"Error writing to file:\n{str(type(e))}: {e}")


# MISCELLANEOUS UTILS
async def get_webhook_by_name(channel: discord.TextChannel, name: str) -> discord.Webhook:
    """
    Helper to get (or create, if it doesn't exist) a webhook by name from a list of webhooks.

    :param channel: The Discord channel to get the webhook from.
    :param name: The name of the webhook to get.

    :return: The Discord webhook with the specified name.
    """
    return next((wh for wh in await channel.webhooks() if wh.name == name), await channel.create_webhook(name=name))


def get_embed_base(title: str,
                   desc: str | None = None,
                   footer_text: str | None = None,
                   color: discord.Color = discord.Color.blue()) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=desc,
        color=color,
        author=discord.EmbedAuthor(
            name="TransforMate",
            icon_url="https://cdn.discordapp.com/avatars/967123840587141181/46a629c191f53ec9d446ed4b712fb39b.png"
        ),
        footer=discord.EmbedFooter(text=footer_text if footer_text is not None else "TransforMate")
    )


def check_message(message: discord.Message) -> tuple[int | None, dict | None]:
    transformed_data = load_transformed(message.guild)['transformed_users']
    # Currently, we have to check over ALL transformed users
    for tfee in transformed_data:
        data = load_tf(int(tfee), message.guild)
        if data != {} and data['into'] == message.author.name:
            # TODO: Make it so that this function returns all currently tfed users with this tf name
            if transformed_data[tfee] not in [[], None]:
                return int(tfee), data
    return None, None


def clear_apple_marks(text: str) -> str:
    text = text.replace("’", "'")
    text = text.replace("“", "\"")
    return text.replace("”", "\"")

# TSF Utilities
# See https://dorythecat.github.io/TransforMate/commands/transformation/export_tf/#transformation-string-format
def encode_tsf(data: dict, version: int) -> str:
    """
    Encodes a TMUD-compliant transformation data dict into a TSF-compliant string.
    The latest version of the TSF standard (v1.1) is used for this operation.

    :param data: Properly encoded TMUD-compliant transformation data dict.
    :param version: The version of the TMUD standard to use. (Used at the moment only to check compatibility)

    :return: A TSF-compliant string.
    """
    if not version == 16:
        raise ValueError("encode_tsf() only supports TMUDv16!")

    def parse_mod(mod_data: dict) -> str:
        if mod_data == {}: return ";%"
        return ",%".join([f"{key}|%{str(value)}" for key, value in mod_data.items()]) + ";%"

    return ";%".join([
        "2.0",
        data['into'],
        data['image_url'],
        str(hex(int(data['big']) + 2 * int(data['small']) + 4 * int(data['hush']) + 8 * int(data['backwards'])))[2:],
        str(data['stutter']),
        str(data['bio']),
        parse_mod(data['prefix']),
        parse_mod(data['suffix']),
        parse_mod(data['sprinkle']),
        parse_mod(data['muffle']),
        parse_mod(data['alt_muffle']),
        parse_mod(data['censor'])
    ])

def decode_tsf(tsf_string: str) -> dict:
    """
    Decodes a TSF-compliant string into a TMUD-compliant dict of transformation data.

    :param tsf_string: A TSF-compliant string.

    :return: A TMUD-compliant transformation data dict.
    """
    if tsf_string[0] == "2": # v2.x
        tsf_data = tsf_string.split(";%")
        version = int(tsf_data[0].split(".")[1]) # Get the minor version
        if version != 0: # v2.0
            raise ValueError("decode_tsf() does not support that version, at this moment!")

        if len(tsf_data) != 12:
            raise ValueError("decode_tsf() expected 12 elements in the TSFv2.0 string, got " + str(len(tsf_data)))

        tsf_data = tsf_data[1:] # Remove the version identifier for easier handling

        boolean_number = int(tsf_data[2], 16)
        big = boolean_number & 1 != 0
        small = boolean_number & 2 != 0
        hush = boolean_number & 4 != 0
        backwards = boolean_number & 8 != 0

        # Generate basic data
        data = {
            'into': tsf_data[0],
            'image_url': tsf_data[1],
            'big': big,
            'small': small,
            'hush': hush,
            'backwards': backwards,
            'stutter': int(tsf_data[3]),
            'bio': tsf_data[4]
        }

        modifiers = ['prefix', 'suffix', 'sprinkle', 'muffle', 'alt_muffle', 'censor']
        for modifier in modifiers:
            data[modifier] = {}
            for mod in tsf_data[5 + modifiers.index(modifier)].split(",%"):
                if mod == "":
                    continue
                key, value = mod.split("|%")
                data[modifier][key] = int(value) if modifier != 'censor' else value

        return data

    sep = ";%"
    tsf_data = tsf_string.split(";%") # v1.2
    if tsf_string[:3] != "1;%": # v1.0 and v1.1
        tsf_data = tsf_string.split(";")
        sep = ";"

    version = int(tsf_data[0])
    if version != 15 and version != 1: # v1.0 and v1.x
        raise ValueError("decode_tsf() does not support that version, at this moment!")

    if version == 15 and len(tsf_data) != 23:
        raise ValueError("decode_tsf() expected 23 elements in the TSFv1.0 string, got " + str(len(tsf_data)))
    if version == 1 and len(tsf_data) != 20:
        raise ValueError("decode_tsf() expected 20 elements in the TSFv1.x string, got " + str(len(tsf_data)))

    tsf_data = tsf_data[1:] # Remove the version identifier for easier handling

    # Booleans
    boolean_number = int(tsf_data[2], 16)
    big = boolean_number & 1 != 0
    small = boolean_number & 2 != 0
    hush = boolean_number & 4 != 0
    backwards = boolean_number & 8 != 0
    next_index = 3

    if version == 15: # v1.0
        big = tsf_data[2] == "1"
        small = tsf_data[3] == "1"
        hush = tsf_data[4] == "1"
        backwards = tsf_data[5] == "1"
        next_index = 6

    # Generate basic data
    data = {
        'into': tsf_data[0],
        'image_url': tsf_data[1],
        'big': big,
        'small': small,
        'hush': hush,
        'backwards': backwards,
        'stutter': int(tsf_data[next_index]),
        'bio': tsf_data[next_index + 3]
    }

    modifiers = ['prefix', 'suffix', 'sprinkle', 'muffle', 'alt_muffle', 'censor']
    for modifier in modifiers:
        data[modifier] = {}
        modifier_data = tsf_data[next_index + 5 + modifiers.index(modifier) * 2].split("," if sep == ";" else ",%")
        for mod in modifier_data:
            if mod == "":
                continue
            key, value = mod.split("|" if sep == ";" else "|%")
            data[modifier][key] = int(value) if modifier != 'censor' else value

    return data


def check_url(url: str) -> str:
    """
    This function will check if a given URL is a valid HTTP address, and if it isn't, and it can be fixed, fixes it.

    :param url: The URL to check.

    :return: A string containing a usable URL, blank if the given URL is invalid and con't be automatically fixed.
    """
    if not re.match(r'(http(s)?://.)?(www\.)?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_+.~#?&/=]*)', url):
        return ""
    if "?" in url:
        url = url[:url.index("?")]
    if not url.startswith("http"): # Basic preliminary check
        return f"https://{url}" # Try HTTPS
    try: # Check that the url is reachable
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.status_code >= 400: # Try HTTP
            url = f"http://{url[8:]}"
            response = requests.head(url, allow_redirects=True, timeout=5)
            if response.status_code >= 400:
                return ""
        if not response.headers['Content-Type'].startswith("image/"):
            return ""
    except requests.RequestException:
        return ""
    return url

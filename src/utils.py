import json
import os
import random
import math
import re

from types import NoneType

import discord

from config import CACHE_PATH

# TODO: https://github.com/dorythecat/TransforMate/issues/31
# TODO: https://github.com/dorythecat/TransforMate/issues/40
# TODO: https://github.com/dorythecat/TransforMate/issues/52

# DATA VERSIONS
# REMEMBER TO REGENERATE (OR UPDATE) ALL TRANSFORMATION DATA IF YOU CHANGE THE VERSION
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
CURRENT_TMUD_VERSION = 15 # 15.1

# VERSION 8: Added "images" field
# VERSION 7: Added compatibility with the new multi-character mode for TFee Data v12
# VERSION 6: Added "affixes" field
# VERSION 5: Added "logs" and "clear_other_logs" fields
# VERSION 4: Each user now stores the channels they're transformed on
# VERSION 3: Added "blocked_users" field
# VERSION 2: Added "blocked_channels" and "transformed_users" fields
# VERSION 1: Base version
CURRENT_TRANSFORMED_DATA_VERSION = 8


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
             channel: discord.TextChannel | int | None = None,
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
             chance: int | None = None,
             proxy_prefix: str | None = None,
             proxy_suffix: str | None = None,
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
    :param channel: A Discord TextChannel object, representing the channel in which the user's data is to be altered. If not specified, will modify the data for the 'all' section of the TMUD data.
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
    :param censor: A string to censor.
    :param censor_replacement: What to replace the censored text with.
    :param sprinkle: A string to sprinkle randomly throughout the transformed user's text.
    :param muffle: A string that will replace random words on the user's text.
    :param alt_muffle: A string that will replace random messages entirely.
    :param stutter: A value from 0 to 100 indicating the amount of stuttering to apply.
    :param chance: A value from 0 to 100 indicating the chance of the associated modifier being applied.
    :param proxy_prefix: When in Tupper-like mode, this is the string that has to precede the user's text for the transformation to be applied.
    :param proxy_suffix: Same as proxy_prefix but has to follow the user's text instead.
    :param bio: The biography of the transformed form. Can be used as general storage for strings, as per the TMUD standard.

    :return: This function does not return anything, but it will write the modified data to the cache file.
    """

    data = load_tf(user)
    user_id = str(user if type(user) is int else user.id)
    guild_id = str(guild if type(guild) is int else guild.id)
    if data == {} or data['version'] != CURRENT_TMUD_VERSION:
        if data != {} and data['transformed_by']: # Translate from v15 to v15.1
            data['transformed_by'] = int(data['transformed_by'])
        data['version'] = CURRENT_TMUD_VERSION
    transformed_data = load_transformed(guild)
    if transformed_data == {}:
        # Write some blank data if there's nothing to read here, and then read it
        transformed_data = write_transformed(guild)
    if new_data is not None:
        new_data['blocked_users'] = [] if 'blocked_users' not in new_data else new_data['blocked_users']
        new_data['blocked_channels'] = [] if 'blocked_channels' not in new_data else new_data['blocked_channels']
        data[guild_id] = new_data
        write_file(f'{CACHE_PATH}/people/{str(user_id)}.json', data)
        write_transformed(guild, user, channel, block_user, block_channel)
        return
    if transformed_data['affixes']:
        channel_id = proxy_prefix + " " + proxy_suffix
    else:
        channel_id = 'all' if channel is None else str(channel if type(channel) is int else channel.id)
    if into not in ["", None]:
        if guild_id not in data:
            data[guild_id] = {}
            data[guild_id]['blocked_channels'] = []
            data[guild_id]['blocked_users'] = []
        data[guild_id][channel_id] = {
            'transformed_by': transformed_by if type(transformed_by) is int else transformed_by.id,
            'into': into,
            'image_url': image_url,
            'claim': 0 if claim_user is None else (claim_user if type(claim_user) is int else claim_user.id),
            'eternal': False if eternal is None else eternal,
            'prefix': {
                'active': False,
                'contents': {}
            },
            'suffix': {
                'active': False,
                'contents': {}
            },
            'big': False if big is None else big,
            'small': False if small is None else small,
            'hush': False if hush is None else hush,
            'backwards': False if backwards is None else backwards,
            'censor': {
                'active': False,
                'contents': {}
            },
            'sprinkle': {
                'active': False,
                'contents': {}
            },
            'muffle': {
                'active': False,
                'contents': {}
            },
            'alt_muffle': {
                'active': False,
                'contents': {}
            },
            'stutter': 0,
            'proxy_prefix': proxy_prefix,
            'proxy_suffix': proxy_suffix,
            'bio': None
        }
    else:
        if transformed_by is not None:
            data[guild_id][channel_id]['transformed_by'] = transformed_by if type(transformed_by) is int else transformed_by.id
        if image_url is not None and image_url != "":
            data[guild_id][channel_id]['image_url'] = image_url
        if claim_user is not None:
            data[guild_id][channel_id]['claim'] = claim_user if type(claim_user) is int else claim_user.id
        if eternal is not None:
            data[guild_id][channel_id]['eternal'] = eternal
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
            data[guild_id][channel_id]['prefix']['active'] = True if prefix != "" else False
            if prefix != "":
                if prefix.startswith("$/-"):
                    data[guild_id][channel_id]['prefix']['contents'].pop(prefix[3:])
                else:
                    data[guild_id][channel_id]['prefix']['contents'][prefix] = chance if chance else 30
            else:
                data[guild_id][channel_id]['prefix']['contents'] = {}
        if suffix is not None:
            data[guild_id][channel_id]['suffix']['active'] = True if suffix != "" else False
            if suffix != "":
                if suffix.startswith("$/-"):
                    data[guild_id][channel_id]['suffix']['contents'].pop(suffix[3:])
                else:
                    data[guild_id][channel_id]['suffix']['contents'][suffix] = chance if chance else 30
            else:
                data[guild_id][channel_id]['suffix']['contents'] = {}
        if big is not None:
            data[guild_id][channel_id]['big'] = big
        if small is not None:
            data[guild_id][channel_id]['small'] = small
        if hush is not None:
            data[guild_id][channel_id]['hush'] = hush
        if backwards is not None:
            data[guild_id][channel_id]['backwards'] = backwards
        if censor is not None:
            data[guild_id][channel_id]['censor']['active'] = True if censor != "" else False
            if censor != "":
                if censor.startswith("$/-"):
                    data[guild_id][channel_id]['censor']['contents'].pop(censor[3:])
                elif censor_replacement not in ["", None]:
                    if data[guild_id][channel_id]['censor']['contents'] is None:
                        data[guild_id][channel_id]['censor']['contents'] = {}
                    data[guild_id][channel_id]['censor']['contents'][censor.lower()] = \
                        censor_replacement.lower()
        if sprinkle is not None:
            data[guild_id][channel_id]['sprinkle']['active'] = True if sprinkle != "" else False
            if sprinkle != "":
                if sprinkle.startswith("$/-"):
                    data[guild_id][channel_id]['sprinkle']['contents'].pop(sprinkle[3:])
                else:
                    data[guild_id][channel_id]['sprinkle']['contents'][sprinkle] = chance if chance else 30
            else:
                data[guild_id][channel_id]['sprinkle']['contents'] = {}
        if muffle is not None:
            data[guild_id][channel_id]['muffle']['active'] = True if muffle != "" else False
            if muffle != "":
                if muffle.startswith("$/-"):
                    data[guild_id][channel_id]['muffle']['contents'].pop(muffle[3:])
                else:
                    data[guild_id][channel_id]['muffle']['contents'][muffle] = chance if chance else 30
            else:
                data[guild_id][channel_id]['muffle']['contents'] = {}
        if alt_muffle is not None:
            data[guild_id][channel_id]['alt_muffle']['active'] = True if alt_muffle != "" else False
            if alt_muffle != "":
                if alt_muffle.startswith("$/-"):
                    data[guild_id][channel_id]['alt_muffle']['contents'].pop(alt_muffle[3:])
                else:
                    data[guild_id][channel_id]['alt_muffle']['contents'][alt_muffle] = chance if chance else 30
            else:
                data[guild_id][channel_id]['alt_muffle']['contents'] = {}

        if stutter is not None:
            data[guild_id][channel_id]['stutter'] = stutter

        if proxy_prefix is not None:
            data[guild_id][channel_id]['proxy_prefix'] = None if proxy_prefix == "" else proxy_prefix
        if proxy_suffix is not None:
            data[guild_id][channel_id]['proxy_suffix'] = None if proxy_suffix == "" else proxy_suffix

        if bio is not None:
            data[guild_id][channel_id]['bio'] = None if bio == "" else bio
    write_file(f'{CACHE_PATH}/people/{user_id}.json', data)


def remove_tf(user: discord.User | discord.Member | int,
              guild: discord.Guild | int,
              channel: discord.TextChannel | int | None = None) -> None:
    """
    Removes the transformation data for a user in a server, and, optionally, a channel.

    :param user: A Discord user or member object, representing the user whose data will be removed.
    :param guild: A Discord guild object, representing the server from which the data will be removed.
    :param channel: A Discord channel object, representing the channel from which the data will be removed.

    :return: This function does not return anything.
    """

    data = load_tf(user)
    guild_id = str(guild if type(guild) is int else guild.id)
    if data == {} or not guild_id in data or \
            (channel is not None and not str(channel.id) in data[guild_id]) or \
            (channel is None and "all" not in data[guild_id]):
        return
    del data[guild_id]['all' if channel is None else str(channel if type(channel) is int else channel.id)]
    write_file(f'{CACHE_PATH}/people/{str(user if type(user) is int else user.id)}.json', data)

    remove_transformed(user, guild, channel)


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
        print("Error removing file:")
        print(f"{str(type(e))}: {e}")


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
                      channel: discord.TextChannel | int | None = None,
                      block_user: discord.User | discord.Member | int | None = None,
                      block_channel: discord.TextChannel | int | None = None,
                      logs: list[int | None] | None = None,
                      clear_other_logs: bool | None = None,
                      affixes: bool | None = None,
                      images: discord.TextChannel | int | None = None) -> dict:
    """
    Writes the transformation data for a user in a server, or, optionally, a channel, to the server data file. Also
    serves as a utility to write server settings to the file.

    :param guild: A Discord guild object, representing the server to which the data will be written.
    :param user: A Discord user or member object, representing the user whose data will be written.
    :param channel: A Discord channel object, representing the channel to which the data will be written.
    :param block_user: A Discord user or member object, representing a user to block in this server.
    :param block_channel: A Discord channel object, representing a channel to block in this server.
    :param logs: A list of four channels, which will become the logging channels, for, in order, edited messages, deleted messages, transformations, and claims.
    :param clear_other_logs: A boolean value indicating whether to clear logs from other bots.
    :param affixes: A boolean value indicating whether to put the bot in affixes (Tupper-like) mode.
    :param images: A Discord channel object, representing the image buffer channel.

    :return: The updated transformation data for the server.
    """

    data = load_transformed()
    if data == {} or int(data['version']) != CURRENT_TRANSFORMED_DATA_VERSION:
        if int(data['version']) == 7:
            for server in data:
                if server == 'version':
                    continue
                data[server]['images'] = None
        data['version'] = CURRENT_TRANSFORMED_DATA_VERSION

    guild_id = str(guild if type(guild) is int else guild.id)
    if guild_id not in data:
        data[guild_id] = {
            'blocked_users': [],
            'blocked_channels': [],
            'logs': [None, None, None, None],
            'clear_other_logs': False,
            'affixes': False,
            'transformed_users': {},
            'images': None
        }

    if user is not None:
        user_id = str(user if type(user) is int else user.id)
        channel_id = str(channel if type(channel) in int else channel.id) if channel else 'all'
        if user_id not in data[guild_id]['transformed_users']:
            data[guild_id]['transformed_users'][user_id] = []
        if channel is None:
            if 'all' not in data[guild_id]['transformed_users'][user_id]:
                data[guild_id]['transformed_users'][user_id].append('all')
        elif channel_id not in data[guild_id]['transformed_users'][user_id]:
            data[guild_id]['transformed_users'][user_id].append(channel_id)

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
    if affixes is not None:
        data[guild_id]['affixes'] = affixes

    if images is not None:
        data[guild_id]['images'] = images if type(images) is int else images.id

    write_file(f'{CACHE_PATH}/transformed.json', data)
    return data[guild_id]


def is_transformed(user: discord.User | discord.Member | int,
                   guild: discord.Guild | int,
                   channel: discord.TextChannel | int | None = None) -> bool:
    """
    Check if a user is transformed in a server, or, optionally, a channel.

    :param user: A Discord user or member object, representing the user to check.
    :param guild: A Discord guild object, representing the server to check.
    :param channel: A Discord channel object, representing the channel to check.

    :return: A boolean value indicating whether the user is transformed in the specified server or, optionally, channel.
    """

    data = load_transformed(guild)
    user_id = str(user if type(user) is int else user.id)
    if data == {} or user_id not in data['transformed_users'] or data['transformed_users'][user_id] in [[], None]:
        return False
    channel_id = 'all' if channel is None else str(channel if type(channel) is int else channel.id)
    return channel_id in data['transformed_users'][user_id] or 'all' in data['transformed_users'][user_id]


def remove_transformed(user: discord.User | discord.Member | int,
                       guild: discord.Guild | int,
                       channel: discord.TextChannel | int | None = None) -> None:
    """
    Removes a user from the transformation data for a server, or, optionally, a channel.

    :param user: A Discord user or member object, representing the user to remove.
    :param guild: A Discord guild object, representing the server from which the user will be removed.
    :param channel: A Discord channel object, representing the channel from which the user will be removed.

    :return: This function does not return anything.
    """

    data = load_transformed()
    if not is_transformed(user, guild, channel):
        return
    guild_id = str(guild if type(guild) is int else guild.id)
    user_id = str(user if type(user) is int else user.id)
    channel_id = 'all' if channel is None else str(channel if type(channel) is int else channel.id)
    data[guild_id]['transformed_users'][user_id].remove(channel_id)
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
    if (original.startswith("*") and original.endswith("*")) or \
            (original.startswith("_") and original.endswith("_")):
        return original

    if data['alt_muffle']['active']:
        # Alternative Muffle will overwrite the entire message with a word from the data array from random chance
        # If we apply this one transformation, that's it. Only this one. That's why it's at the top.
        if original in data['alt_muffle']['contents']:
            return original

        for alt_muffle in data['alt_muffle']['contents']:
            if random.randint(0, 100) <= int(data['alt_muffle']['contents'][alt_muffle]):
                return alt_muffle

    transformed = original
    transformed = clear_apple_marks(transformed)
    words = transformed.split(" ")

    for i in range(len(words)):
        # Force lowercase and strip punctuation

        # Censor will change a word for another, "censoring" it
        if data['censor']['active']:
            raw_word = words[i].lower()
            word = raw_word.strip("*.,!?\"'()[]{}<>:;")

            if word in data['censor']['contents']:
                words[i] = raw_word.replace(word, data['censor']['contents'][word]) # We keep punctuation
                continue

            if raw_word in data['censor']['contents']:
                words[i] = data['censor']['contents'][raw_word] # The entire word should be replaced
                continue

        # Muffle will overwrite a word with a word from the data array by random chance
        if data['muffle']['active']:
            if words[i].startswith("http"):
                continue

            muffles = list(data['muffle']['contents'].keys())
            random.shuffle(muffles)
            for muffle in muffles:
                if random.randint(0, 100) <= int(data['muffle']['contents'][muffle]):
                    words[i] = muffle

    # Sprinkle will add the sprinkled word to the message between words by random chance
    # for each word, if the chance is met, add a sprinkled word before it
    if data['sprinkle']['active']:
        sprinkles = list(data['sprinkle']['contents'].keys())
        for i in range(len(words)):
            random.shuffle(sprinkles)
            for sprinkle in sprinkles:
                if random.randint(0, 100) <= int(data['sprinkle']['contents'][sprinkle]):
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
    if data['prefix']['active']:
        prefixes = list(data['prefix']['contents'].keys())
        random.shuffle(prefixes)
        for prefix in prefixes:
            if random.randint(0, 100) <= int(data['prefix']['contents'][prefix]):
                transformed = prefix + transformed

    if data['suffix']['active']:
        suffixes = list(data['suffix']['contents'].keys())
        random.shuffle(suffixes)
        for suffix in suffixes:
            if random.randint(0, 100) <= int(data['suffix']['contents'][suffix]):
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
            transformed += "-# " + text.strip() + "\n"

        # Make sure mentions work appropriately
        mention_transformed = ""
        for word in transformed.split(" "):
            if word.startswith("<@"):
                word = word.translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789"))
            mention_transformed += word + " "
        transformed = mention_transformed.strip()

    if data['hush']:
        transformed = "||" + transformed + "||"

    return transformed


# ABSTRACTION FUNCTIONS
async def extract_tf_data(ctx: discord.ApplicationContext,
                          user: discord.User | discord.Member | None,
                          get_command: bool = False,
                          channel: discord.TextChannel | None = None) -> tuple[bool,
                                                                               dict | None,
                                                                               discord.User | discord.Member | None]:
    if user is None:
        user = ctx.author
    if not is_transformed(user, ctx.guild, channel):
        await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
        return False, None, None
    data = load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if not get_command and data['claim'] != 0 and data['claim'] != ctx.author.id:
        await ctx.respond(f"You can't do that! {user.mention} is owned by"
                          f"{ctx.guild.get_member(data['claim']).mention}, and not by you!")
        return False, None, None
    return True, data, user


# FILE UTILS
def load_file(filename: str, guild_id: int | None = None) -> dict:
    filename = filename.split("/")
    if filename[-1] not in os.listdir("/".join(filename[:-1])):
        return {}
    try:
        with open("/".join(filename)) as f:
            contents = f.read().strip()
    except OSError as e:
        print("Error loading file:")
        print(f"{str(type(e))}: {e}")
        return {}
    if contents == "":
        return {}
    data = json.loads(contents)
    if guild_id is None:
        return data
    if str(guild_id) in data:
        return data[str(guild_id)]
    return {}


def write_file(filename: str,
               data: dict) -> None:
    try:
        with open(filename, "w+") as f:
            f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.
    except OSError as e:
        print("Error writing to file:")
        print(f"{str(type(e))}: {e}")


# MISCELLANEOUS UTILS
def get_webhook_by_name(webhooks: list[discord.Webhook],
                        name: str) -> discord.Webhook | None:
    for wh in webhooks:
        if wh.name == name:
            return wh
    return None


def get_embed_base(title: str,
                   desc: str | None = None,
                   color: discord.Color = discord.Color.blue()) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=desc,
        color=color,
        author=discord.EmbedAuthor(
            name="TransforMate",
            icon_url="https://cdn.discordapp.com/avatars/967123840587141181/46a629c191f53ec9d446ed4b712fb39b.png"
        )
    )


def check_message(message: discord.Message) -> tuple[int | None, dict | None]:
    transformed_data = load_transformed(message.guild)['transformed_users']
    # Currently, we have to check over ALL transformed users
    # TODO(Before release): Find a better way to do this
    for tfee in transformed_data:
        data = load_tf(int(tfee), message.guild)
        if data == {}:
            continue
        data = data[str(message.channel.id)] if str(message.channel.id) in data else data['all']
        if data['into'] == message.author.name:
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

    if version != 15:
        raise ValueError("encode_tsf() only supports TMUDv15, at the moment!")

    # Basic stuff
    output = "1;%" # TSF v1(.2)
    output += data['into'] + ";%"
    output += data['image_url'] + ";%"

    # Booleans
    boolean_number = 0
    boolean_number += 1 if data['big'] else 0
    boolean_number += 2 if data['small'] else 0
    boolean_number += 4 if data['hush'] else 0
    boolean_number += 8 if data['backwards'] else 0
    output += str(hex(boolean_number))[2:] + ";%"

    # "Easy Stuff"
    output += str(data['stutter']) + ";%"
    output += (data['proxy_prefix'] if data['proxy_prefix'] else "") + ";%"
    output += (data['proxy_suffix'] if data['proxy_suffix'] else "") + ";%"
    output += (data['bio'] if data['bio'] else "") + ";%"

    # Prefix
    output += "1;%" if data['prefix']['active'] else "0;%"
    output += (",%".join([key + "|%" + str(value) for key, value in data['prefix']['contents'].items()])
               if data['prefix']['active'] else "") + ";%"

    # Suffix
    output += "1;%" if data['suffix']['active'] else "0;%"
    output += (",%".join([key + "|%" + str(value) for key, value in data['suffix']['contents'].items()])
               if data['suffix']['active'] else "") + ";%"

    # Sprinkle
    output += "1;%" if data['sprinkle']['active'] else "0;%"
    output += (",%".join([key + "|%" + str(value) for key, value in data['sprinkle']['contents'].items()])
               if data['sprinkle']['active'] else "") + ";%"

    # Muffle
    output += "1;%" if data['muffle']['active'] else "0;%"
    output += (",%".join([key + "|%" + str(value) for key, value in data['muffle']['contents'].items()])
               if data['muffle']['active'] else "") + ";%"

    # Alt Muffle
    output += "1;%" if data['alt_muffle']['active'] else "0;%"
    output += (",%".join([key + "|%" + str(value) for key, value in data['alt_muffle']['contents'].items()])
               if data['alt_muffle']['active'] else "") + ";%"

    # Censor
    output += "1;%" if data['censor']['active'] else "0;%"
    output += (",%".join([key + "|%" + value for key, value in data['censor']['contents'].items()])
               if data['censor']['active'] else "")

    return output

def decode_tsf(tsf_string: str) -> dict:
    """
    Decodes a TSF-compliant string into a TMUD-compliant dict of transformation data.

    :param tsf_string: A TSF-compliant string.

    :return: A TMUD-compliant transformation data dict.
    """

    sep = ";"
    if tsf_string[0:4] == "1;%": # v1.2
        sep = ";%"

    tsf_data = tsf_string.split(sep)
    version = int(tsf_data[0])
    if version != 15 and version != 1: # v1.0 and v1.x
        raise ValueError("decode_tsf() only supports TSFv1.x, at the moment!")

    if version == 15 and len(tsf_data) != 23:
        raise ValueError("decode_tsf() expected 23 elements in the TSFv1.0 string, got " + str(len(tsf_data)))
    if version == 1 and len(tsf_data) != 20:
        raise ValueError("decode_tsf() expected 20 elements in the TSFv1.x string, got " + str(len(tsf_data)))

    tsf_data = tsf_data[1:] # Remove the version identifier for easier handling

    # Booleans
    if version == 15: # v1.0
        big = tsf_data[2] == "1"
        small = tsf_data[3] == "1"
        hush = tsf_data[4] == "1"
        backwards = tsf_data[5] == "1"
        next_index = 6
    else: # v1.x
        boolean_number = int(tsf_data[2], 16)
        big = boolean_number & 1 != 0
        small = boolean_number & 2 != 0
        hush = boolean_number & 4 != 0
        backwards = boolean_number & 8 != 0
        next_index = 3

    # Generate basic data
    data = {
        'into': tsf_data[0],
        'image_url': tsf_data[1],
        'big': big,
        'small': small,
        'hush': hush,
        'backwards': backwards,
        'stutter': int(tsf_data[next_index]),
        'proxy_prefix': tsf_data[next_index + 1],
        'proxy_suffix': tsf_data[next_index + 2],
        'bio': tsf_data[next_index + 3]
    }

    modifiers = ['prefix', 'suffix', 'sprinkle', 'muffle', 'alt_muffle', 'censor']
    for modifier in modifiers:
        data[modifier] = {
            'active': tsf_data[next_index + 4 + modifiers.index(modifier) * 2] != "0",
            'contents': {}
        }
        if not data[modifier]['active']:
            continue
        modifier_data = tsf_data[next_index + 5 + modifiers.index(modifier) * 2].split("," if sep == ";" else ",%")
        for mod in modifier_data:
            if mod == "":
                continue
            key, value = mod.split("|" if sep == ";" else "|%")
            data[modifier]['contents'][key] = int(value) if modifier != 'censor' else value

    return data


def check_url(url: str) -> str:
    """
    This function will check if a given URL is a valid HTTP address, and if it isn't, and it can be fixed, fixes it.

    :param url: The URL to check.

    :return: A string containing a usable URL, blank if the given URL is invalid and con't be automatically fixed.
    """
    if not re.match(r'(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)', url):
        return ""
    if "?" in url:
        url = url[:url.index("?")]
    if not url.startswith("http"): # Basic preliminary check
        return "http://" + url
    return url

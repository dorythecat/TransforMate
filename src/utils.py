import json
import os
import random
import math

from types import NoneType

import discord

from config import CACHE_PATH

# SETTINGS
CLEAR_OLD_TFEE_DATA = True  # If a file is from a previous version that we can't translate, should it be cleared out?
CLEAR_OLD_TRANSFORMED_DATA = True  # Same as above

# DATA VERSIONS
# REMEMBER TO REGENERATE (OR UPDATE) ALL TRANSFORMATION DATA IF YOU CHANGE THE VERSION
# VERSION 15: Added individual chances to all modifiers
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
CURRENT_TFEE_DATA_VERSION = 15

# VERSION 7: Added compatibility with the new multi-character mode for TFee Data v12
# VERSION 6: Added "affixes" field
# VERSION 5: Added "logs" and "clear_other_logs" fields
# VERSION 4: Each user now stores the channels they're transformed on
# VERSION 3: Added "blocked_users" field
# VERSION 2: Added "blocked_channels" and "transformed_users" fields
# VERSION 1: Base version
CURRENT_TRANSFORMED_DATA_VERSION = 7


# USER TRANSFORMATION DATA UTILS
def load_tf_by_id(user_id: str, guild: discord.Guild | int | None = None) -> dict:
    return load_file(f'{CACHE_PATH}/people/{user_id}.json',
                     guild if type(guild) in [int, NoneType] else guild.id)


def load_tf(user: discord.User | discord.Member, guild: discord.Guild | int | None = None) -> dict:
    return load_tf_by_id(str(user.id), guild)

def get_data_version(user: discord.User | discord.Member) -> int:
    return int(load_file(f'{CACHE_PATH}/people/{str(user.id)}.json')['version'])


def write_tf(user: discord.User | discord.Member | int,
             guild: discord.Guild | int,
             channel: discord.TextChannel | int | None = None,
             new_data: dict | None = None,
             block_channel: discord.TextChannel | int | None = None,
             block_user: discord.User | discord.Member | int | None = None,
             transformed_by: str | None = None,
             into: str | None = None,
             image_url: str | None = None,
             claim_user: int | None = None,
             eternal: int | None = None,
             prefix: str | None = None,
             suffix: str | None = None,
             big: int | None = None,
             small: int | None = None,
             hush: int | None = None,
             backwards: int | None = None,
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
    data = load_tf(user)
    user_id = str(user if type(user) is int else user.id)
    guild_id = str(guild if type(guild) is int else guild.id)
    if new_data is not None:
        data[guild_id] = new_data
        write_file(f'{CACHE_PATH}/people/{str(user_id)}.json', data)
        return
    transformed_data = load_transformed(guild)
    if data == {} or data['version'] != CURRENT_TFEE_DATA_VERSION:
        # TODO: Add a way to update (at least) previous version data to newest version
        if CLEAR_OLD_TFEE_DATA:
            data = {}  # Clear data if necessary
        data['version'] = CURRENT_TFEE_DATA_VERSION
    if transformed_data == {}:
        # Write some blank data if there's nothing to read here, and then read it
        transformed_data = write_transformed(guild)
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
            'transformed_by': transformed_by,
            'into': into,
            'image_url': image_url,
            'claim': None,
            'eternal': False,
            'prefix': {
                'active': False,
                'contents': {}
            },
            'suffix': {
                'active': False,
                'contents': {}
            },
            'big': False,
            'small': False,
            'hush': False,
            'backwards': False,
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
        if transformed_by is not None and transformed_by != "":
            data[guild_id][channel_id]['transformed_by'] = transformed_by
        if image_url is not None and image_url != "":
            data[guild_id][channel_id]['image_url'] = image_url
        if claim_user is not None and claim_user != 0:
            data[guild_id][channel_id]['claim'] = claim_user
        if eternal is not None:
            data[guild_id][channel_id]['eternal'] = False if eternal == 0 else True
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
            data[guild_id][channel_id]['big'] = False if big == 0 else True
        if small is not None:
            data[guild_id][channel_id]['small'] = False if small == 0 else True
        if hush is not None:
            data[guild_id][channel_id]['hush'] = False if hush == 0 else True
        if backwards is not None:
            data[guild_id][channel_id]['backwards'] = False if backwards == 0 else True
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


def remove_tf(user: discord.User | discord.Member,
              guild: discord.Guild,
              channel: discord.TextChannel | None = None) -> None:
    data = load_tf(user)
    if data == {} or not str(guild.id) in data or \
            (channel is not None and not str(channel.id) in data[str(guild.id)]) or \
            (channel is None and "all" not in data[str(guild.id)]):
        return
    del data[str(guild.id)]['all' if channel is None else str(channel.id)]
    write_file(f'{CACHE_PATH}/people/{str(user.id)}.json', data)

    remove_transformed(user, guild, channel)


def remove_all_server_tf(user: discord.User | discord.Member,
                         guild: discord.Guild) -> None:
    data = load_tf(user)
    if data == {} or not str(guild.id) in data:
        return
    del data[str(guild.id)]
    write_file(f'{CACHE_PATH}/people/{str(user.id)}.json', data)

    remove_transformed(user, guild)


def remove_all_tf(user: discord.User | discord.Member) -> None:
    os.remove(f'{CACHE_PATH}/people/{str(user.id)}.json')


# TRANSFORMED DATA UTILS
def load_transformed(guild: discord.Guild | int | None = None) -> dict:
    return load_file(f'{CACHE_PATH}/transformed.json', guild if type(guild) in [int, NoneType] else guild.id)


def write_transformed(guild: discord.Guild | int,
                      user: discord.User | discord.Member | int | None = None,
                      channel: discord.TextChannel | int | None = None,
                      block_user: discord.User | discord.Member | int | None = None,
                      block_channel: discord.TextChannel | int | None = None,
                      logs: list[int | None] | None = None,  # [edit, del, tf, claim]
                      clear_other_logs: bool | None = None,
                      affixes: bool | None = None) -> dict:
    data = load_transformed()
    if data == {} or data['version'] != CURRENT_TRANSFORMED_DATA_VERSION:
        if CLEAR_OLD_TRANSFORMED_DATA:
            data = {}  # Clear data if necessary
        data['version'] = CURRENT_TRANSFORMED_DATA_VERSION

    guild_id = str(guild if type(guild) is int else guild.id)
    if guild_id not in data:
        data[guild_id] = {
            'blocked_users': [],
            'blocked_channels': [],
            'logs': [None, None, None, None],
            'clear_other_logs': False,
            'affixes': False,
            'transformed_users': {}
        }

    if user is not None:
        user_id = str(user if type(user) is int else user.id)
        channel_id = str(channel if type(channel) is int else channel.id)
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

    write_file(f'{CACHE_PATH}/transformed.json', data)
    return data[guild_id]


def is_transformed(user: discord.User | discord.Member | int,
                   guild: discord.Guild | int,
                   channel: discord.TextChannel | int | None = None) -> bool:
    data = load_transformed(guild)
    user_id = str(user if type(user) is int else user.id)
    channel_id = 'all' if channel is None else str(channel if type(channel) in int else channel.id)
    if data == {} or user_id not in data['transformed_users']:
        return False
    if data['transformed_users'][user_id] not in [[], None] and channel_id in data['transformed_users'][user_id]:
        return True
    return False


def remove_transformed(user: discord.User | discord.Member,
                       guild: discord.Guild,
                       channel: discord.TextChannel | None = None) -> None:
    data = load_transformed()
    if not is_transformed(user, guild, channel):
        return
    data[str(guild.id)]['transformed_users'][str(user.id)].remove(str(channel.id) if channel is not None else 'all')
    write_file(f'{CACHE_PATH}/transformed.json', data)


def remove_server_from_transformed(guild: discord.Guild):
    data = load_transformed()
    del data[str(guild.id)]
    write_file(f'{CACHE_PATH}/transformed.json', data)


# TEXT UTILS
# Apply all necessary modifications to the message, based on the user's transformation data
def transform_text(data: dict,
                   original: str) -> str:
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
            if words[i].startswith("http"):
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
            transformed += "-# " + text.strip() + "\n"

    if data['hush']:
        transformed = "||" + transformed + "||"

    return transformed


# ABSTRACTION FUNCTIONS
async def extract_tf_data(ctx: discord.ApplicationContext,
                          user: discord.User | discord.Member | None,
                          get_command: bool = False,
                          channel: discord.TextChannel | None = None) -> [bool,
                                                         dict | None,
                                                         discord.User | discord.Member | None]:
    if user is None:
        user = ctx.author
    if not is_transformed(user, ctx.guild, channel):
        await ctx.respond(f"You can't do that! {user.mention} is not transformed at the moment!")
        return [False, None, None]
    data = load_tf(user, ctx.guild)
    data = data[str(ctx.channel.id)] if str(ctx.channel.id) in data else data['all']
    if not get_command and data['claim'] is not None and data['claim'] != ctx.author.id:
        await ctx.respond(f"You can't do that! {user.mention} is owned by"
                          f"{ctx.guild.get_member(data['claim']).mention}, and not by you!")
        return [False, None, None]
    return [True, data, user]


# FILE UTILS
def load_file(filename: str,
              guild_id: int | None = None) -> dict:
    filename = filename.split("/")
    if filename[-1] not in os.listdir("/".join(filename[:-1])):
        return {}
    with open("/".join(filename)) as f:
        contents = f.read().strip()
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
    with open(filename, "w+") as f:
        f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.


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


def check_message(message: discord.Message) -> [int | None, dict | None]:
    transformed_data = load_transformed(message.guild)['transformed_users']
    # Currently, we have to check over ALL transformed users
    # TODO(Before release): Find a better way to do this
    for tfee in transformed_data:
        data = load_tf_by_id(tfee, message.guild)
        if data == {}:
            continue
        data = data[str(message.channel.id)] if str(message.channel.id) in data else data['all']
        if data['into'] == message.author.name:
            return [int(tfee), data]
    return [None, None]

def check_reactions(reaction: discord.Reaction) -> [int | None, dict | None]:
    return check_message(reaction.message)


def clear_apple_marks(text: str) -> str:
    text = text.replace("’", "'")
    text = text.replace("“", "\"")
    return text.replace("”", "\"")

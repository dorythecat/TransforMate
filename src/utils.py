import json
import os
import random
import discord

from src.config import CACHE_PATH

# SETTINGS
CLEAR_OLD_TFEE_DATA = True  # If a file is from a previous version, should it be cleared out?
CLEAR_OLD_TRANSFORMED_DATA = True  # Same as above

# DATA VERSIONS
# REMEMBER TO REGENERATE (OR UPDATE) ALL TRANSFORMATION DATA IF YOU CHANGE THE VERSION
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
CURRENT_TFEE_DATA_VERSION = 14

# VERSION 7: Added compatibility with the new multi-character mode for TFee Data v12
# VERSION 6: Added "affixes" field
# VERSION 5: Added "logs" and "clear_other_logs" fields
# VERSION 4: Each user now stores the channels they're transformed on
# VERSION 3: Added "blocked_users" field
# VERSION 2: Added "blocked_channels" and "transformed_users" fields
# VERSION 1: Base version
CURRENT_TRANSFORMED_DATA_VERSION = 7


# USER TRANSFORMATION DATA UTILS
def load_tf_by_id(user_id: str,
                  guild: discord.Guild | None = None) -> dict:
    return {} if f'{user_id}.json' not in os.listdir(f'{CACHE_PATH}/people') else \
        load_file(f'{CACHE_PATH}/people/{user_id}.json', guild)


def load_tf(user: discord.User | discord.Member,
            guild: discord.Guild | None = None) -> dict:
    return load_tf_by_id(str(user.id), guild)


def write_tf(user: discord.User | discord.Member,
             guild: discord.Guild,
             channel: discord.TextChannel | None = None,
             new_data: dict | None = None,
             block_channel: discord.TextChannel | None = None,
             block_user: discord.User | discord.Member | None = None,
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
             mod_type: str | None = None,
             proxy_prefix: str | None = None,
             proxy_suffix: str | None = None,
             bio: str | None = None) -> None:
    data = load_tf(user)
    if new_data is not None:
        data[str(guild.id)] = new_data
        write_file(f'{CACHE_PATH}/people/{str(user.id)}.json', data)
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
        channel_id = 'all' if channel is None else str(channel.id)
    if into not in ["", None]:
        if str(guild.id) not in data:
            data[str(guild.id)] = {}
            data[str(guild.id)]['blocked_channels'] = []
            data[str(guild.id)]['blocked_users'] = []
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
            'backwards': False,
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
            'alt_muffle': {
                'active': False,
                'contents': [],
                'chance': 0
            },
            'stutter': 0,
            'proxy_prefix': proxy_prefix,
            'proxy_suffix': proxy_suffix,
            'bio': None
        }
    else:
        if transformed_by is not None and transformed_by != "":
            data[str(guild.id)][channel_id]['transformed_by'] = transformed_by
        if image_url is not None and image_url != "":
            data[str(guild.id)][channel_id]['image_url'] = image_url
        if claim_user is not None and claim_user != 0:
            data[str(guild.id)][channel_id]['claim'] = claim_user
        if eternal is not None:
            data[str(guild.id)][channel_id]['eternal'] = False if eternal == 0 else True
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
        if prefix is not None:
            data[str(guild.id)][channel_id]['prefix']['active'] = True if prefix != "" else False
            data[str(guild.id)][channel_id]['prefix']['contents'] += [prefix.strip()] if (prefix not in
                data[str(guild.id)][channel_id]['prefix']['contents']) else []
            if prefix == "":
                data[str(guild.id)][channel_id]['prefix']['contents'] = []
            data[str(guild.id)][channel_id]['prefix']['chance'] = 100 if prefix != "" else 0
        if suffix is not None:
            data[str(guild.id)][channel_id]['suffix']['active'] = True if suffix != "" else False
            data[str(guild.id)][channel_id]['suffix']['contents'] += [suffix.strip()] if (suffix not in
                data[str(guild.id)][channel_id]['suffix']['contents']) else []
            if suffix == "":
                data[str(guild.id)][channel_id]['suffix']['contents'] = []
            data[str(guild.id)][channel_id]['suffix']['chance'] = 100 if suffix != "" else 0
        if big is not None:
            data[str(guild.id)][channel_id]['big'] = False if big == 0 else True
        if small is not None:
            data[str(guild.id)][channel_id]['small'] = False if small == 0 else True
        if hush is not None:
            data[str(guild.id)][channel_id]['hush'] = False if hush == 0 else True
        if backwards is not None:
            data[str(guild.id)][channel_id]['backwards'] = False if backwards == 0 else True
        if censor is not None:
            data[str(guild.id)][channel_id]['censor']['active'] = True if censor != "" else False
            if censor != "":
                censor = clear_apple_marks(censor)
                if censor_replacement not in ["", None]:
                    if data[str(guild.id)][channel_id]['censor']['contents'] is None:
                        data[str(guild.id)][channel_id]['censor']['contents'] = {}
                    data[str(guild.id)][channel_id]['censor']['contents'][censor.strip().lower()] = \
                        censor_replacement.strip().lower()
        if sprinkle is not None:
            data[str(guild.id)][channel_id]['sprinkle']['active'] = True if sprinkle != "" else False
            data[str(guild.id)][channel_id]['sprinkle']['contents'] += [sprinkle.strip()] if (sprinkle not in
                data[str(guild.id)][channel_id]['sprinkle']['contents']) else []
            if sprinkle == "":
                data[str(guild.id)][channel_id]['sprinkle']['contents'] = []
            data[str(guild.id)][channel_id]['sprinkle']['chance'] = 30 if sprinkle != "" else 0
        if muffle is not None:
            data[str(guild.id)][channel_id]['muffle']['active'] = True if muffle != "" else False
            data[str(guild.id)][channel_id]['muffle']['contents'] += [muffle.strip()] if (muffle not in
                data[str(guild.id)][channel_id]['muffle']['contents']) else []
            if muffle == "":
                data[str(guild.id)][channel_id]['muffle']['contents'] = []
            data[str(guild.id)][channel_id]['muffle']['chance'] = 30 if muffle != "" else 0
        if alt_muffle is not None:
            data[str(guild.id)][channel_id]['alt_muffle']['active'] = True if alt_muffle != "" else False
            data[str(guild.id)][channel_id]['alt_muffle']['contents'] += [alt_muffle.strip()] if (alt_muffle not in
                data[str(guild.id)][channel_id]['alt_muffle']['contents']) else []
            if alt_muffle == "":
                data[str(guild.id)][channel_id]['alt_muffle']['contents'] = []
            data[str(guild.id)][channel_id]['alt_muffle']['chance'] = 30 if alt_muffle != "" else 0

        if stutter is not None:
            data[str(guild.id)][channel_id]['stutter'] = stutter

        if mod_type is not None and chance:
            if mod_type in ['prefix', 'suffix', 'sprinkle', 'muffle', 'alt_muffle']:
                data[str(guild.id)][channel_id][mod_type]['chance'] = chance
            elif mod_type in ['stutter']:
                data[str(guild.id)][channel_id][mod_type] = chance

        if proxy_prefix is not None:
            data[str(guild.id)][channel_id]['proxy_prefix'] = None if proxy_prefix == "" else proxy_prefix
        if proxy_suffix is not None:
            data[str(guild.id)][channel_id]['proxy_suffix'] = None if proxy_suffix == "" else proxy_suffix

        if bio is not None:
            data[str(guild.id)][channel_id]['bio'] = None if bio == "" else bio
    write_file(f'{CACHE_PATH}/people/{str(user.id)}.json', data)


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


def remove_all_server_tf(user: discord.User | discord.Member,
                         guild: discord.Guild) -> None:
    data = load_tf(user)
    if data == {} or not str(guild.id) in data:
        return
    del data[str(guild.id)]
    write_file(f'{CACHE_PATH}/people/{str(user.id)}.json', data)


def remove_all_tf(user: discord.User | discord.Member) -> None:
    os.remove(f'{CACHE_PATH}/people/{str(user.id)}.json')


# TRANSFORMED DATA UTILS
def load_transformed(guild: discord.Guild | None = None) -> dict:
    return {} if 'transformed.json' not in os.listdir(CACHE_PATH) else \
        load_file(f'{CACHE_PATH}/transformed.json', guild)


def write_transformed(guild: discord.Guild,
                      user: discord.User | discord.Member | None = None,
                      channel: discord.TextChannel | None = None,
                      block_user: discord.User | discord.Member | None = None,
                      block_channel: discord.TextChannel | None = None,
                      logs: list[int | None] | None = None,  # [edit, del, tf, claim]
                      clear_other_logs: bool | None = None,
                      affixes: bool | None = None) -> dict:
    data = load_transformed()
    if data == {} or data['version'] != CURRENT_TRANSFORMED_DATA_VERSION:
        if CLEAR_OLD_TRANSFORMED_DATA:
            data = {}  # Clear data if necessary
        data['version'] = CURRENT_TRANSFORMED_DATA_VERSION

    if str(guild.id) not in data:
        data[str(guild.id)] = {
            'blocked_users': [],
            'blocked_channels': [],
            'logs': [None, None, None, None],
            'clear_other_logs': False,
            'affixes': False,
            'transformed_users': {}
        }

    if user is not None:
        if str(user.id) not in data[str(guild.id)]['transformed_users']:
            data[str(guild.id)]['transformed_users'][str(user.id)] = []
        if channel is None:
            if 'all' not in data[str(guild.id)]['transformed_users'][str(user.id)]:
                data[str(guild.id)]['transformed_users'][str(user.id)].append('all')
        elif str(channel.id) not in data[str(guild.id)]['transformed_users'][str(user.id)]:
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

    if logs is not None:
        data[str(guild.id)]['logs'] = logs

    if clear_other_logs is not None:
        data[str(guild.id)]['clear_other_logs'] = clear_other_logs
    if affixes is not None:
        data[str(guild.id)]['affixes'] = affixes

    write_file(f'{CACHE_PATH}/transformed.json', data)
    return data[str(guild.id)]


def is_transformed(user: discord.User | discord.Member,
                   guild: discord.Guild,
                   channel: discord.TextChannel | None = None) -> bool:
    data = load_transformed(guild)
    if data == {} or str(user.id) not in data['transformed_users']:
        return False
    if data['transformed_users'][str(user.id)] not in [[], None] and \
            ((channel is not None and str(channel.id) in data['transformed_users'][str(user.id)]) or
             'all' in data['transformed_users'][str(user.id)]):
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
        if random.randint(1, 100) <= data['alt_muffle']['chance']:
            return data['alt_muffle']['contents'][random.randint(0, len(data['alt_muffle']['contents']) - 1)]

    transformed = original
    transformed = clear_apple_marks(transformed)
    words = transformed.split(" ")

    for i in range(len(words)):
        # Force lowercase and strip punctuation

        # Censor will change a word for another, "censoring" it
        if data['censor']['active']:
            raw_word = words[i].lower()
            word = raw_word.strip("*.,!?\"'()[]{}<>:;")

            if word in data['censor']['contents'].keys():
                words[i] = raw_word.replace(word, data['censor']['contents'][word]) # We keep punctuation
                continue

            if raw_word in data['censor']['contents'].keys():
                words[i] = data['censor']['contents'][raw_word] # The entire word should be replaced
                continue

        # Muffle will overwrite a word with a word from the data array by random chance
        if data['muffle']['active']:
            if words[i].startswith("http"):
                continue
            if random.randint(1, 100) <= data['muffle']['chance']:
                words[i] = data['muffle']['contents'][random.randint(0, len(data['muffle']['contents']) - 1)]
                continue

    # Sprinkle will add the sprinkled word to the message between words by random chance
    # for each word, if the chance is met, add a sprinkled word before it
    if data['sprinkle']['active']:
        for i in range(len(words)):
            if random.randint(1, 100) <= data['sprinkle']['chance']:
                words[i] = data['sprinkle']['contents'][
                               random.randint(0, len(data['sprinkle']['contents']) - 1)] + " " + words[i]

    if data['stutter'] > 0:
        for i in range(len(words)):
            if words[i].startswith("http"):
                continue
            if random.randint(1, 100) <= data['stutter']:
                words[i] = words[i][0] + "-" + words[i]
    transformed = " ".join(words)

    # Moving these below, so text changes are applied before the prefix and suffix so they aren't affected
    # by censors or such
    if data['prefix']['active']:
        # Prefix will add the prefix to the message, try the chance of adding it,
        # and then select a random prefix from the list
        if (0 <= data['prefix']['chance'] < 100 and random.randint(1, 100) <= data['prefix']['chance']) or \
                data['prefix']['chance'] >= 100:
            transformed = data['prefix']['contents'][
                              random.randint(0, len(data['prefix']['contents']) - 1)] + " " + transformed

    if data['suffix']['active']:
        # Suffix will add the suffix to the message, try the chance of adding it,
        # and then select a random suffix from the list
        if (0 <= data['suffix']['chance'] < 100 and random.randint(1, 100) <= data['suffix']['chance']) or \
                data['suffix']['chance'] >= 100:
            transformed = transformed + " " + data['suffix']['contents'][
                random.randint(0, len(data['suffix']['contents']) - 1)]

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

    if data['backwards']:
        transformed = transformed[::-1]

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
              guild: discord.Guild | None = None) -> dict:
    with open(filename) as f:
        contents = f.read().strip()
        if contents == "":
            return {}
        data = json.loads(contents)
        if guild is None:
            return data
        if str(guild.id) in data:
            return data[str(guild.id)]
        return {}


def write_file(filename: str,
               data: dict) -> None:
    with open(filename, "w+") as f:
        f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.


# COMPRESSION
def encode_url(url: str) -> str:
    header = 1 if not url.find("https://") else 0  # 0: http:// 1: https://
    output = str(header)
    url = url[(7 + header):]
    if url[:27] == "cdn.discordapp.com/avatars/":
        output += "0"
        url = url[27:]  # 0: cdn.discordapp.com/avatars/
    elif url[:33] == "media.discordapp.net/attachments/":
        output += "1"  # 1: media.discordapp.net/attachments/
        url = url[33:]
    elif url[:37] == "images-ext-1.discordapp.net/external/":
        output += "2"  # 2: images-ext-1.discordapp.net/external/
        url = url[37:]

    if url.rfind(".png") == len(url) - 4: url = url[:url.rfind(".png")] + "0"  # 0: .png
    elif url.rfind(".jpg") == len(url) - 4: url = url[:url.rfind(".jpg")] + "1"  # 1: .jpg
    elif url.rfind(".webp") == len(url) - 5: url = url[:url.rfind(".webp")] + "2"  # 2: .webp
    elif url.rfind(".jpeg") == len(url) - 5: url = url[:url.rfind(".jpeg")] + "3"  # 3: .jpeg
    elif url.rfind(".gif") == len(url) - 4: url = url[:url.rfind(".gif")] + "4"  # 4: .gif

    return output + url


def decode_url(encoded: str) -> str:
    # Check encode_url for the expected association of values
    url = "https://" if encoded[0] else "http://"

    if encoded[1] == "0": url += "cdn.discordapp.com/avatars/"
    elif encoded[1] == "1": url += "media.discordapp.net/attachments/"
    elif encoded[1] == "2": url += "images-ext-1.discordapp.net/external/"

    url += encoded[2:(len(encoded) - 1)]

    match encoded[len(encoded) - 1]:
        case "0": url += ".png"
        case "1": url += ".jpg"
        case "2": url += ".webp"
        case "3": url += ".jpeg"
        case "4": url += ".gif"
    return url


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

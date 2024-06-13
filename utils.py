import json
import os

import discord

# VERSION 3: Added "big", "small", and "hush" fields, and changed "eternal" from bool to int
# VERSION 2: Added guild specific data
# VERSION 1: Base version
CURRENT_TFEE_DATA_VERSION = 3

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


def load_tf(user: discord.User, guild: discord.Guild = None) -> dict: return load_tf_by_name(user.name, guild)


def write_tf(user: discord.User,
             guild: discord.Guild,
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
        data["version"] = CURRENT_TFEE_DATA_VERSION
    elif data["version"] != CURRENT_TFEE_DATA_VERSION:
        data["version"] = CURRENT_TFEE_DATA_VERSION
        if data["version"] < 2:
            data[str(guild.id)] = {
                "transformed_by": data["transformed_by"],
                "into": data["into"],
                "image_url": data["image_url"],
                "claim": data["claim"],
                "eternal": data["eternal"],
                "prefix": data["prefix"],
                "suffix": data["suffix"],
                "big": False,
                "small": False,
                "hush": False,
                "censor": {
                    "active": data["censor"]["active"],
                    "contents": data["censor"]["contents"]
                },
                "sprinkle": {
                    "active": data["sprinkle"]["active"],
                    "contents": data["sprinkle"]["contents"]
                },
                "muffle": {
                    "active": data["muffle"]["active"],
                    "contents": data["muffle"]["contents"]
                }
            }
        elif data["version"] < 3:
            data[str(guild.id)]["big"] = False
            data[str(guild.id)]["small"] = False
            data[str(guild.id)]["hush"] = False
    if into not in ["", None]:
        data[str(guild.id)] = {  # Add guild specific data
            "transformed_by": transformed_by,
            "into": into,
            "image_url": image_url,
            "claim": claim_user,
            "eternal": False if eternal == 0 else True,
            "prefix": prefix,
            "suffix": suffix,
            "big": False if big == 0 else True,
            "small": False if small == 0 else True,
            "hush": False if hush == 0 else True,
            "censor": {
                "active": censor_bool,
                "contents": censor
            },
            "sprinkle": {
                "active": sprinkle_bool,
                "contents": sprinkle
            },
            "muffle": {
                "active": muffle_bool,
                "contents": muffle
            }
        }
    else:
        if transformed_by is not None and transformed_by != "":
            data[str(guild.id)]["transformed_by"] = transformed_by
        if image_url is not None and image_url != "":
            data[str(guild.id)]["image_url"] = image_url
        if claim_user is not None and claim_user != "":
            data[str(guild.id)]["claim"] = claim_user.strip()
        elif claim_user == "":
            data[str(guild.id)]["claim"] = None
        if eternal is not None:
            if eternal == 0:
                data[str(guild.id)]["eternal"] = False
            else:
                data[str(guild.id)]["eternal"] = True
        if prefix is not None:
            if prefix != "":
                data[str(guild.id)]["prefix"] = prefix
            else:
                data[str(guild.id)]["prefix"] = None
        if suffix is not None:
            if suffix != "":
                data[str(guild.id)]["suffix"] = suffix
            else:
                data[str(guild.id)]["suffix"] = None
        if big is not None:
            if big == 0:
                data[str(guild.id)]["big"] = False
            else:
                data[str(guild.id)]["big"] = True
        if small is not None:
            if small == 0:
                data[str(guild.id)]["small"] = False
            else:
                data[str(guild.id)]["small"] = True
        if hush is not None:
            if hush == 0:
                data[str(guild.id)]["hush"] = False
            else:
                data[str(guild.id)]["hush"] = True
        if censor is not None and censor != "":
            data[str(guild.id)]["censor"]["active"] = True
            data[str(guild.id)]["censor"]["contents"] = censor.strip()
        elif censor == "":
            data[str(guild.id)]["censor"]["active"] = False
            data[str(guild.id)]["censor"]["contents"] = None
        if sprinkle is not None and sprinkle != "":
            data[str(guild.id)]["sprinkle"]["active"] = True
            data[str(guild.id)]["sprinkle"]["contents"] = sprinkle.strip()
        elif sprinkle == "":
            data[str(guild.id)]["sprinkle"]["active"] = False
            data[str(guild.id)]["sprinkle"]["contents"] = None
        if muffle is not None and muffle != "":
            data[str(guild.id)]["muffle"]["active"] = True
            data[str(guild.id)]["muffle"]["contents"] = muffle.strip()
        elif muffle == "":
            data[str(guild.id)]["muffle"]["active"] = False
            data[str(guild.id)]["muffle"]["contents"] = None
    with open(f"cache/people/{user.name}.json", "w+") as f:
        f.write(json.dumps(data, indent=4))  # Indents are just so that data is more readable. Remove for production.


def remove_tf(user: discord.User, guild: discord.Guild) -> None:
    data = load_tf(user)
    del data[guild.id]
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
def transform_text(tf_data: dict, original: str) -> str:
    transformed = original
    if tf_data["prefix"]:
        transformed = tf_data["prefix"] + transformed
    if tf_data["suffix"]:
        transformed = transformed + tf_data["suffix"]
    return transformed


# MISCELLANEOUS UTILS
def get_webhook_by_name(webhooks, name) -> discord.Webhook or None:
    for wh in webhooks:
        if wh.name == name:
            return wh
    return None

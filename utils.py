import json
import os

import discord

CURRENT_TFEE_DATA_VERSION = 2
# VERSION 1: Base version
# VERSION 2: Added guild specific data

CURRENT_TRANSFORMED_DATA_VERSION = 1
# VERSION 1: Base version


def get_webhook_by_name(webhooks, name) -> discord.Webhook or None:
    for wh in webhooks:
        if wh.name == name:
            return wh
    return None


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
             transformed_by: str = None,
             into: str = None,
             image_url: str = None,
             claim_user: str = None,
             eternal: bool = False,
             prefix: str = None,
             suffix: str = None,
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
            data[guild.id] = {
                "transformed_by": data["transformed_by"],
                "into": data["into"],
                "image_url": data["image_url"],
                "claim": data["claim"],
                "eternal": data["eternal"],
                "prefix": data["prefix"],
                "suffix": data["suffix"],
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
    if into not in ["", None]:
        data[str(guild.id)] = {  # Add guild specific data
            "transformed_by": transformed_by,
            "into": into,
            "image_url": image_url,
            "claim": claim_user,
            "eternal": eternal,
            "prefix": prefix,
            "suffix": suffix,
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
        if transformed_by:
            data[str(guild.id)]["transformed_by"] = transformed_by
        if image_url:
            data[str(guild.id)]["image_url"] = image_url
        if claim_user:
            data[str(guild.id)]["claim"] = claim_user.strip()
        elif claim_user.strip() == "":
            data[str(guild.id)]["claim"] = None
        if eternal:
            data[str(guild.id)]["eternal"] = eternal
        if prefix:
            data[str(guild.id)]["prefix"] = prefix
        if suffix:
            data[str(guild.id)]["suffix"] = suffix
        if censor:
            data[str(guild.id)]["censor"]["active"] = True
            data[str(guild.id)]["censor"]["contents"] = censor.strip()
        elif censor.strip() == "":
            data[str(guild.id)]["censor"]["active"] = False
            data[str(guild.id)]["censor"]["contents"] = None
        if sprinkle:
            data[str(guild.id)]["sprinkle"]["active"] = True
            data[str(guild.id)]["sprinkle"]["contents"] = sprinkle.strip()
        elif sprinkle.strip() == "":
            data[str(guild.id)]["sprinkle"]["active"] = False
            data[str(guild.id)]["sprinkle"]["contents"] = None
        if muffle:
            data[str(guild.id)]["muffle"]["active"] = True
            data[str(guild.id)]["muffle"]["contents"] = muffle.strip()
        elif muffle.strip() == "":
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
    if guild.id not in data:
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


def is_transformed(user: discord.User, guild: discord.Guild) -> bool:
    return user.name in load_transformed(guild)


def get_transformed(guild: discord.Guild) -> dict:
    return load_transformed(guild)

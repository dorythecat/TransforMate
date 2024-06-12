import json

import discord

CURRENT_DATA_VERSION = 1


def get_webhook_by_name(webhooks, name) -> discord.Webhook or None:
    for wh in webhooks:
        if wh.name == name:
            return wh
    return None


def load_tf(user: discord.User) -> dict:
    with open(f"cache/people/{user.name}.json", "r") as f:
        return json.loads(f.read())


def load_tf_by_name(name: str) -> dict:
    with open(f"cache/people/{name}.json", "r") as f:
        return json.loads(f.read())


def write_tf(user: discord.User,
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
    if into not in ["", None]:
        data = {
            "version": CURRENT_DATA_VERSION,
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
        data = load_tf(user)
        # Add all the new data
        # Could this be made more efficient? Probably, but I'm too lazy to do it right now
        # TODO: Improve this code.

        # Check if the version is correct
        # if data["version"] != CURRENT_DATA_VERSION:
        # Here we would make sure any changes that haven't been implemented yet on older versions are implemented

        if transformed_by:
            data["transformed_by"] = transformed_by
        if image_url:
            data["image_url"] = image_url
        if claim_user:
            data["claim"] = claim_user.strip()
        elif claim_user.strip() == "":
            data["claim"] = None
        if eternal:
            data["eternal"] = eternal
        if prefix:
            data["prefix"] = prefix
        if suffix:
            data["suffix"] = suffix
        if censor:
            data["censor"]["active"] = True
            data["censor"]["contents"] = censor.strip()
        elif censor.strip() == "":
            data["censor"]["active"] = False
            data["censor"]["contents"] = None
        if sprinkle:
            data["sprinkle"]["active"] = True
            data["sprinkle"]["contents"] = sprinkle.strip()
        elif sprinkle.strip() == "":
            data["sprinkle"]["active"] = False
            data["sprinkle"]["contents"] = None
        if muffle:
            data["muffle"]["active"] = True
            data["muffle"]["contents"] = muffle.strip()
        elif muffle.strip() == "":
            data["muffle"]["active"] = False
            data["muffle"]["contents"] = None
    with open(f"cache/people/{user.name}.json", "w+") as f:
        f.write(json.dumps(data, indent=4)) # Indents are just so that data is more readable. Remove for production.

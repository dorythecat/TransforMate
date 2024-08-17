import os
from dotenv import load_dotenv


# Helper function to parse a string into a list of integers
def parse_list(string: str | None) -> list[int]:
    if string is None or string.strip() in ["", "[]"]:
        return []
    output = string.removeprefix("[").removesuffix("]").split(",")
    return [int(output[i].strip()) for i in range(len(output))]


# Get settings from .env file
if not load_dotenv():
    raise Exception("Either your .env file is empty, or you don't even have a .env file! Aborting")

if os.getenv("BOT_TOKEN") is None:
    raise Exception("BOT_TOKEN hasn't been provided! Check your .env! Aborting")
BOT_TOKEN: str = os.getenv("BOT_TOKEN")  # Token for the bot

if os.getenv("WEBHOOK_NAME") is None:
    raise Exception("WEBHOOK_NAME hasn't been provided! Check your .env! Aborting")
WEBHOOK_NAME: str = os.getenv("WEBHOOK_NAME")  # Name to use for the webhooks

if os.getenv("BLOCKED_USERS") is None:
    raise Exception("BLOCKED_USERS hasn't been provided! Check your .env! Aborting")
BLOCKED_USERS: list[int] = parse_list(os.getenv("BLOCKED_USERS"))  # Users that are blocked from using the bot

if os.getenv("USER_REPORTS_CHANNEL_ID") is None:
    raise Exception("USER_REPORTS_CHANNEL_ID hasn't been provided! Check your .env! Aborting")
USER_REPORTS_CHANNEL_ID: int = int(os.getenv("USER_REPORTS_CHANNEL_ID"))  # Channel to use for the /report command

if os.getenv("CACHE_PATH") is None:
    raise Exception("CACHE_PATH hasn't been provided! Check your .env! Aborting")
CACHE_PATH: str = os.getenv("CACHE_PATH")  # What's the path to the cache folder? (In relationship to the utils.py file)

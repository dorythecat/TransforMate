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

required_variables = ["BOT_TOKEN", "WEBHOOK_NAME", "BLOCKED_USERS", "USER_REPORTS_CHANNEL_ID", "CACHE_PATH",
                      "SECRET_KEY", "CLIENT_ID", "CLIENT_SECRET", "REDIRECT_URI",
                      "PATREON_SERVERS"]
for var in required_variables:
    if os.getenv(var) is None:
        raise Exception(f"{var} hasn't been provided! Check your .env! Aborting")
    elif os.getenv(var) in [""]:
        raise Exception(f"{var} has been provided, but is empty! Check your .env! Aborting")

# General bot configuration
BOT_TOKEN: str = os.getenv("BOT_TOKEN")  # Token for the bot
WEBHOOK_NAME: str = os.getenv("WEBHOOK_NAME")  # Name to use for the webhooks
BLOCKED_USERS: list[int] = parse_list(os.getenv("BLOCKED_USERS"))  # Users that are blocked from using the bot
USER_REPORTS_CHANNEL_ID: int = int(os.getenv("USER_REPORTS_CHANNEL_ID"))  # Channel to use for the /report command
CACHE_PATH: str = os.getenv("CACHE_PATH")  # What's the path to the cache folder? (In relationship to the utils.py file)
MAX_REGEN_USERS: int = int(os.getenv("MAX_REGEN_USERS")) # Maximum number of users in a server allowed for /regen_server_tfs

# API settings
SECRET_KEY: str = os.getenv("SECRET_KEY") # Secret key for encoding passwords and others
CLIENT_ID: str = os.getenv("CLIENT_ID")
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET")
REDIRECT_URI: str = os.getenv("REDIRECT_URI")

# Patreon settings
PATREON_SERVERS: list[int] = parse_list(os.getenv("PATREON_USERS"))
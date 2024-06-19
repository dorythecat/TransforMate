import os
from dotenv import load_dotenv


# Helper function to parse a string into a list of integers
def parse_list(string: str) -> list[int]:
    if string.strip() == "":
        return []
    output = string.removeprefix("[").removesuffix("]").split(",")
    return [int(output[i].strip()) for i in range(len(output))]


# Get settings from .env file
load_dotenv()
BOT_TOKEN: str = os.getenv("BOT_TOKEN")  # Token for the bot
WEBHOOK_NAME: str = os.getenv("WEBHOOK_NAME")  # Name to use for the webhooks
BLOCKED_USERS: list[int] = parse_list(os.getenv("BLOCKED_USERS"))  # Users that are blocked from using the bot
USER_REPORTS_CHANNEL_ID: int = int(os.getenv("USER_REPORTS_CHANNEL_ID"))  # Channel to use for the /report command

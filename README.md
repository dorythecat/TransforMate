![GitHub last commit](https://img.shields.io/github/last-commit/dorythecat/TransforMate)
[![Qodana](https://github.com/dorythecat/TransforMate/actions/workflows/code_quality.yml/badge.svg)](https://github.com/dorythecat/TransforMate/actions/workflows/code_quality.yml)
[![CodeQL](https://github.com/dorythecat/TransforMate/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/dorythecat/TransforMate/actions/workflows/github-code-scanning/codeql)

# TransforMate
> A bot to Transform your Mates

## Who's this bot for?
Ever felt like Tupperbox and PluralKit weren't enough for your RPs? Ever felt
like you needed to spice them up, transforming your friends and family? Well,
look no further! With TransforMate, this task is made much simpler!

## Current Features
### For users:
- Transform yourself and others
- Go back and forth with a single command
- Highly customizable and modular
- Straightforward to use and understand
- Well-documented, open-source, and in active development and support
- Friendly, helpful, and active community
- Free to use
- No ads, no tracking, no selling of data

### For server staff:
- Little to none setup and configuration
- Easily configurable for all kinds of servers
- Block users from using the bot, on a per-user or per-server basis
- Global ban system that helps you keep your server safe from known bad actors
- A big (and growing) community for support

### For developers:
- Open-source, with a permissive license
- Well-documented, with a clear and easy-to-understand codebase
- Easy to contribute to, with a friendly and welcoming community
- Active development and support
- Fully open source data formats

## Upcoming Features
- Avoid logging deleted messages in most popular log bots
- More customization options, both for users AND server staff
- ~~Custom API~~
- ~~Webpage and web interface~~
- ~~Even better documentation~~
- Optimised file structure
- Plugins and custom scripting language
- And more fun stuff!!!

## Inviting TransforMate
To invite TransforMate to your server, you can use [this link](https://discord.com/oauth2/authorize?client_id=1274436972621987881).
You can either use it as is, or, if you have any security concerns with giving the bot the Administrator permission, you
can also disable it and just keep the other permissions active, though this may need additional setup, and may be prone
to unusual behaviours.

By adding TransforMate to your server, you agree to our
[Terms of Service](http://docs.transformate.live/legal/tos/), and to our
[Privacy Policy](http://docs.transformate.live/legal/privacy_policy/).

## Hosting TransforMate
To host your own TransforMate instance, you'll just need to clone this repo,
install the requirements, and create a `.env` file with the following contents:
```
# General bot configuration
BOT_TOKEN= # Your Discord Bot token
WEBHOOK_NAME= # The name of the Discord Webhooks your bot will create
BLOCKED_USERS="[user_id1, user_id2, ...]" # List of globally blocked users
USER_REPORTS_CHANNEL_ID= # Discord Channel ID to send user reports to
CACHE_PATH="cache" # Path for cache files, especifically TMUD data and server settings
MAX_REGEN_USERS=100 # Maximum number of users in a server allowed for /regen_server_tfs

# API settings
SECRET_KEY= # (see "Secret Key" below)
CLIENT_ID= # Your Discord app client id
CLIENT_SECRET= # Your Discord app secret
REDIRECT_URI= # Your Discord REDIRECT_URI
```

If all of these contents aren't present, an error will be thrown by the program
automatically.

You should also install all the requirements from `requirements.txt` and create the
cache directory and a `people` directory inside it, with, for example,
`mkdir cache/people`.

For more information or help, don't hesitate to ask in our Discord server!

### Secret Key
The Secret Key is required to encode user passwords using passlib. You can leave
this field empty if you aren't going to use the API features. Otherwise, to
populate it, run the command `openssl rand -hex 32` in your terminal to get a
randomly generated secret key. Do not share this key with anyone.

## Collaborating with the project
If you've had a cool idea, found a bug, or wanted to add some of your own code, 
feel free to open an issue or to do a pull request! You can also contact us in
our Discord server, where we have channels and forums specifically for this stuff!

## More info
[Discord Server](https://discord.gg/uGjWk2SRf6)

Inspired by the awesome BPTBot, made by Leroco.
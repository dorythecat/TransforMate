Admin commands are mean for admins to use to set up and moderate their servers.
They range from global channel and user blocks, regenerating files, and setting
up the server logs and settings.

!!! bug
    There's a known issue by which, oftentimes, the admin commands won't have
    the proper permissions set where they should only be usable by admins. Please
    check [this article](https://discord.com/blog/slash-commands-permissions-discord-apps-bots)
    from Discord to see how to properly set up slash command permissions in your
    server.

- [`/admin killhooks`](killhooks.md)
??? info
    This command will delete and force regeneration of all the bot's webhooks on
    the server. Use if any errors arise with the webhooks.

- [`/admin block_channel <channel>`](block_channel.md)
??? info
    Block a channel from being used by anyone in the server. Globally transformed
    users won't have any messages altered on these channels.

- [`/admin block_user [user]`](block_user.md)
??? info
    Blocks a user from using the bot inside the server.

- [`/admin block_category <category>`](block_category.md)
??? info
    Block a channel category from being used by anyone in the server. Globally
    transformed users won't have any messages altered on these channel categories.

- [`/admin list_blocked_channels`](list_blocked_channels.md)
??? info
    List all the globally blocked channels on the server.

- [`/admin list_blocked_users`](list_blocked_users.md)
??? info
    List all the globally blocked users on the server.

- [`/admin setup_logs <all> <edit> <delete> <transform> <claim>`](setup_logs.md)
??? info
    Set up your logs, either in a single channel or in different channels for
    different functions.
    !!! bug
        Some logs don't work properly as expected.

        See [this](https://github.com/dorythecat/TransforMate/issues/53)

- [`/admin update_settings <clean_logs> <image_buffer>`](update_settings.md)
??? info
    Update the settings to your server. Clean logs makes it so that deletion logs
    from other bots (Dyno bot, at the moment) get deleted to not clog up your log
    channel.Image buffer lets the bot store images in a channel which makes it more
    reliable most of the time.

- [`/admin regen_server_tfs <sure> <really_sure> <really_really_sure> <fully_sure>`](regen_server_tfs.md)
??? info
    Deletes all transformations for the current server.
    !!! danger
        This command is like the panic button of TransforMate. Only use when your
        server data is corrupt. he lost data is irrecoverable. Save your tfs.

- [`/admin regen_user_tfs [user] <sure> <really_sure>`](regen_user_tfs.md)
??? info
    Removes all the server data of a user and regenerates it next time they
    transform, akin to when the user leaves the server.
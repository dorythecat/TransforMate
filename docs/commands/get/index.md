Get commands allow you to see what a user's settings are. These are in a different
section to set and clear commands because their outputs and how they're read might
differ, so this is the best way to provide proper clarity on them.

- [`/get settings <user>`](settings.md)
??? info
    This command will show you what modifiers are turned on and which are turned
    off, and will also show you the stutter chance. It will NOT show you the
    biography, claim, or eternal status of a user.

- [`/get claim <user>`](claim.md)
??? info
    Displays whether the user is claimed or not, and, if they are, by whom.

- [`/get censors <user>`](censors.md)
??? info
    Displays a list of censored words and their replacements.

- [`/get sprinkles <user>`](sprinkles.md)
??? info
    Displays a list of the sprinkles a user has; with their individual chances.

- [`/get muffle <user>`](muffle.md)
??? info
    Displays a list of the muffles a user has active; with their individual chances.
    !!! bug
        There's a [known issue](https://github.com/dorythecat/TransforMate/issues/50),
        due to which, the alternative muffle settings won't show up on this list.

- [`/get prefixes <user>`](prefixes.md)
??? info
    Displays a list of the prefixes a user has active; with their individual chances.

- [`/get suffixes <user>`](suffixes.md)
??? info
    Displays a list of the suffixes a user has active; with their individual chances.

- [`/get bio <user>`](bio.md)
??? info
    Get the biography of a user.

- [`/get transformed`](transformed.md)
??? info
    Displays a list of all the transformed users in the current server, alongside
    the name of their transformed form.
    !!! bug
        Some of the mentions in the embedded message may display as <@number>.
        This is an error on the Discord client, and we can't do anything to fix
        it from our side, at least with how the command is currently set up.

        See [this](https://github.com/dorythecat/TransforMate/issues/51) feature
        request for a possible fix.

- [`/get image <user>`](image.md)
??? info
    Gives you the avatar image of a transformed user.

---

## The `extract_tf_data` function
For more information on this function, check the expanation given on the
[set and clear command page](../set_and_clear/index.md#the-extract_tf_data-function).
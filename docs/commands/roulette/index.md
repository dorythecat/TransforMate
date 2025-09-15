The "roulette" commands allow you to set up, manage, and use roulettes, which are a way
of randomly selecting a transformation with a varying chance. They can be used for things
from a simple chance game to a complex way of gambling away your identity.

The roulette works using TSF strings, so it's compatible with all of the features a TSF
string has to offer.

!!! note
    All the commands which take a `name` parameter default to giving the roulette the
    name "Default"

!!! warning
    You can only create one roulette, with up to 30 items, per server. This limit can be
    overridden by the bot's owner by adding the server ID to the `PATREON_SERVERS`
    environment variable. In the Official server, all patreon supporters can select a
    number of servers to override the limit, and how many they can do so for depends on
    their Patreon tier.

- [`/roulette create <name>`](create.md)
??? info
    Creates roulette for the server the command is executed in.

- [`/roulette remove <sure> <name>`](remove.md)
??? info
    Deletes the roulette with the given name.
    
    !!! warning
        This will delete all the items in the roulette, and they will be lost forever!

- [`/roulette add_item <item> <name>`](add_item.md)
??? info
    Adds an item to the roulette. If no item parameter is provided, it will ask for a
    string or file to be sent to fulfill the parameter.

- [`/roulette remove_item <item> <name>`](remove_item.md)
??? info
    Removes an item from the roulette.

- [`/roulette roll <name>`](roll.md)
??? info
    Rolls the given roulette and applies the transformation, removing it from the list
    of items afterward.

- [`/roulette info <name>`](info.md)
??? info
    Lists the roulette's information, including the items inside of it.
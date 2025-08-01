## Syntax
`/block channel <channel>`

- `channel`: A valid Discord Channel. If not provided, defaults to the current channel.

---

## Usage
This command is to be used when a user wants to block a channel so that they, and only
they, won't interact with the bot in said channels. This also means that, even if
you're transformed globally, your messages won't be altered on a blocked channel.

!!! note
    This command can also be used to unblock previously blocked channels, which will
    be automatically handled.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> CheckChannel[channel parameter provided]
    CheckChannel --> |False| AssignChannel[[channel = ctx.channel]]
    CheckChannel --> |True| BlockChannel[[Block the selected channel]]
    AssignChannel --> BlockChannel
    BlockChannel --> SendAnswer[[Send answer]]
```
## Syntax
`/admin block_channel <channel>`

- `channel`: A valid Discord Channel. If not provided, defaults to the current channel.

---

## Usage
This command is the same as [`/block channel`](../block/channel.md), but it applies to
the entire server, instead of a single user.

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
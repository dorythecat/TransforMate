## Syntax
`/admin block_category <category>`

- `category`: A valid Discord Channel Category. If not provided, defaults to the current channel's category.

---

## Usage
This command is the same as [`/block category`](../block/category.md), but it applies to
the entire server, instead of a single user.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> CheckCategory[category parameter provided]
    CheckCategory --> |False| AssignCategory[[category = ctx.channel. category]]
    CheckCategory --> |True| BlockCategory[[Block or unblock the selected category]]
    AssignCategory --> BlockCategory
    BlockCategory --> SendAnswer[[Send answer]]
```
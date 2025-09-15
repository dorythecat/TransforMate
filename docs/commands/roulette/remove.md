## Syntax
`/roulette create <sure> <name>`

- `sure`: A boolean that must be set to true to confirm the deletion of the
          roulette. This is to prevent accidental deletions.

- `name`: A string representing the name of the roulette to be created. This field
          defaults to "Default" if not provided.

---

## Usages
The command is used to remove an existing roulette in the server it is executed
in. The command will fail if no roulette with the given name exists.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> CheckBlocked[[Check if the user is blocked]]
    CheckBlocked --> CheckSure[[Check if 'sure' parameter is true]]
    CheckSure --> CheckName[[Check a roulette with that name exists]]
    CheckName --> RemoveRoulette[[Remove the roulette]]
    RemoveRoulette --> SendAnswer[[Send answer]]
```
## Syntax
`/roulette create <name>`

- `name`: A string representing the name of the roulette to be created. No two
          roulettes in the same server can have the same name. This field defaults
          to "Default" if not provided.

---

## Usages
The command is used to create a new roulette in the server it is executed in.
The command will fail if a roulette already exists and the server isn't registered
in the PATREON_SERVERS environment variable.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> CheckPatreon[[Check for patreon status and number of existing roulettes]]
    CheckPatreon --> CheckName[[Check a roulette with that name doesn't already exist]]
    CheckName --> CheckBlocked[[Check if the user is blocked]]
    CheckBlocked --> CreateRoulette[[Create the roulette]]
    CreateRoulette --> SendAnswer[[Send answer]]
```
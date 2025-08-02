## Syntax
`/set big <user>`

- `user`: A valid Discord User, defaults to the user executing the command. User to
          apply this modifier to.

---

## Usage
This command will apply the big text modifier to the specified user. This modifier
will make it so that every message the user speaks will be displayed as big text, by
using Discord's Markdown `#` modifier in front of the message.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> ExtractTfData[[extract_tf_data]]
    ExtractTfData --> CheckModifier[[Check that the modifier isn't already being applied]]
    CheckModifier --> ApplyModifier[[Apply the modifier]]
    ApplyModifier --> SendAnswer[[Send answer]]
```
## Syntax
`/set backwards <user>`

- `user`: A valid Discord User, defaults to the user executing the command. User to
          apply this modifier to.

---

## Usage
This command will apply the backwards text modifier, which inverts the order of the
letters on the message.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> ExtractTfData[[extract_tf_data]]
    ExtractTfData --> CheckModifier[[Check that the modifier isn't already being applied]]
    CheckModifier --> ApplyModifier[[Apply the modifier]]
    ApplyModifier --> SendAnswer[[Send answer]]
```
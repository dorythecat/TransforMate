## Syntax
`/clear all_fiels <user>`

- `user`: A valid Discord User, defaults to the user executing the command. User to
          clear modifiers from.

---

## Usage
Clears all modifiers from a transformed user.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> ExtractTfData[[extract_tf_data]]
    ExtractTfData --> ClearModifiers[[Clear all modifiers]]
    ClearModifiers --> SendAnswer[[Send answer]]
```
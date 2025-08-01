## Syntax
`/clear all_fiels <user>`

- `user`: A valid Discord User, defaults to the user executing the command.

---

## Usage
Clears all settings from a transformed user.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> ExtractTfData[extract_tf_data]
    ExtractTfData --> CheckValid[[Check if valid]]
    CheckValid --> ClearModifiers[[Clear all modifiers]]
    ClearModifiers --> SendAnswer[[Send answer]]
```
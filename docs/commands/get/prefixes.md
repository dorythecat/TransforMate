## Syntax
`/get prefixes <user>`

- `user`: A valid Discord User, defaults to the user executing the command. User to
          apply this modifier to.

---

## Usage
Lets you see the prefixes (and their respective chances) this user has active, if any.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> ExtractTfData[[extract_tf_data]]
    ExtractTfData --> SendAnswer[[Send answer]]
```
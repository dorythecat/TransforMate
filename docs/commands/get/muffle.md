## Syntax
`/get muffle <user>`

- `user`: A valid Discord User, defaults to the user executing the command. User to
          apply this modifier to.

---

## Usage
Lets you see the muffles (and their respective chances) this user has active, if any.
Also, displays alternative muffles in a separate embed.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> ExtractTfData[[extract_tf_data]]
    ExtractTfData --> CheckMuffles[[Check if there's muffles active]]
    CheckMuffles --> SendMuffles[[Send normal muffles]]
    SendMuffles --> CheckAlt[[Check if there's alternative muffles]]
    CheckAlt --> SendAlt[[Send alternative muffles]]
```
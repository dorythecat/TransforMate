## Syntax
`/set suffix [suffix] <chance> <user> <whitespace>`

- `suffix`: A string, to add to the suffix list.

- `chance`: An integer from 0 to 100, defaults 30. The chance, in percentage, of the
            suffix being used for a given message.

- `user`: A valid Discord User, defaults to the user executing the command. User to
          apply this modifier to.

- `whitespace`: A boolean, defaults true. Whether to include whitespace before the
                suffix, so it doesn't join the message before it.

---

## Usage
This command is used to add a suffix modifier, that is to say, a word or string that
will appear after certain messages, with a specific chance of it occurring.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> ExtractTfData[[extract_tf_data]]
    ExtractTfData --> AddWhitespace[[Add whitespace if necessary]]
    AddWhitespace --> ApplyModifier[[Apply the modifier]]
    ApplyModifier --> SendAnswer[[Send answer]]
```
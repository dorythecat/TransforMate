## Syntax
`/set censor [censor] [replacement] <user>`

- `censor`: A string, that will be censored and replaced.

- `replacement`: A string, that will replace the censored word.

- `user`: A valid Discord User, defaults to the user executing the command. User to
          apply this modifier to.

---

## Usage
This command will apply the censor text modifier, which will replace every instance
(case-insensitive) of the `censor` parameter with the `replacement` parameter,
effectively censoring said word. Multiple censored pairs can be set.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> ExtractTfData[[extract_tf_data]]
    ExtractTfData --> ApplyModifier[[Apply the modifier]]
    ApplyModifier --> SendAnswer[[Send answer]]
```
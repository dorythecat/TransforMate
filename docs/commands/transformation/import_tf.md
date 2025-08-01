## Syntax
`/import_tf <user>`

- `user`: A valid Discord User to import the transformation data to. If not provided,
          the user executing the command will be used.

---

## Usage
The `/import_tf` command is used in coordination with the [`/export_tf`](export_tf.md)
to save and load transformation data to and from files and/or strings.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> CheckUser[user parameter is provided]
    CheckUser --> |False| AssignUser[[user == ctx.user]]
    CheckUser --> |True| CheckBannedGlobal[[Check if user is globally banned]]
    AssignUser --> CheckBannedGlobal
    CheckBannedGlobal --> LoadData[[Load Data]]
    Database[(Database)] --> LoadData
    LoadData --> CheckBanned[[Check if the user and/or channel is banned in the server]]
    CheckBanned --> GetData[[Ask user for TSF data]]
    GetData --> CheckFile[Did they send a file?]
    CheckFile --> |True| ProcessFile[[Extract string from file]]
    CheckFile --> |False| TransformFunction[[transform_function]]
    ProcessFile --> TransformFunction
    TransformFunction --> ApplyModifiers[[Apply Modifiers]]
    ApplyModifiers --> SendAnswer[[Send answer]]
```

!!! note
    For more information on the TSF data format, see the documentation for the
    [`/export_tf`](export_tf.md#transformation-string-format) command.

!!! note
    For more information on `transform_function`, see the documentation for the
    [`/transform`](transform.md#the-transform_function) command.
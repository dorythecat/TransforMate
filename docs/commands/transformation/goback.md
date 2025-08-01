## Syntax
`/goback <user>`

- `user`: A valid Discord User. Defaults to the user executing the command.

---

## Usage
The `/goback` command can be used to return a user to their normal self, or, if
they have been transformed previously by another user or themselves, to turn them
back to their last form.

---

## Simplified internal logic
```mermaid
flowchart TD
    CommandReceived[Command Received] --> CheckUser[user parameter provided]
    CheckUser --> |False| AssignUser[[user == ctx.user]]
    CheckUser --> |True| LoadData[[Load Data]]
    Database[(Database)] --> LoadData
    AssignUser --> LoadData
    LoadData --> CheckTransformed[Is the user transformed?]
    CheckTransformed --> |False| CheckPrevious[[Check hat the user has a form to go back to]]
    CheckPrevious --> TransformPrevious[[Transform into previous form]]
    CheckTransformed --> |True| CheckEternal[Is the user eternally transformed?]
    CheckEternal --> |False| GoBack[[Go back to normal]]
    CheckEternal --> |True| CheckClaim[[Check that the user wanting to make the user go back has them claimed]]
    CheckClaim --> GoBack
    GoBack --> SendAnswer[[Send answer]]
    TransformPrevious --> SendAnswer
    SendAnswer --> Log[[Log the transformation, or undoing of such]]
```
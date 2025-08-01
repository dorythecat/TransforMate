## Syntax
`/(un)claim [user]`

- `user`: A valid Discord User to (un)claim.

---

## Usage
The `/claim` and `/unclaim` commands are used to claim and unclaim users, respectively.
A claimed user will only be able to be altered by the user that claimed them until
they're unclaimed or use the [`/safeword`](safeword.md) command.

---

## Simplified internal logic for `/claim`
```mermaid
flowchart TD
    CommandReceived[Command Received] --> CheckUser[[Check that the user has provided a valid Discord User that isn't themselves]]
    CheckUser --> SecondCheckUser[[Check that the chosen user is currently transformed]]
    SecondCheckUser --> LoadData[[Load Data]]
    Database[(Database)] --> LoadData
    LoadData --> CheckClaim[[Check that the user isn't already claimed]]
    CheckClaim --> Claim[[Claim the user]]
    Claim --> Log[[Log the claiming]]
```

---

## Simplified logic for `/unclaim`
```mermaid
flowchart TD
    CommandReceived[Command Received] --> CheckUser[[Check that the user has provided a valid Discord User that isn't themselves]]
    CheckUser --> SecondCheckUser[[Check that the chosen user is currently transformed]]
    SecondCheckUser --> LoadData[[Load Data]]
    Database[(Database)] --> LoadData
    LoadData --> CheckClaim[[Check that the user is claimed and that the owner is the current user]]
    CheckClaim --> Unclaim[[Unclaim the user]]
    Unclaim --> Log[[Log the unclaiming]]
```
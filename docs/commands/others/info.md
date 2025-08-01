## Syntax
`/info`

---

## Usage
The `/info` command is meant to be used just to get a small embedded command that
allows you see some info about the bot.

---

## Simpified internal logic
```mermaid
flowchart TD
    ReceiveCommand[Command received] --> SendEmbed[[Send embedded answer]]
```
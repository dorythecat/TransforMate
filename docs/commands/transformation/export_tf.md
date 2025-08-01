## Syntax
`/export_tf <user> <file>`

- `user`: A valid Discord User to export their transformation data. If not provided,
          the user executing the command will be used.

- `file`: A boolean, defaults true. If set to false, will return the plain string,
          otherwise returns a .tf file containing the string.

---

## Usage
The `/export_tf` command is used in coordination with the [`/import_tf`](import_tf.md)
to save and load transformation data to and from flies and/or strings.

---

## Simplified internal logic
```mermaid
flowchart TD
    CheckUser[user parameter is provided]
    CheckUser --> |False| AssignUser[[user == ctx.user]]
    CheckUser --> |True| CheckBannedGlobal[[Check if user is globally banned]]
    AssignUser --> CheckBannedGlobal
    CheckBannedGlobal --> LoadData[[Load Data]]
    Database[(Database)] --> LoadData
    LoadData --> CheckBanned[[Check if the user and/or channel is banned in the server]]
    CheckBanned --> PrepareString[[Make output string, see below for more info]]
    PrepareString --> CheckFile[file value]
    CheckFile --> |False| Output[[Output the result]]
    CheckFile --> |True| PrepareFile[[Encapsulate the string into a file]]
    PrepareFile --> Output
```

---

## Transformation String Format
The Transformation String Format (TSF) is a standard manner of encoding
transformation data, in an uncompressed, human-readable, and easy o edit manner. It
possesses various revisions, reflecting their equivalent version of the internal
TransforMate User Data (TMUD). The numbering starts as 0, where TSFv0 is compatible
with TMUDv14 (Both deprecated since v1.5.0).

!!! note
    The TMUD standard isn't documented as-is, and only exists inside the
    [`utils.py`](https://github.com/dorythecat/TransforMate/blob/main/src/utils.py)
    file of TransforMate, where the changelog is located too.

    If you would like for a TMUD documentation to be published, please
    [contact us](../../about.md#contact)

!!! note
    The TSF and TMUD format are both open and licencsed under the same
    [license](https://github.com/dorythecat/TransforMate/blob/main/LICENSE) as the bot,
    so you can use them freely for your projects, modify, and propose changes to them.

!!! warning
    TSF is backwards compatible with all previous versions, but TMUD is not.

The current specification, here described, is TSFv1.0, used since v1.5.0. The
documentation for v0 will not be released, but every version since v1 will be kept
as archive for future reference, with the expected behavior when importing said
versions of TSF data.

### v1.0 specification
This version counts with 15 parameters separated using the `;` character.
The parameters are displayed here, with an explanation where necessary, and divided
into categories for easier understanding. For more information on the modifiers, see
their respective [modifier page](../set_and_clear/index.md).

#### Basic data
This data is vital for the TSF data to be valid. Its the information that would
normally be given through the [`/transform`](transform.md) command, except for the
`brackets` parameter.

- `version`: This parameter encodes the TMUD version this TSF file was written as.
             Should always be 15 for TSFv1.0.

- `into`: Name of the transformed avatar.

- `image_url`: URL pointing to a valid image that serves as the transformed avatar's
               profile picture.

#### Boolean modifiers
These modifiers are always populated, as they represent the four boolean modifiers the
bot has available. `0` means False, `1` means True.

- `big`: Big text.

- `small`: Small text.

- `hush`: Hush messages (Discord spoiler).

- `backwards`: Invert text.

#### Basic modifiers
These modifiers ren't separated within themselves, since they are simple strings or
integers.

- `stutter`: Stutter modifier. Integer from 0 to 100.

- `proxy_prefix`: The prefix required to use the transformation in Tupper-like servers.

- `proxy_suffix`: The suffix required to use the transformation in Tupper-like servers.

- `bio`: A string with any length, containing a biography or any kind of user-defined
         information about the transformation.

#### Complex modifiers
These modifiers require a bit more of processing. All of them follow the same
pattern though; they are a dictionary, with elements separated with the `,`
character, and pairs denoted with the `|` character. For all except the `censor`
parameter, these are string-integer pairs, with the integer being a number from 0
to 100. In he case of he `censor` parameter, it's all string-string pairs.

- `prefix`: Strings that go before the text the user has sent, with a certain chance.

- `suffix`: Strings that go after the text the user has sent, with a certain chance.

- `sprinkle`: Strings that are randomly sprinkled between words that the user has sent.

- `muffle`: Strings that randomly replace words that the user has sent.

- `alt_muffle`: Strings that fully replace what the user has sent.

- `censor`: Replaces the first string of the pair for the second one. Case-insensitive.
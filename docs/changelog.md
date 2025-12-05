## v2.4.4
- Fixed [#93](https://github.com/dorythecat/TransforMate/issues/93).
- Fixed some minor issues with images.
- Fixed [#94](https://github.com/dorythecat/TransforMate/issues/94).

---

## v2.4.3
- Added a goodbye message when removing the bot from a server.
- Made the nickname changing option for transformations be false by default.
- Updated Terms of Service and Privacy Policy links.
- Made API-related .env variables optional.
- Improved regex errors.
- Made sprinkles be able to be after words instead of always before them.
- Made modifiers ACTUALLY work as floats.
- Added a few new glyphs to small text parsing.
- Greatly improved code structure and readability.
- Made censors be the last modifier to be applied.
- Fixed mentions on backwards text.
- Made big text and small text not interfere mutually.

---

## v2.4.2
- Added support for float values in chances and stutter, which fixes
  [#88](https://github.com/dorythecat/TransforMate/issues/88).
- Corrected a deadly typo.
- Fixed [#87](https://github.com/dorythecat/TransforMate/issues/87).
- Implemented [#85](https://github.com/dorythecat/TransforMate/issues/85).
- Fixed [#89](https://github.com/dorythecat/TransforMate/issues/89).
- Slightly improved replies.
- Implemented [#81](https://github.com/dorythecat/TransforMate/issues/81).
- Transformations no longer apply on announcements or forums channels.

---

## v2.4.1
- Non-regex censors are case-insensitive again.
- Fixed an issue with TSFv2.0 exporting.
- Fixed claiming and unclaiming not working properly.
- Fixed image URL checking not working properly.

---

## v2.4.0 (RegExpansion)
- Removed "brackets" or "Tupper-like" mode from the feature list.
- Added regex support on censors. (Use "/" before the censor to enable it
  on a per-word basis, or use "-/" to enable it on the entire message.)
  (Fulfills [#77](https://github.com/dorythecat/TransforMate/issues/77))
- Bumped TMUD format to v16.
- Updated TSF to v2.0, to match the new TMUD format.
- Fixed [#82](https://github.com/dorythecat/TransforMate/issues/82)
- Made censors no longer be forced to lowercase.
- Slightly improved performance and structure.
- Added [#83](https://github.com/dorythecat/TransforMate/issues/83),
  and extended it to all modifiers.
- Removed per-channel transformations.
- Added an error on too-long messages when transformed.
- We now actually check if the image URL provided is reachable.
- Improved message editing.
- Improved `/info` command.

---

## v2.3.1
- Fixed [#65](https://github.com/dorythecat/TransforMate/issues/65)
- Fixed [#66](https://github.com/dorythecat/TransforMate/issues/66)
- Fixed [#67](https://github.com/dorythecat/TransforMate/issues/67)
- Fixed [#68](https://github.com/dorythecat/TransforMate/issues/68)
- Fixed [#69](https://github.com/dorythecat/TransforMate/issues/69)
- Fixed [#64](https://github.com/dorythecat/TransforMate/issues/64)
  (therefore [#79](https://github.com/dorythecat/TransforMate/issues/79) as well)
- Fixed a bug where the bot would not properly work on Windows systems.
- Made export_tf output be in code block format.
- Fixed a bug where the bot would not properly discern if a user was tfed or
  not when using the "who is it" reaction
- Fixed a few minor bugs.

---

## v2.3.0 (Blockade)
- Added [`/block category`](commands/block/category.md) command.
- Added [`/admin block_category`](commands/admin/block_category.md) command.
- Messages can now be escaped with `\`.
- Fixed a bug where censors would not work properly with special characters.
- Fixed a bug where claimed users would lose that status upon having a transformation
  imported upon them.

---

## v2.2.1
- Fixed a few minor bugs, and an undocumented bug by which people
  would not properly get tfed randomly.

---

## v2.2.0
- Fixed [#55](https://github.com/dorythecat/TransforMate/issues/55)
- Fixed [#61](https://github.com/dorythecat/TransforMate/issues/61)
- Updated TSF to v1.2, which fixes [#56](https://github.com/dorythecat/TransforMate/issues/56)

## v2.1.1
- Fixed a few bugs, of all kinds.

---

## v2.1.0
- Fixed the ability to use the alternative TF method when transformed and
  trying to transform others
- Fixed a few minor bugs.

---

## v2.0.0 (TransforWeb)
- Added [TransforWeb](http://www.transformate.live/) and the accompanying
  [TransforMate API](http://api.transformate.live/) to production, allowing
  for a lot of new features, like the TSF Editor.
- Improved the performance of the bot slightly and fixed some minor bugs.

---

## v1.6.2
- Fixed TSF data documentation.

---

## v1.6.1
- Fixed Issues [#49](https://github.com/dorythecat/TransforMate/issues/49) and
  [#50](https://github.com/dorythecat/TransforMate/issues/50). Updated wiki to
  reflect these changes.

---

## v1.6.0 (DocuMate)
- Added documentation
- Altered the [Terms of Service](legal/tos.md) and
  [Privacy Policy](legal/privacy_policy.md).
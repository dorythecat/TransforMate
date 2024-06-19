# Transformate Help

## Description

This is a simple markdown file that will be transformed into a HTML file.


## Commands

### Basics

#### **/transform** (user) (into) (image_url) (channel)

- **User**: The user you want to transform. (optional, defaults to the user who sent the command)
- **Into**: The transformation you want to do. (optional)
- **Image URL**: The URL of the image you want to transform the user into. (optional, defaults to user avatar)
- **Channel**: The channel you want the transformation to be sent to. (optional, defaults to the entire server)

This command will transform the user into the image you provide with the name you provide. If you don't provide a user, it will default to the user who sent the command. 

If no into is provided, the bot will send a follow-up message asking for the transformation you want to do. In this message you just write the name and attach an image. Due to bot limitations, you can't attach an image to the original command and transformed users can't transform others by attaching an imaging to the follow-up message (the image will get deleted and the url will not work anymore due to the deletion).

If you don't provide an image URL, it will default to the user's avatar. If you don't provide a channel, it will default to the entire server.

#### **/goback** (user)

- **User**: The user you want to revert the transformation of. (optional, defaults to the user who sent the command)

This command will revert the transformation of the user you provide. If you don't provide a user, it will default to the user who sent the command. If you are untransformed, but were previously transformed, you can use this command to revert the transformation to the previous one (this may have unexpected results).

#### **/safeword**

Use this to get out of any claims and eternals you may be in. **This command is to be used in the case of uncomfortable situations. Remember that you can always block the bot from transforming you and that safe, sane, and consensual play is the most important thing.** If you are in a situation where you are uncomfortable, please use this command and consider using **/report** to report the user who made you uncomfortable.

### Set

<!-- censor, muffle, big, eternal, hush, prefix, small, suffix, sprinkle -->

The set commands are to change settings for a user's transformation, editing their text in often humorous ways. These settings will persist across transformations until changed again.

#### **/set censor** (user) (censored_text) (replacement_text)

- **User**: The user you want to set the censor for. (optional, defaults to the user who sent the command)
- **Censored Text**: The text you want to censor. (required)
- **Replacement Text**: The text you want to replace the censored text with. (required)

This command will set the censor for the user you provide. If you don't provide a user, it will default to the user who sent the command. The censor will replace the censored text with the replacement text in the user's messages. Example: `/set censor @user badword ****`.

"badword" will be replaced with "****" in the user's messages.

#### **/set muffle** (user) (muffled_text) (chance)

- **User**: The user you want to set the muffle for. (optional, defaults to the user who sent the command)
- **Muffled Text**: The text you want to muffle. (required)
- **Chance**: The chance that the text will be muffled. (optional, defaults to 30%, limited to 0-100)

This command will set the muffle for the user you provide. If you don't provide a user, it will default to the user who sent the command. The muffle will muffle the text in the user's messages. Example: `/set muffle @user badword 50`. 

Words in the user's messages will have a 50% chance of being turned into "badword".

**You can set multiple muffle words for a user. That way you can have a variety of words that will be replacing the original text.**

#### **/set eternal** (user)

- **User**: The user you want to set the eternal for. (optional, defaults to the user who sent the command)

This command will make the user's transformation eternal. If you don't provide a user, it will default to the user who sent the command. Eternals will not be reverted by the **/goback** command. Remember that you can always use **/safeword** to get out of any claims and eternals you may be in.

#### **/set big** (user)

- **User**: The user you want to set the big for. (optional, defaults to the user who sent the command)

This command will make every message the user sends as big text. If you don't provide a user, it will default to the user who sent the command. Big text is just '# ' in front of the message.

#### **/set small** (user)

- **User**: The user you want to set the small for. (optional, defaults to the user who sent the command)

This command will make every message the user sends as small text. If you don't provide a user, it will default to the user who sent the command. Small text are just small versions of unicode characters. It is recommended to avoid this command when in a server with visually impaired users as screen readers will have a hard time reading the text.

#### **/set hush** (user)

- **User**: The user you want to set the hush for. (optional, defaults to the user who sent the command)

This command will surround the user's messages with '||'. If you don't provide a user, it will default to the user who sent the command. This will make the user's messages hidden until you uncover them, a good compromise for muting a user without actually muting them.

#### **/set backwards** (user)

- **User**: The user you want to set the backwards for. (optional, defaults to the user who sent the command)

This command will make the user's messages backwards. If you don't provide a user, it will default to the user who sent the command.

#### **/set prefix** (user) (prefix) (chance)

- **User**: The user you want to set the prefix for. (optional, defaults to the user who sent the command)
- **Prefix**: The text you want to prefix the user's messages with. (required)
- **Chance**: The chance that the prefix will be added to the user's messages. (optional, defaults to 30%, limited to 0-100)

This command will set the prefix for the user you provide. If you don't provide a user, it will default to the user who sent the command. The prefix will add the prefix to the user's messages. Example: `/set prefix @user prefix 50`.

The user's messages will have a 50% chance of having "prefix" added to the beginning of them.

You can set multiple prefixes for a user. That way you can have a variety of prefixes that will be added to the original text.

#### **/set suffix** (user) (suffix) (chance)

- **User**: The user you want to set the suffix for. (optional, defaults to the user who sent the command)
- **Suffix**: The text you want to suffix the user's messages with. (required)
- **Chance**: The chance that the suffix will be added to the user's messages. (optional, defaults to 30%, limited to 0-100)

This command will set the suffix for the user you provide. If you don't provide a user, it will default to the user who sent the command. The suffix will add the suffix to the user's messages. Example: `/set suffix @user suffix 50`.

The user's messages will have a 50% chance of having "suffix" added to the end of them.

You can set multiple suffixes for a user. That way you can have a variety of suffixes that will be added to the original text.

#### **/set sprinkle** (user) (sprinkle) (chance)

- **User**: The user you want to set the sprinkle for. (optional, defaults to the user who sent the command)
- **Sprinkle**: The text you want to sprinkle the user's messages with. (required)
- **Chance**: The chance that the sprinkle will be added to the user's messages. (optional, defaults to 30%, limited to 0-100)

This command will set the sprinkle for the user you provide. If you don't provide a user, it will default to the user who sent the command. The sprinkle will add the sprinkle to the user's messages. Example: `/set sprinkle @user sprinkle 50`.

The user's messages will have a 50% chance of having "sprinkle" added to them, this chance is determined between each word in the message.

You can set multiple sprinkles for a user. That way you can have a variety of sprinkles that will be added to the original text.

#### **/set bio** (user) (biography)

- **User**: The user you want to set the bio for. (optional, defaults to the user who sent the command)
- **Biography**: The text you want to set as the user's bio. (required)

This command will set the bio for the user you provide. If you don't provide a user, it will default to the user who sent the command. The bio will be shown when you use the **/get bio** command. Example: `/set bio @user "This is a bio."`. This is a good way to give a little bit of information about the user and what they are transformed into for roleplay purposes.

### Get

The get commands are to get the settings for a user's transformation, showing the current settings for the user.

#### **/get censors** (user)

- **User**: The user you want to get the censors for. (optional, defaults to the user who sent the command)

This command will get the censors for the user you provide. If you don't provide a user, it will default to the user who sent the command. This will send an embed with the censors for the user, showing the censored text and the replacement text.

#### **/get muffle** (user)

- **User**: The user you want to get the muffle for. (optional, defaults to the user who sent the command)

This command will get the muffle for the user you provide. If you don't provide a user, it will default to the user who sent the command. This will send an embed with the muffle for the user, showing the muffled text and the chance.

#### **/get prefixes** (user)

- **User**: The user you want to get the prefixes for. (optional, defaults to the user who sent the command)

This command will get the prefixes for the user you provide. If you don't provide a user, it will default to the user who sent the command. This will send an embed with the prefixes for the user, showing the prefix and the chance.

#### **/get suffixes** (user)

- **User**: The user you want to get the suffixes for. (optional, defaults to the user who sent the command)

This command will get the suffixes for the user you provide. If you don't provide a user, it will default to the user who sent the command. This will send an embed with the suffixes for the user, showing the suffix and the chance.

#### **/get sprinkles** (user)

- **User**: The user you want to get the sprinkles for. (optional, defaults to the user who sent the command)

This command will get the sprinkles for the user you provide. If you don't provide a user, it will default to the user who sent the command. This will send an embed with the sprinkles for the user, showing the sprinkle and the chance.

#### **/get settings** (user)

- **User**: The user you want to get the settings for. (optional, defaults to the user who sent the command)

This command will get the settings for the user you provide. If you don't provide a user, it will default to the user who sent the command. This will send an embed with the settings for the user, showing the censors, muffle, prefixes, suffixes, and sprinkles.


#### **/get bio** (user)

- **User**: The user you want to get the bio for. (optional, defaults to the user who sent the command)

This command will get the bio for the user you provide. If you don't provide a user, it will default to the user who sent the command. This will send an embed with the bio for the user, showing the user and what they are transformed into as well as a blurb about the user.

#### **/get transformed**

This command will get the transformed users in the server. This will send an embed with the transformed users in the server, showing the user and what they are transformed into.

### Clear

The clear commands are to clear the settings for a user's transformation, removing the settings for the user.

#### **/clear censor** (user) (censor_word)

- **User**: The user you want to clear the censor for. (optional, defaults to the user who sent the command)
- **Censor Word**: The word you want to clear the censor for. (optional, if not provided, clears all censors)

This command will clear the censor for the user you provide. If you don't provide a user, it will default to the user who sent the command. If you provide a censor word, it will clear that censor word. If you don't provide a censor word, it will clear all censor words.

#### **/clear muffle** (user) (muffle_word)

- **User**: The user you want to clear the muffle for. (optional, defaults to the user who sent the command)
- **Muffle Word**: The word you want to clear the muffle for. (optional, if not provided, clears all muffle words)

This command will clear the muffle for the user you provide. If you don't provide a user, it will default to the user who sent the command. If you provide a muffle word, it will clear that muffle word. If you don't provide a muffle word, it will clear all muffle words and disable the muffle.

#### **/clear eternal** (user)

- **User**: The user you want to clear the eternal setting for. (required)

This command will clear the eternal setting for the user you provide. If the user is not eternal, it will do nothing.

#### **/clear big** (user)

- **User**: The user you want to clear the big text setting for. (optional, defaults to the user who sent the command)

This command will clear the big text setting for the user you provide. If you don't provide a user, it will default to the user who sent the command.

#### **/clear small** (user)

- **User**: The user you want to clear the small text setting for. (optional, defaults to the user who sent the command)

This command will clear the small text setting for the user you provide. If you don't provide a user, it will default to the user who sent the command.

#### **/clear hush** (user)

- **User**: The user you want to clear the hush text setting for. (optional, defaults to the user who sent the command)

This command will clear the hush text setting for the user you provide. If you don't provide a user, it will default to the user who sent the command.

#### **/clear backwards** (user)

- **User**: The user you want to clear the backwards text setting for. (optional, defaults to the user who sent the command)

This command will clear the backwards text setting for the user you provide. If you don't provide a user, it will default to the user who sent the command.

#### **/clear prefix** (user) (prefix)

- **User**: The user you want to clear the prefix for. (optional, defaults to the user who sent the command)
- **Prefix**: The prefix you want to clear. (optional, if not provided, clears all prefixes)

This command will clear the prefix for the user you provide. If you don't provide a user, it will default to the user who sent the command. If you provide a prefix, it will clear that prefix. If you don't provide a prefix, it will clear all prefixes.

#### **/clear suffix** (user) (suffix)

- **User**: The user you want to clear the suffix for. (optional, defaults to the user who sent the command)
- **Suffix**: The suffix you want to clear. (optional, if not provided, clears all suffixes)

This command will clear the suffix for the user you provide. If you don't provide a user, it will default to the user who sent the command. If you provide a suffix, it will clear that suffix. If you don't provide a suffix, it will clear all suffixes.

#### **/clear sprinkle** (user) (sprinkle)

- **User**: The user you want to clear the sprinkle for. (optional, defaults to the user who sent the command)
- **Sprinkle**: The sprinkle you want to clear. (optional, if not provided, clears all sprinkles)

This command will clear the sprinkle for the user you provide. If you don't provide a user, it will default to the user who sent the command. If you provide a sprinkle, it will clear that sprinkle. If you don't provide a sprinkle, it will clear all sprinkles.

#### **/clear bio** (user)

- **User**: The user you want to clear the bio for. (optional, defaults to the user who sent the command)

This command will clear the bio for the user you provide. If you don't provide a user, it will default to the user who sent the command.

#### **/clear all_fields** (user)

- **User**: The user you want to clear all fields for. (optional, defaults to the user who sent the command)

This command will clear all fields for the user you provide. If you don't provide a user, it will default to the user who sent the command.

### Admin

These commands will only work for those with the `Manage Server` permission.

#### **/admin block_channel** (channel_id)

- **Channel ID**: The ID of the channel you want to block. (Optional)

This command will block the channel from having any transformations done inside of it, or any users typing there to have their messages transformed. Useful for Out-Of-Character channels.

#### **/admin block_user** (user)

- **User ID**: The ID of the user you want to block. (Required)

This command will block the user from having any transformations done to their messages. Useful for users who don't want their messages transformed or for users who are abusing the bot.

#### **/admin killhooks**

This command will remove all webhooks from the server, this is useful if you are having issues with the bot and need to reset the webhooks. This will not remove the bot from the server. You shouldn't need to use this command unless something has gone wrong.

### Important Advanced Commands

#### **/report** (user) (reason)

- **User**: The user you want to report. (required)
- **Reason**: The reason you are reporting the user. (required)

This command will report the user you provide. If you don't provide a user, it will default to the user who sent the command. This will send a report to the channel listed in env, for the main instance of the bot, it will send to a hidden channel in the Transformate server. This is to report users who are making you uncomfortable or are abusing the bot. This is a serious command and should not be used lightly. If the report is substantiated, the user reported will be **banned** from using the bot.

#### **/claim** (user)

- **User**: The user you want to claim. (required)

This command will claim the user you provide. If you don't provide a user, it will default to the user who sent the command. This will make it so that only you can transform the user you claimed. This is useful for roleplay purposes and for making sure that you are the only one who can transform a user. This can be per channel or server-wide.

#### **/unclaim** (user)

- **User**: The user you want to unclaim. (required)

This command will unclaim the user you provide. If you don't provide a user, it will default to the user who sent the command. This will make it so that anyone can transform the user you unclaimed. This is useful for roleplay purposes and for making sure that you are not the only one who can transform a user. This can be per channel or server-wide.

#### **/ping**

This command will send a message to the bot and the bot will respond with "Pong!" if it is working correctly. This is useful for checking if the bot is online and responding, as well as checking the latency of the bot.

#### **/help**

This command will start a message tree that will guide you through the commands available to you. This is useful for finding out what commands are available and how to use them.

#### **/invite**

This command will send you an invite link to add the bot to your server. This is useful for adding the bot to your server and getting started with the bot.

#### **/info**

This command will send you information about the bot, including the version, the developers, and the source code.
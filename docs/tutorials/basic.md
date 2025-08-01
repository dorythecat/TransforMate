# Basic TransforMate Tutorial
In this tutorial, you will learn how to operate the basics of TransforMate, plus a
few handy tricks to help you transform yourself and others in an approachable and
fun manner!

Before starting, go to a Discord server where you can test the bot's
functionalities without disturbing other users. If you need to find such a place,
you can always use the `public-bot-tests` channel in the awesome
[Official TransforMate Discord Server](https://discord.gg/uGjWk2SRf6), where you
can also freely ask for help to our great team if you get stuck at any point of
this guide.

!!! note
    Remember that Discord provides an autocomplete feature, and that, when
    inputting the command, you can select the field you want to fill out through
    this very autocomplete feature. When you're still learning, autocomplete will
    be your very best friend.

## Learning to use the `/transform` command
This command will be your most versatile tool, since you will constantly be using
it, alongside its partner, the `/goback` command. In this section, you'll learn to
transform yourself, but remember you can always change other users by using the
`user` parameter.

Go to your testing channel, and type the `/transform` command. You will see a lot
of options, but the one that interests us at this moment is the `into` parameter.
For this test, set it to whatever you like, for example, "Test1"; and send the
command.

And that's it! You have transformed yourself! Try typing in the chat, and see how
you're now transformed!

!!! note
    You will easily be able to tell that your avatar when transformed is your normal
    user avatar. That's because we haven't provided an `image_url` field, so the bot
    has defaulted to your profile picture for your avatar.

Now that you're transformed, you have to know how to go back, don't you? Try
executing the `/goback` command, without filling out any of the arguments.
Ta-dah! Now you're back to normal! Wasn't that easy?

Once you're back to normal, if you want to return to your previous form, you just
need to send the `/goback` command once more, and the bot will turn you into
whatever you were last time you went back to normal!

??? question "Exercise 1"
    You have now transformed yourself for the first time. But, as we've seen, if
    we don't provide an `image_url` parameter, we default to just having our
    profile picture as our avatar. How can we change this by using the `ìmage_url`
    parameter?

??? tip "Answer 1"
    The `image_url` parameter takes as input any URL that serves an image. This
    means we could use any image, in theory. To do so, paste it into a Discord
    channel, right-click on it, and select "Copy Image URL". This URL can then be
    given as the `image_url` parameter for your transformation. Voilà! We have an
    avatar image that isn't your profile picture!

    But, is there an easier method, that doesn't require us to fool around and
    paste images into Discord...?

### The "simplified" command
The full `/transform` command is designed to be very versatile and compact, but it
can sometimes be very bothersome having to copy image URLs, or to remember what
each option does.

This is why the "simplified" mode exists! Simply execute `/transform`, without any
parameters (unless you want to transform another user, in which case you should
populate the `user` parameter), and wait for the bot to respond.

The bot will ask you what you want to transform into. Now, you can simply reply
with the name of what you want to transform into, BUT, and this is where the magic
happens; if you attach an image to the message, the bot will automatically set it
as your avatar! No need for pesky URLs!

---

## Playing with settings
There are a lot of settings you can configure for a transformation with
TransforMate. If you want to know all of the settings you can configure, check out
the [set and clear commands index](../commands/set_and_clear/index.md).

For the examples given here, we've decided to use the censor, muffle, hush, and
stutter settings, which describe the types of settings the bot has available in a
pretty good manner, without exceeding what's realistically possible to easily
learn in this tutorial.

Let's start by the easiest kind of setting: On-off settings. Currently, these are
the big, small, hush, and backwards settings. Try and hush your messages by using
`/set hush`. When you type next time, it will be a spoiler, "hushing" you. Try it!

??? question "Exercise 2"
    Can you make your text small, and disable hushing now?

??? tip "Answer 2"
    To make your text small, you just need to use the `/set small` command, and, to
    stop being hushed, just use `/clear hush`!

That is the most basic type of setting you can modify, but we still have a long way
to go! Let's try with numeric settings now! At the moment, the only setting of this
kind that's available in TransforMate is he stutter setting. Let's try and make you
stutter with a 20% chance. For this, you'll need to use the `/set stutter <chance>`
command. Can you manage to do it?

Once you've figured it out, try typing a bit of text and see if you stutter a bit!

!!! note
    Remember, any time you want to check your current settings you can use
    `/get settings`, and [the other `/get` commands](../commands/get/index.md) to
    see your settings in detail!

You're doing great! We're halfway there to learn all the kinds of modifiers you
can use with TransforMate, and being able to transform yourself and others with
ease!

Now, it's time to introduce chance-based modifiers. These can have a lot of
different values for the same user. Let's say, for example, that we have a user,
lets call him John. John has been muffled by his friends, with three different
words. This means those three words will be substituting some of his words with
a random chance.

For this example, let's say the words are "cheese", "*squeak*", and
"great beyond", and that their chances to occur are, in order, 20%, 50%, and 3%.
How would you se this up?

Well, to do so, we would need three commands:

```
/set muffle chese 20
/set muffle *squeak* 50
/set muffle "great beyond" 3
```

!!! warning
    You should be aware that a multi-word parameter like "great beyond" works
    because Discord treats everything you write inside a parameter like a single
    thing, so, in practice, you don't need the surrounding quotes, used here to
    tell you that it goes al together in the same parameter. If you keep the
    quotes, they will become part of the final substitution!

Now, you might have noticed that we have messed up the word "cheese" and written
"chese" instead! We could always do `/clear muffle`, to clear all of the muffle
settings we have just set up, but, specially for more complex transformations,
that is a chore we shouldn't really have to go through!

Instead, try using `/clear muffle chese`! This will only delete the erroneous
muffle, and you'll write half as much! Try it!

Now, you have learnt the three "basic" types of modifiers, and you can use what
is basically the entire set of modifiers the bot has to offer. The only two you
have left to learn are the biography, and the censor modifiers!

??? question "Exercise 3"
    Can you set a biography for your current transformation? Try to be creative!

??? hint "Answer 3"
    Using the `/set bio` command you can see a biography as long as you want
    (Discord's message length restrictions apply).

    And an exra trick: You can use the `\n` escape character to make a line jump!

Now, the censor command isn't all that different from the chance-based modifiers
like muffle, but it differs in a very important aspect. Censors differ from these
in that they don't trigger based on a random chance, but based on a keyword.

For example, let's say we censor the word "four" to say "five". This means that
EVERY TIME the transformed user says the word "four", they will say "five" instead,
for example, "two plus two is four" will become "two plus two is five".

To set a censor, we use a similar syntax as for chance-based modifiers. For the
above example, for example, we'd use `/set censor four five`. See? Easy right?
Try it out!

!!! example "Now what?"
    You have learnt how to use the basics of modifiers! Now you should try other
    modifiers around, like the sprinkle or suffix. Try the alternative muffle,
    that muffles entire messages instead of words, if you want! You're free to
    experiment with the bot and learn from that! Have fun!

# Exporting and importing transformations
Sometimes, you make a really great transformation, and you'd like to either share
it with your friends; or just to save it for later whilst you experiment with some
new transformation ideas.

To do this, you can export and import transformations to either text files; or
easy to share (and edit) strings. This not only allows you to save and share
transformation, but also to edit transformation data without needing to use a
single command for every single thing you want to change about a transformation.
To know more about how to edit these files, check out the full documentation for
the [`/export_tf` and `/import_tf`](../commands/transformation/import_and_export.md)
commands, where you'll find a full explanation oh how these strings (and the files)
work, so you can edit them to your liking.

For now, in this tutorial, we will learn the basics on how to import and export
your transformation data. For this, you'll need to be transformed. Choose a form
that has a few modifiers applied, so that you can see how they're kept completely
through exporting and re-importing it.

Now, execute he `/export_tf` command. You will get a file, with the same name as
your transformation. This file contains all the information about your
current transformation, that can be used to transform yourself once again, or to
transform others.

!!! note
    Transformation files do not store any information about the user that created
    them, the time they were created at, where they were created at, or how they
    were created. If no external information is given, transformation files are
    effectively untraceable, so you don't have to worry about people doxxing you
    from a transformation file, don't worry!

Now, why don't you try transforming into something else? Make sure it's different
from what you just transformed out of, but don't worry about making a complex
transformation, just enough to see the difference.

Now, use the `/import_tf` command. The bot will ask you for a transformation to
use to transform you. You can use a file or a string here. Since we got a file,
just send a message with the file attached. And... That's it! Now, if you check
your settings, you'll see that you're on the form you were before, all the same!
Pretty awesome, right?

You can store these files in Discord itself, or on any other storage platform,
including your own computer! But not everyone has access to a computer, much
less at all times, so, to make storing transformation easier, you can always get
a string by setting the `file` parameter of `/export_tf` to false! This will
give you an easy-to-copy string that you can save in your notes app or in a
Discord channel, so it's easier to copy and use!

# Claiming and eternally transforming other users
For this part of the tutorial, you will need a [good friend](https://xkcd.com/513/)
to be your [test subject](https://xkcd.com/749/). Be sure they're fine with being
claimed and eternally transformed for a few minutes so you can learn the basics of
these features.

!!! warning
    Remember, kids: Consent is important

Now, transform your friend into something they enjoy being. Once you're done, use
the `/claim` command to claim them. If you do so successfully, the bot will let
you know. Now, you're the "owner" of your friend. This means you're the only one
allowed to transform them and modify their settings. They themselves can still
go back to their normal form, though.

!!! danger
    If at any point you feel uncomfortable as the claimed user, there's a command
    to free yourself: `/safeword`. If you feel like your partner has abused you
    or didn't consent, try to resolve the issue with the server's moderation
    team. If this doesn't work, use the `/report` command, or send the word
    "report" to the bot's DMs.

To avoid them escaping their transformative cage, you'll have to close the door
with the `/set eternal` command. Now, they'll be eternally transformed into
whatever form you have chosen for them, until you decide to free them.

!!! note
    Remember to use `/clear eternal` and/or `/unclaim` when you are done with
    your partner, so they can be free once again.

# Conclusion
Well, you have done great! Now you know how to use all the basic features of the
bot! We've only really skipped two features in all of this tutorial. The first
of these is the per-channel transformations, but you should be able to figure
those out with the information in this tutorial.

!!! hint
    Check out the `channel` parameter in the `/transform` command.

There's only really one thing you've missed, and that's the twinning and merging
capabilities of the bot. These are very specific and kinda fiddly. Check out the
[Basic Twinning Tutorial](twinning.md) to learn more about this feature!

We'd recommend you experiment a bit with the bot, to get your bearings, and,
always remember to have fun and let others have their own fun!
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
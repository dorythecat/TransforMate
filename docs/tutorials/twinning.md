Twinning, at least here, refers to when you copy a user's transformation and apply
it to yourself, effectively becoming a copy of them. Merging is the same concept,
but you'll become *literally the same;* that includes your messages merging,
so you cannot even be differentiated from one another!

We recommend starting by checking out the [Basic TransforMate Tutorial](basic.md).
If you already come from there, you'll probably be thinking "can't I just do this
by exporting my transformation and importing it onto another user, or viceversa?",
and, yeah, you'd be right, you *could* do that... Why would you, though? Unless you
want to edit the file or string, that limits you to only merging, and, besides, you
can do all that with just the `/transform` command.

You might have noticed this command has a `copy` and a `merge` parameter, right?
The `copy` parameter takes a user as an input, and it will copy the data from that
user into whatever user you choose to transform, including yourself. If you set
the `merge` value to be true, you'll merge with them. Easy, isn't it?

!!! warning
    When you don't merge two users, the way the bot actually handles this is by
    adding an invisible character to the end of the name on the newly transformed
    user.

    This means that, if you want to transform, let's say, three users, you would
    need to first do the original transformation, then twin that one onto another,
    and then, twin the one you just twinned into the other user. Otherwise, the
    second and third users will effectively be merged!

But wait! There's an extra feature awaiting you in this command! You can still
provide all the other parameters the `/transform` command takes, like `into` and
`image_url`, and the bot will automatically change the copied values to reflect
your changed data. This allows you to do some cool stuff, like twinning with very
slight changes to he newly transformed user. Try it out!
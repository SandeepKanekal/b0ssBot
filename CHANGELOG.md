# Changelog for b0ssb0t #

# Overall #
+ Specific errors such as missing required arguments are now mentioned explicitly.
+ General errors are highlighted to make it more visible
+ Owner only commands are now stored in a different Cog
+ Slash commands have been added for commands which require multiple arguments
+ A module named `tools` is now used to store commonly called functions

# Events #
+ Markdown syntax for embedding links in text is now detected and, a webhook is sent after deleting the original message.

# Fun #
+ The quote command now sends the user to wait if the API is overloaded.
+ The view mode in the message_response command now checks accepts a message/response parameter

# Help #
+ The command usage field now calls the `command.usage` for its value.

# Moderation #
+ Modlogs now detect voice state updates and bulk message deletions.
+ A small bug which made `'` to be visible as `''` was fixed.

# MISC #
+ Since a member can be of multiple strings, the `member` argument in the avatar command now is a multiline string.

# Info #
+ Since a member can be of multiple strings, the `member` argument in the userinfo command now is a multiline string.
+ The changelog command will not copy everything from this file.

# Internet #
+ The youtubesearch command, has a button with the label 'Watch Video' will now reply with the video link instead of opening the link in the browser.

# Music #
+ The lyrics command's response's title now is the title of the song instead of the query. However, the query is visible as the footer.
+ Custom error classes

# Util #
+ No changes

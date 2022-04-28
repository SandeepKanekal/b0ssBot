# Changelog for b0ssb0t #

# Overall #
+ Slash commands have been added to the bot.

# Events #
+ Markdown syntax for embedding links in text is now detected and, a webhook is sent after deleting the original message.

# Fun #
+ The messageresponse command has been transferred to slash commands since it is easier with slash commands.

# Help #
+ The command usage field now calls the `command.usage` for its value.
+ A field showing the slash commands has been added.

# Moderation #
+ Modlogs now detect voice state updates and bulk message deletions.
+ A small bug which made `'` to be visible as `''` was fixed.
+ Edit messages in modlogs now shows even if there are embeds in the message.
+ Avatar updates are shown differently. Previous avatar is the thumbnail, and the new avatar is the image.

# MISC #
+ Since a member can be of multiple strings, the `member` argument in the avatar command now is a multiline string.

# Info #
+ Since a member can be of multiple strings, the `member` argument in the userinfo command now is a multiline string.
+ The changelog command will not copy everything from this file.

# Internet #
+ The youtubenotification, hourlyweather commands have been transferred to slash commands since it is easier with slash commands.

# Music #
+ The lyrics command's response's title now is the title of the song instead of the query. However, the query is visible as the footer.
+ Custom error classes.

# Util #
+ No changes.

# Slash #
+ Addition the code command.
+ The code command now sends `.py` files instead of `.txt` files.

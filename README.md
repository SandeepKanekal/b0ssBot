# b0ssBot
A discord bot for fun, moderation, and music! Adding features everyday

# Prerequisites
+ py-cord 2.0+ (https://github.com/Pycord-Development/pycord)
+ Flask
+ FFmpeg (Add FFmpeg to PATH in Windows/Mac, Linux requires only installation. Download from ffmpeg.org, not the pip package)
+ pafy (Comment line 54 in pafy.backend_youtube_dl)
+ asyncpraw (praw.ini file required)
+ PyNaCl
+ lyrics-extractor
+ wikipedia
+ google-api-python-client
+ psycopg2

# API requisites
+ [JSON API Key](https://developers.google.com/custom-search/v1/overview) Required for searching lyrics
+ [Programmable Search Engine](https://cse.google.com/cse/create/new) Required for searching lyrics
+ [YouTube API access Key](https://console.developers.google.com) Create a new project and enable the YouTube API

# Database 
PostgreSQL is used. You can change the database details (username, host, database) to your convinience. 

Currently, there are 3 tables:
+ afks (columns: SN, member, member_id, guild_id, reason)
+ snipes (columns: SN, author_id, message, channel_id, time)
+ prefixes (columns: SN, guild_id, prefix)

More details in DATABASE.md

# Invite
Please contact Dose#7204 through discord for the invite link.

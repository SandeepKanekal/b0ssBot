# b0ssBot
A discord bot for fun, moderation, and music! Adding features everyday

# Prerequisites
+ py-cord 2.0+ (https://github.com/Pycord-Development/pycord)
+ Flask
+ FFmpeg (Add FFmpeg to PATH in Windows/Mac, Linux requires only installation. Download from ffmpeg.org, not the pip package)
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
+ [OpenWeatherMap API Key](https://openweathermap.org/api) Required for weather commands

# Database 
PostgreSQL is used. You can change the database details (username, host, database) to your convinience. 

Currently, there are 9 tables:
+ afks (columns: SN, member, member_id, guild_id, reason)
+ snipes (columns: SN, author_id, message, channel_id, time, 'guild_id')
+ prefixes (columns: SN, guild_id, prefix)
+ modlogs (columns: SN, guild_id, mode, channel_id)
+ warns (columns: SN, guild_id, member_id, reason, warns)
+ queue (columns: SN, guild_id, source, title, url)
+ loop (columns: SN, guild_id, source, title, url)
+ message_responses(columns: SN, guild_id, message, response)
+ youtube(columns: SN, guild_id, text_channel_id, channel_id, channel_name, latest_video_id)
+ hourlyweather(columns: SN, guild_id, channel_id, location)

More details in [DATABASE.md](https://github.com/SandeepKanekal/b0ssBot/blob/main/DATABASE.md)

# Invite
Please contact Dose#7204 through discord for the invite link.

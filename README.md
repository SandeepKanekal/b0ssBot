# b0ssBot
A discord bot for fun, moderation, and music! Adding features everyday

# Prerequisites
+ [py-cord 2.0+](https://github.com/Pycord-Development/pycord)
+ [Flask](https://pypi.org/project/Flask/)
+ [FFmpeg](https://www.ffmpeg.org/)
+ [asyncpraw](https://pypi.org/project/asyncpraw/)
+ [PyNaCl](https://pypi.org/project/PyNaCl/)
+ [lyrics-extractor](https://pypi.org/project/lyrics-extractor/)
+ [wikipedia](https://pypi.org/project/wikipedia/)
+ [google-api-python-client](https://pypi.org/project/google-api-python-client/)
+ [psycopg2](https://pypi.org/project/psycopg2/)
+ [pillow](https://pypi.org/project/Pillow/)

# API requisites
+ [JSON API Key](https://developers.google.com/custom-search/v1/overview) Required for searching lyrics
+ [Programmable Search Engine](https://cse.google.com/cse/create/new) Required for searching lyrics
+ [YouTube API access Key](https://console.developers.google.com) Create a new project and enable the YouTube API
+ [OpenWeatherMap API Key](https://openweathermap.org/api) Required for weather commands
+ [Zenquotes.io API](https://zenquotes.io/api) Required for quote commands (no key required)
+ [OpenTDB API](https://opentdb.com/api_config.php) Required for trivia commands (no key required)
+ [TruthOrDareBot API](https://docs.truthordarebot.xyz/api-docs) Required for truth or dare commands (no key required)
+ [Icanhasdadjoke API](https://icanhazdadjoke.com/api) Required for dad joke commands (no key required)
+ [BoredAPI](https://boredapi.com/api) Required for bored commands (no key required)
+ [GitHub API](https://developer.github.com/v3/) Required for GitHub commands (no key required)
+ [Dog CEO API](https://dog.ceo/dog-api/) Required for dog commands (no key required)
+ [The Cat API](https://thecatapi.com/) Required for cat commands (no key required)

# Database 
PostgreSQL is used. You can change the database details (username, host, database) to your convinience. 

Currently, there are 10 tables:
+ afks (columns: SN, member, member_id, guild_id, reason)
+ snipes (columns: SN, author_id, message, channel_id, time, 'guild_id', 'attachments')
+ prefixes (columns: SN, guild_id, prefix)
+ modlogs (columns: SN, guild_id, mode, channel_id)
+ warns (columns: SN, guild_id, member_id, reason, warns)
+ queue (columns: SN, guild_id, source, title, url)
+ loop (columns: SN, guild_id, source, title, url)
+ message_responses(columns: SN, guild_id, message, response)
+ youtube(columns: SN, guild_id, text_channel_id, channel_id, channel_name, latest_video_id)

More details in [DATABASE.md](https://github.com/SandeepKanekal/b0ssBot/blob/main/DATABASE.md)

# Invite
[Click Here](https://discord.com/api/oauth2/authorize?client_id=930715008025890887&permissions=8&scope=bot%20applications.commands) to invite b0ssBot to your server.

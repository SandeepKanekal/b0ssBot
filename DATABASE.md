# Database 
PostgreSQL is used. You can change the database details (username, host, database) to your convinience. 

Currently, there are 3 tables:
+ afks (columns: SN, member, member_id, guild_id, reason)
+ snipes (columns: SN, author_id, message, channel_id, time)
+ prefixes (columns: SN, guild_id, prefix)

# afks 
Stores AFK members
+ SN: Serial number (Not Null, Primary Key)
+ member: Member who is afk (Not Null, VARCHAR(50))
+ member_id: Member ID who is afk (Not Null, VARCHAR(18))
+ guild_id: Guild ID who is afk (Not Null, VARCHAR(18))
+ reason: Reason for afk (Not Null, VARCHAR(2000))

# snipes
Stores deleted messages for a minute
+ SN: Serial number (Not Null, Primary Key)
+ author_id: ID of the author of the deleted message (Not Null, VARCHAR(18))
+ message: Deleted message (Not Null, VARCHAR(2000))
+ channel_id: Channel ID of the deleted message (Not Null, VARCHAR(18))
+ time: Time of the deleted message (Not Null, VARCHAR(26))

# prefixes
Stores custom prefixes for guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(18))
+ prefix: Prefix for the guild (Not Null, VARCHAR(2))

# modlogs
Stores if the guild has enabled modlogs, and the channel if enabled
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(18))
+ mode: Mode of the modlogs (Not Null, int)
+ channel_id: Channel ID of the modlog channel (Not Null, VARCHAR(18))

# warns
Stores warns for members for that specific guild
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(18))
+ member_id: Member ID (Not Null, VARCHAR(18))
+ reason: Reason for the warn (Not Null, VARCHAR(2000))
+ warns: Number of warns for the user (Not Null, int)

# queue
Stores the music queue for all guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(18))
+ source: Source of the song (Not Null, VARCHAR(2000))
+ title: Title of the song (Not Null, VARCHAR(2000))
+ url: URL of the song (Not Null, VARCHAR(2000))

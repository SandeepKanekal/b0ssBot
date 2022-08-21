# Database 
PostgreSQL is used. You can change the database details (username, host, database) to your convinience. 

Table information:

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
+ guild_id: Guild ID of the deleted message (Not Null, VARCHAR(18))
+ attachments: Stores URLs of each attachment send (Not Null, VARCHAR\[](2000))

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
Store warns for members for that specific guild
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(18))
+ member_id: Member ID (Not Null, VARCHAR(18))
+ reason: Reason for warning (Not Null, VARCHAR\[](2000))
+ warns: Number of warns for the user (Not Null, int)

# queue
Stores the music queue for all guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(18))
+ source: Source of the song (Not Null, VARCHAR(2000))
+ title: Title of the song (Not Null, VARCHAR(2000))
+ url: URL of the song (Not Null, VARCHAR(2000))

# loop
Stores the details of the track to be looped for the guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(18))
+ source: Source of the song (Not Null, VARCHAR(2000))
+ title: Title of the song (Not Null, VARCHAR(2000))
+ url: URL of the song (Not Null, VARCHAR(2000))

# message_responses
Stores the message responses for the guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(18))
+ message: Message to be responded to (Not Null, VARCHAR(2000))
+ response: Response to the message (Not Null, VARCHAR(2000))

# youtube
Stores the YouTube channels that the guild wants to be notified when a video is uploaded
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(18))
+ text_channel_id: Text channel ID (Not Null, VARCHAR(18))
+ channel_id: Channel ID (Not Null, VARCHAR(24))
+ channel_name: Channel name (Not Null, VARCHAR(2000))
+ latest_video_id: Latest video ID (Not Null, VARCHAR(11))

# verifications
Stores the verification system of the guilds
+ SN: Serial number (Not Null, Primary Key)
+ message_id: Message ID (Not Null, VARCHAR(18))
+ role_id: Role ID (Not Null, VARCHAR(18))
+ unverified_role_id: The ID of the unverified role (Not Null, VARCHAR(18))
+ channel_id: Channel ID (Not Null, VARCHAR(18))
+ guild_id: Guild ID (Not Null, VARCHAR(18))

# history
Stores the search history a user has with b0ssBot
+ SN: Serial number (Not Null, Primary Key)
+ member_id: Member ID (Not Null, VARCHAR(18))
+ query: The query (Not Null, VARCHAR(2000))
+ type: The type of service used  (Not Null, VARCHAR(20))
+ timestamp: The timestamp of when the service was used (Not Null, integer)
+ guild_id: Guild ID (Not Null, VARCHAR(18))

# serverjoin
Stores role addition configurations for members/bots of the guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(18))
+ member_role_id: Role ID for members (Not Null, VARCHAR(18))
+ bot_role_id: Role ID for bots (Not Null, VARCHAR(18))

# playlist
Stores the playlist to be looped for the guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(18))
+ source: Source of the song (Not Null, VARCHAR(2000))
+ title: Title of the song (Not Null, VARCHAR(2000))
+ url: URL of the song (Not Null, VARCHAR(2000))
+ position: Position of the song in the playlist (Not Null, int)

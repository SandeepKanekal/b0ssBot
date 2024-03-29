# Database 
PostgreSQL is used. You can change the database details (username, host, database) to your convinience. 

Table information:

# afks 
Stores AFK members
+ SN: Serial number (Not Null, Primary Key)
+ member: Member who is afk (Not Null, VARCHAR(50))
+ member_id: Member ID who is afk (Not Null, VARCHAR(19))
+ guild_id: Guild ID who is afk (Not Null, VARCHAR(19))
+ reason: Reason for afk (Not Null, VARCHAR(2000))

# snipes
Stores deleted messages for a minute
+ SN: Serial number (Not Null, Primary Key)
+ author_id: ID of the author of the deleted message (Not Null, VARCHAR(19))
+ message: Deleted message (Not Null, VARCHAR(2000))
+ channel_id: Channel ID of the deleted message (Not Null, VARCHAR(19))
+ time: Time of the deleted message (Not Null, VARCHAR(26))
+ guild_id: Guild ID of the deleted message (Not Null, VARCHAR(19))
+ attachments: Stores URLs of each attachment send (Not Null, VARCHAR\[])

# prefixes
Stores custom prefixes for guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(19))
+ prefix: Prefix for the guild (Not Null, VARCHAR(2))

# modlogs
Stores if the guild has enabled modlogs, and the channel if enabled
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(19))
+ channel_id: Channel ID of the modlog channel (Not Null, VARCHAR(19))

# warns
Store warns for members for that specific guild
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(19))
+ member_id: Member ID (Not Null, VARCHAR(19))
+ reason: Reason for warning (Not Null, VARCHAR\[])
+ warns: Number of warns for the user (Not Null, int)

# queue
Stores the music queue for all guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(19))
+ source: Source of the song (Not Null, VARCHAR(2000))
+ title: Title of the song (Not Null, VARCHAR(2000))
+ url: URL of the song (Not Null, VARCHAR(2000))

# loop
Stores the details of the track to be looped for the guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(19))
+ source: Source of the song (Not Null, VARCHAR(2000))
+ title: Title of the song (Not Null, VARCHAR(2000))
+ url: URL of the song (Not Null, VARCHAR(2000))

# message_responses
Stores the message responses for the guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(19))
+ message: Message to be responded to (Not Null, VARCHAR(2000))
+ response: Response to the message (Not Null, VARCHAR(2000))

# youtube
Stores the YouTube channels that the guild wants to be notified when a video is uploaded
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(19))
+ text_channel_id: Text channel ID (Not Null, VARCHAR(19))
+ channel_id: Channel ID (Not Null, VARCHAR(24))
+ channel_name: Channel name (Not Null, VARCHAR(2000))
+ latest_video_id: Latest video ID (Not Null, VARCHAR(11))

# verifications
Stores the verification system of the guilds
+ SN: Serial number (Not Null, Primary Key)
+ message_id: Message ID (Not Null, VARCHAR(19))
+ role_id: Role ID (Not Null, VARCHAR(19))
+ unverified_role_id: The ID of the unverified role (Not Null, VARCHAR(19))
+ channel_id: Channel ID (Not Null, VARCHAR(19))
+ guild_id: Guild ID (Not Null, VARCHAR(19))

# serverjoin
Stores role addition configurations for members/bots of the guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(19))
+ member_role_id: Role ID for members (Not Null, VARCHAR(19))
+ bot_role_id: Role ID for bots (Not Null, VARCHAR(19))

# playlist
Stores the playlist to be looped for the guilds
+ SN: Serial number (Not Null, Primary Key)
+ guild_id: Guild ID (Not Null, VARCHAR(19))
+ source: Source of the song (Not Null, VARCHAR(2000))
+ title: Title of the song (Not Null, VARCHAR(2000))
+ url: URL of the song (Not Null, VARCHAR(2000))
+ position: Position of the song in the playlist (Not Null, int)

# Copyright (c) 2022 Sandeep Kanekal
# Requirements for running this module:
# Linux/Mac - Install in terminal
# Windows - Add FFmpeg to PATH (https://windowsloop.com/install-ffmpeg-windows-10/)
import contextlib
import discord
import os
import asyncio
import datetime
import lyrics_extractor
from sql_tools import SQL
from discord.ext import commands
from discord.ext.commands import CommandError
from tools import send_error_embed, get_video_stats, format_time, inform_owner
from youtube_dl import YoutubeDL
from ui_components import MusicView
from discord.commands import Option, SlashCommandGroup


class AuthorNotConnectedToVoiceChannel(CommandError):
    pass


class AlreadyConnectedToVoiceChannel(CommandError):
    pass


class LoopingEnabled(CommandError):
    pass


class AuthorInDifferentVoiceChannel(CommandError):
    pass


class PlayerNotConnectedToVoiceChannel(CommandError):
    pass


class NoAudioPlaying(CommandError):
    pass


class PlayerPaused(CommandError):
    pass


class PlayerPlaying(CommandError):
    pass


class NoTrack(CommandError):
    pass


class NotInRange(CommandError):
    pass


class Music(commands.Cog):

    def __init__(self, bot: commands.Bot):
        """
        Initializes the Music cog.
        
        :param bot: The bot object.
        
        :type bot: commands.Bot
        
        :return: None
        :rtype: None
        """
        self.bot: commands.Bot = bot
        self.now_playing: dict[int, str | None] = {}  # Stores the current track for each guild
        self.now_playing_url: dict[int, str | None] = {}  # Stores the current track url for each guild
        self.start_time: dict[int, datetime.datetime | None] = {}  # Stores the start time for each guild
        self.source: dict[int, str | None] = {}  # Stores the source for each guild
        self.volume: dict[int, int] = {}  # Stores the volume for each guild
        self.pause_time: dict[
            int, datetime.datetime | None] = {}  # Stores the time when the track was paused for each guild
        self.music_view: dict[int, MusicView | None] = {}  # Stores the view object for each guild
        self.loop_limit: dict[int, int | None] = {}  # Stores the number of times the track must be looped
        self.sql: SQL = SQL(os.getenv('sql_db_name'))
        self._ydl_options: dict[str, bool | str] = {
            "format": "bestaudio/best",
            "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
            "restrictfilenames": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "source_address": "0.0.0.0",
        }  # Options for youtube_dl
        self._ffmpeg_options: dict[str, str] = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }  # Options for ffmpeg

    # noinspection PyUnusedLocal
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState) -> None:
        """
        Listener for when a member changes voice state.
        
        :param member: The member that changed voice state.
        :param before: The voice state before the change.
        :param after: The voice state after the change.
        
        :type member: discord.Member
        :type before: discord.VoiceState
        :type after: discord.VoiceState
        
        :return: None
        :rtype: None
        """
        vc: discord.VoiceClient = member.guild.voice_client
        if not vc:
            return

        # Auto disconnect
        if before.channel and not after.channel:
            if list(filter(lambda m: not m.bot, vc.channel.members)):
                return

            vc.stop()
            await vc.disconnect()

            # Delete all the keys storing the guild's information
            with contextlib.suppress(KeyError, AttributeError):
                del self.now_playing[member.guild.id]
                del self.now_playing_url[member.guild.id]
                del self.start_time[member.guild.id]
                del self.source[member.guild.id]
                del self.volume[member.guild.id]
                del self.pause_time[member.guild.id]
                self.music_view[member.guild.id].stop()
                del self.music_view[member.guild.id]
                del self.loop_limit[member.guild.id]

            self.sql.delete('queue', f"guild_id = '{member.guild.id}'")
            self.sql.delete('loop', f"guild_id = '{member.guild.id}'")
            self.sql.delete('playlist', f"guild_id = '{member.guild.id}'")

        # Auto pause/resume on self deafen/undeafen
        elif len(list(filter(lambda m: not m.bot, vc.channel.members))) == 1:
            if not before.self_deaf and after.self_deaf:
                vc.pause()
                self.pause_time[member.guild.id] = datetime.datetime.now()
                await member.send(
                    'I paused the player since you self deafened and were the only member in the voice channel.')
            elif before.self_deaf and not after.self_deaf:
                vc.resume()
                self.start_time[member.guild.id] += datetime.datetime.now() - self.pause_time[member.guild.id]
                await member.send(
                    'I resumed the player since you unself deafened and were the only member in the voice channel.')

    def search_yt(self, item):
        """
        Searches YouTube for the item.
        
        :param item: The item to search for.
        
        :type item: str
        
        :return: The video details of the item.
        :rtype: dict[str, str | int] | Exception
        """
        with YoutubeDL(self._ydl_options) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]  # Get the required details
            except Exception as e:
                return e

        return {'source': info['formats'][0]['url'], 'title': info['title'],
                'url': info['webpage_url'], 'channel_title': info['channel'], 'channel_id': info['channel_id'],
                'view_count': info['view_count'],
                'like_count': info['like_count'] if 'like_count' in info else 'Could not fetch likes',
                'thumbnail': info['thumbnail'],
                'duration': info['duration']}  # Return required details

    async def _send_embed_after_track(self, ctx: commands.Context):
        """
        Sends an embed after the track has finished playing

        :param ctx: The context of the command.
        
        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
        self.music_view[ctx.guild.id].stop()  # Stop listening for interactions with buttons

        # Delete the track from the loop table if the limit is over
        if isinstance(self.loop_limit[ctx.guild.id], int):
            self.loop_limit[ctx.guild.id] -= 1

        if self.loop_limit[ctx.guild.id] == 0:
            self.loop_limit[ctx.guild.id] = None
            self.sql.delete('loop', f"guild_id = '{ctx.guild.id}'")

        # Loop track
        if self.sql.select(elements=['*'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
            track = self.sql.select(elements=['title', 'url'], table='loop', where=f"guild_id = '{ctx.guild.id}'")[0]
            embed = discord.Embed(title='Now Playing', description=f"[{track[0]}]({track[1]})",
                                  colour=discord.Colour.green())
            view = MusicView(ctx, self.bot, ctx.guild.voice_client, track[0][0], timeout=None)

        # Queued track
        elif self.sql.select(elements=['*'], table='queue', where=f"guild_id = '{ctx.guild.id}'"):
            track = self.sql.select(elements=['title', 'url'], table='queue', where=f"guild_id = '{ctx.guild.id}'")[0]
            embed = discord.Embed(title='Now Playing', description=f"[{track[0]}]({track[1]})",
                                  colour=discord.Colour.green())
            view = MusicView(ctx, self.bot, ctx.guild.voice_client, track[0][0], timeout=None)

        # No track
        else:
            embed = discord.Embed(description='Queue is over', colour=discord.Colour.red())
            embed.set_footer(text='Use the play command to add tracks')
            view = None

        self.music_view[ctx.guild.id] = view
        await ctx.send(embed=embed, view=view)

    async def _send_confirmation(self, ctx: commands.Context, song: dict):
        """
        Sends a confirmation message to the channel.
        
        :param ctx: The context of the command.
        :param song: The details of the track
        
        :type ctx: commands.Context
        :type song: dict
        
        :return: None
        :rtype: None
        """
        # Create embed
        embed = discord.Embed(colour=discord.Colour.blurple())

        embed.set_thumbnail(url=song['thumbnail'])
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(
            text=f'Duration: {format_time(song["duration"])}, 📽️: {song["view_count"]}, 👍: {song["like_count"]}'
        )

        embed.add_field(
            name='Song added to queue',
            value=f'[{song["title"]}]({song["url"]}) BY [{song["channel_title"]}](https://youtube.com/channel/{song["channel_id"]})'
        )

        # Configure view
        if not ctx.voice_client.is_playing():
            view = MusicView(ctx, self.bot, ctx.guild.voice_client, song['title'], timeout=None)
            self.music_view[ctx.guild.id] = view
        else:
            view = None

        # Respond
        await ctx.send(
            'In case the music is not playing, please use the play command again since the access to the music player could be denied.',
            embed=embed, view=view
        )

    def update_playlist(self, ctx: commands.Context):
        """
        Updates the playlist to be looped if it exists.

        :param ctx: The context of the command.

        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        if ctx.guild.voice_client is None:
            return

        if playlist_track := self.sql.select(elements=['source', 'title', 'url', 'position'], table='playlist',
                                             where=f"guild_id = '{ctx.guild.id}'"):
            # Update index properly
            index = 0
            for track_details in playlist_track:
                if self.now_playing[ctx.guild.id] in track_details:
                    break
                index += 1

            try:
                index = playlist_track[index + 1][3]
            except IndexError:
                index = 0

            # Update database
            self.sql.update('loop', 'source', f"'{playlist_track[index][0]}'", f"guild_id = '{ctx.guild.id}'")
            self.sql.update('loop', 'title', f"'{playlist_track[index][1]}'", f"guild_id = '{ctx.guild.id}'")
            self.sql.update('loop', 'url', f"'{playlist_track[index][2]}'", f"guild_id = '{ctx.guild.id}'")

    def play_next(self, ctx: commands.Context):
        """
        The play_next function is used when the player is already playing, this function is invoked when the player is done playing one of the tracks in the queue.
        
        :param ctx: The context of the command.
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        vc = ctx.guild.voice_client  # Get the voice client
        self.update_playlist(ctx)  # Update the playlist to be looped if it exists
        asyncio.run_coroutine_threadsafe(self._send_embed_after_track(ctx), self.bot.loop)  # Send the embed
        if self.sql.select(['title'], 'queue', f"guild_id = '{ctx.guild.id}'") or self.sql.select(['title'], 'loop',
                                                                                                  f"guild_id = '{ctx.guild.id}'"):  # Check if there are any tracks queued or looped
            self._play_next(ctx, vc)
        else:
            # If no track is present to play, all the variables store None
            self.now_playing[ctx.guild.id] = None
            self.now_playing_url[ctx.guild.id] = None
            self.start_time[ctx.guild.id] = None
            self.source[ctx.guild.id] = None
            self.pause_time[ctx.guild.id] = None
            self.loop_limit[ctx.guild.id] = None

    def _play_next(self, ctx: commands.Context, vc: discord.VoiceClient):
        """
        The _play_next function plays the music after a track has been played and updates the database.
        
        :param ctx: The context of the command.
        :param vc: The voice client.
        
        :type ctx: commands.Context
        :type vc: discord.VoiceClient
        
        :return: None
        :rtype: None
        """
        # Get the url to be played from the loop or queue table
        track = self.sql.select(elements=['source', 'title', 'url'], table='loop',
                                where=f"guild_id = '{ctx.guild.id}'") or self.sql.select(
            elements=['source', 'title', 'url'], table='queue', where=f"guild_id = '{ctx.guild.id}'")

        m_url = track[0][0]
        self.now_playing[ctx.guild.id] = track[0][1]
        self.now_playing_url[ctx.guild.id] = track[0][2]
        self.start_time[ctx.guild.id] = datetime.datetime.now()
        self.source[ctx.guild.id] = track[0][0]

        # Play the track
        vc.play(discord.FFmpegPCMAudio(m_url, **self._ffmpeg_options), after=lambda e: self.play_next(ctx))
        vc.source = discord.PCMVolumeTransformer(vc.source, volume=self.volume[ctx.guild.id] / 100)

        # Delete the track from the queue
        if not self.sql.select(elements=['*'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
            title = track[0][1]
            title = title.replace("'", "''")
            self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}' AND title = '{title}'")

    async def play_music(self, ctx: commands.Context):
        """
        The play_music function is used to play the music when no track is playing.
        
        :param ctx: The context of the command.
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        vc = ctx.guild.voice_client  # Get the voice client
        voice_channel = ctx.author.voice.channel  # Get the voice channel

        if track := self.sql.select(['source', 'title', 'url'], 'loop', f"guild_id = '{ctx.guild.id}'"):
            self.start_time[ctx.guild.id] = datetime.datetime.now()
        else:
            track = \
                self.sql.select(elements=['source', 'title', 'url'], table='queue',
                                where=f"guild_id = '{ctx.guild.id}'")

        m_url = track[0][0]
        self.now_playing[ctx.guild.id] = track[0][1]
        self.now_playing_url[ctx.guild.id] = track[0][2]
        self.start_time[ctx.guild.id] = datetime.datetime.now()
        self.source[ctx.guild.id] = track[0][0]

        # try to connect to voice channel if you are not already connected
        try:
            vc = await voice_channel.connect()
        except discord.ClientException:
            await vc.move_to(voice_channel)

        # Play the track
        vc.play(discord.FFmpegPCMAudio(m_url, **self._ffmpeg_options), after=lambda e: self.play_next(ctx))
        vc.source = discord.PCMVolumeTransformer(vc.source, volume=self.volume[ctx.guild.id] / 100)

        # Delete the track as it is being played
        if not self.sql.select(elements=['*'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
            title = track[0][1]
            title = title.replace("'", "''")
            self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}' AND title = '{title}'")

    @commands.command(aliases=['j', 'summon'], description='Joins the voice channel you are in', usage='join')
    async def join(self, ctx: commands.Context):
        """
        Joins the voice channel you are in.
        
        :param ctx: The context of the command.
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        if ctx.author.voice is None:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')
        voice_channel = ctx.author.voice.channel  # Get the voice channel
        try:
            await voice_channel.connect()
        except discord.ClientException as e:
            raise AlreadyConnectedToVoiceChannel('Already connected to a voice channel') from e

    @join.error
    async def join_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the join command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, AlreadyConnectedToVoiceChannel):
            await send_error_embed(ctx, f'Error: `{error}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the join command! The owner has been notified.')
            await inform_owner(self.bot, error)

    @commands.command(aliases=['p', 'add'],
                      description='Plays the searched song from YouTube or adds it to the queue, query can be a link or a search term',
                      usage='play <query>')
    async def play(self, ctx: commands.Context, *, query: str):
        """
        Plays the searched song from YouTube or adds it to the queue, query can be a link or a search term.

        :param ctx: The context of the command.
        :param query: The query to be searched.

        :type ctx: commands.Context
        :type query: str

        :return: None
        :rtype: None
        """
        async with ctx.typing():
            vc = ctx.guild.voice_client  # Get the voice client

            if ctx.author.voice is None:
                raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')
            voice_channel = ctx.author.voice.channel  # Get the voice channel

            if vc is None:
                await voice_channel.connect()
            elif vc.is_connected() and vc.channel != voice_channel:
                raise AuthorInDifferentVoiceChannel('You are in a different voice channel')

            if vc and vc.is_paused():
                vc.resume()

            song = self.search_yt(query)  # Get the track details

            if isinstance(song, IndexError):
                await send_error_embed(ctx, description=f'No results found for {query}')
                return

            if isinstance(song, Exception):
                await send_error_embed(ctx, description=f'Error: `{song}`')
                return

            if ctx.guild.id not in self.volume:
                self.volume[ctx.guild.id] = 100
            if ctx.guild.id not in self.loop_limit:
                self.loop_limit[ctx.guild.id] = None
            song["title"] = song["title"].replace("'", "''")  # Single quotes cause problems

            self.sql.insert(
                table='queue',
                columns=['guild_id', 'source', 'title', 'url'],
                values=[
                    f"'{ctx.guild.id}'",
                    f"'{song['source']}'",
                    f"'{song['title']}'",
                    f"'{song['url']}'"
                ]
            )

            song['title'] = song['title'].replace("''", "'")

        await self._send_confirmation(ctx, song)

        if not ctx.voice_client.is_playing():
            # Plays the music
            await self.play_music(ctx)

    # Sometimes, videos are not available, a response is required to inform the user
    @play.error
    async def play_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the play command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, (AuthorNotConnectedToVoiceChannel, AuthorInDifferentVoiceChannel)):
            await send_error_embed(ctx, f'Error: `{error}`')
        elif isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   f'Please specify a query\n\nProper Usage: `{self.bot.get_command("play").usage}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the play command! The owner has been notified.')
            await inform_owner(self.bot, error)

    @commands.command(aliases=['q'], description='Shows the music queue', usage='queue')
    async def queue(self, ctx: commands.Context):
        """
        Shows the music queue.
        
        :param ctx: The context of the command.
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        # This command does not stop users outside the voice channel from accessing the command since it is a view-only command
        vc = ctx.guild.voice_client

        if vc is None:  # Player is not connected
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if not vc.is_playing():
            raise NoAudioPlaying('No audio is playing')

        # Create embed
        embed = discord.Embed(title='Music Queue', colour=discord.Colour.dark_teal(), timestamp=datetime.datetime.now())
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)

        # Playlist
        if track := self.sql.select(elements=['title', 'url'], table='playlist', where=f"guild_id = '{ctx.guild.id}'"):
            embed.title = 'Looping Playlist'
            for index, song in enumerate(track):
                embed.add_field(name=f'Track Number {index + 1}', value=f'[{song[0]}]({song[1]})', inline=False)

        # Looping
        elif track := self.sql.select(elements=['title', 'url'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
            embed.add_field(
                name='Looping',
                value=f'[{track[0][0]}]({track[0][1]})'
            )
            video = get_video_stats(track[0][1])
            embed.set_footer(
                text=f'Duration: {video["contentDetails"]["duration"].strip("PT")}, 📽️: {video["statistics"]["viewCount"]}, 👍: {video["statistics"]["likeCount"] if "likeCount" in video["statistics"].keys() else "Could not fetch likes"}'
            )

        # Queue
        else:
            queue = self.sql.select(elements=['title', 'url'], table='queue', where=f"guild_id = '{ctx.guild.id}'")
            embed.add_field(name='Now Playing:',
                            value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})',
                            inline=False)
            for index, item in enumerate(queue):
                embed.add_field(name=f'Track Number {index + 1}', value=f'[{item[0]}]({item[1]})', inline=False)

        await ctx.send(embed=embed)

    @queue.error
    async def queue_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the queue command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, (PlayerNotConnectedToVoiceChannel, NoAudioPlaying)):
            await send_error_embed(ctx, f'Error: `{error}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the queue command! The owner has been notified.')
            await inform_owner(self.bot, error)

    @commands.command(name='pause', description='Pauses the current track', usage='pause')
    async def pause(self, ctx: commands.Context):
        """
        Pauses the current track.
        
        :param ctx: The context of the command.
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        # Get the voice client
        vc = ctx.guild.voice_client

        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if vc.is_paused():
            raise PlayerPaused('Player is already paused')

        if not vc.is_playing():
            raise NoAudioPlaying('No audio is playing')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

        self.pause_time[ctx.guild.id] = datetime.datetime.now()

        vc.pause()

        # Response embed
        embed = discord.Embed(
            description=f'Paused [{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})',
            colour=discord.Colour.green())
        await ctx.send(embed=embed)

    @pause.error
    async def pause_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the pause command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, (
                AuthorNotConnectedToVoiceChannel, NoAudioPlaying, PlayerPaused, AuthorInDifferentVoiceChannel,
                PlayerNotConnectedToVoiceChannel)):
            await send_error_embed(ctx, f'Error: `{error}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the pause command! The owner has been notified.')
            await inform_owner(self.bot, error)

    @commands.command(aliases=['unpause', 'up'], description='Resumes the paused track', usage='resume')
    async def resume(self, ctx: commands.Context):
        """
        Resumes the paused track.
        
        :param ctx: The context of the command.
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = ctx.guild.voice_client

        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if vc.is_playing():
            raise PlayerPlaying('Player is already playing')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

        self.start_time[ctx.guild.id] += datetime.datetime.now() - self.pause_time[ctx.guild.id]

        vc.resume()

        # Response embed
        embed = discord.Embed(
            description=f'Resumed [{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})',
            colour=discord.Colour.green())
        await ctx.send(embed=embed)

    @resume.error
    async def resume_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the resume command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, (AuthorNotConnectedToVoiceChannel, PlayerPlaying, AuthorInDifferentVoiceChannel,
                              PlayerNotConnectedToVoiceChannel)):
            await send_error_embed(ctx, f'Error: `{error}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the resume command! The owner has been notified.')
            await inform_owner(self.bot, error)

    # Skips the current track
    @commands.command(name="skip", description="Skips the current track", usage="skip")
    async def skip(self, ctx: commands.Context):
        """
        Skips the current track.
        
        :param ctx: The context of the command.
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = ctx.guild.voice_client

        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if not vc.is_playing():
            raise NoAudioPlaying('No audio is playing')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

        vc.stop()  # Stopping the player (play_next will be called instantly after stopping)

        # Response embed
        embed = discord.Embed(
            description=f'Skipped [{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})',
            colour=discord.Colour.green())
        await ctx.send(embed=embed)

    @skip.error
    async def skip_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the skip command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, (AuthorNotConnectedToVoiceChannel, NoAudioPlaying, PlayerNotConnectedToVoiceChannel,
                              AuthorInDifferentVoiceChannel)):
            await send_error_embed(ctx, f'Error: `{error}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the skip command! The owner has been notified.')
            await inform_owner(self.bot, error)

    # Stop command
    @commands.command(name='stop', description='Stops the current track and clears the queue', usage='stop')
    async def stop(self, ctx: commands.Context):
        """
        Stops the current track and clears the queue.
        
        :param ctx: The context of the command.
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = ctx.guild.voice_client

        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if not vc.is_playing():
            raise NoAudioPlaying('No audio is playing')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

        embed = discord.Embed(description='Stopped', colour=discord.Colour.green())
        await ctx.send(embed=embed)

        # Clearing the queue for the guild
        self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}'")
        self.sql.delete(table='loop', where=f"guild_id = '{ctx.guild.id}'")
        self.sql.delete(table='playlist', where=f"guild_id = '{ctx.guild.id}'")

        # Stopping the player
        vc.stop()

    @stop.error
    async def stop_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the stop command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, (AuthorNotConnectedToVoiceChannel, NoAudioPlaying, PlayerNotConnectedToVoiceChannel,
                              AuthorInDifferentVoiceChannel)):
            await send_error_embed(ctx, f'Error: `{error}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the stop command! The owner has been notified.')
            await inform_owner(self.bot, error)

    # Disconnect command
    @commands.command(aliases=['dc', 'leave'], description="Disconnects the player from the voice channel",
                      usage='disconnect')
    async def disconnect(self, ctx: commands.Context):
        """
        Disconnects the player from the voice channel.
        
        :param ctx: The context of the command.
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = ctx.guild.voice_client

        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

        embed = discord.Embed(description='Disconnected', colour=discord.Colour.green())
        await ctx.send(embed=embed)
        await vc.disconnect()  # Disconnecting the player

        with contextlib.suppress(KeyError):
            # Delete all the keys storing the guild's information
            del self.now_playing[ctx.guild.id]
            del self.now_playing_url[ctx.guild.id]
            del self.start_time[ctx.guild.id]
            del self.source[ctx.guild.id]
            del self.volume[ctx.guild.id]
            del self.pause_time[ctx.guild.id]
            del self.music_view[ctx.guild.id]
            del self.loop_limit[ctx.guild.id]

        # Clearing the queue for the guild
        self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}'")
        self.sql.delete(table='loop', where=f"guild_id = '{ctx.guild.id}'")
        self.sql.delete(table='playlist', where=f"guild_id = '{ctx.guild.id}'")

    @disconnect.error
    async def disconnect_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the disconnect command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, (
                AuthorNotConnectedToVoiceChannel, PlayerNotConnectedToVoiceChannel, AuthorInDifferentVoiceChannel)):
            await send_error_embed(ctx, f'Error: `{error}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the disconnect command! The owner has been notified.')
            await inform_owner(self.bot, error)

    # Nowplaying command
    @commands.command(aliases=['np', 'now'], description='Shows the current track being played', usage='nowplaying')
    async def nowplaying(self, ctx: commands.Context):
        """
        Shows the current track being played.
        
        :param ctx: The context of the command.
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        # This command does not prevent users from outside the voice channel from accessing the command since it is view-only
        vc = ctx.guild.voice_client

        # Basic responses to false calls
        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if not vc.is_playing():
            raise NoAudioPlaying('No audio is playing')

        # Getting the video details
        video = get_video_stats(self.now_playing_url[ctx.guild.id])

        # Time calculations
        time_now = datetime.datetime.now()
        seconds_between = (time_now - self.start_time[ctx.guild.id]).seconds  # Calculating the time elapsed
        minutes_between = seconds_between // 60  # Calculating the minutes elapsed
        hours_between = minutes_between // 60  # Calculating the hours elapsed
        seconds_between = seconds_between % 60  # Seconds cannot exceed 60
        minutes_between = minutes_between % 60  # Minutes cannot exceed 60

        # Concatenate 0 if the number is less than 10
        if seconds_between < 10:
            seconds_between = f'0{str(seconds_between)}'
        if minutes_between < 10:
            minutes_between = f'0{str(minutes_between)}'
        if hours_between < 10:
            hours_between = f'0{str(hours_between)}'

        duration = video["contentDetails"]["duration"].strip("PT")  # Getting the duration of the video
        if "S" not in duration:  # Putting 0S if there are no seconds
            duration = f"{duration}0S"
        if "H" in duration and "M" not in duration:  # Putting 0M if hours are present, without minutes
            dur = duration.split("H")
            duration = f'{dur[0]}H0M{dur[1]}'
        if "M" not in duration:  # Putting 0M if there are no minutes
            duration = f'0M{duration}'
        if "H" not in duration:  # Putting 0H if there are no hours
            duration = f'0H{duration}'
        duration = duration.replace('H', ':')  # Replacing H with :
        duration = duration.replace("M", ":")  # Replacing the M with :
        duration = duration.replace("S", "")  # Removing the S
        dur = duration.split(":")  # Splitting the duration into hours, minutes and seconds
        if int(dur[0]) < 10:
            dur[0] = f'0{dur[0]}'  # Adding 0 if the hours are less than 10
        if int(dur[1]) < 10:
            dur[1] = f'0{dur[1]}'  # Adding 0 if the minutes are less than 10
        if int(dur[2]) < 10:
            dur[2] = f'0{dur[2]}'  # Adding 0 if the seconds are less than 10

        progress_string = f'{hours_between}:{minutes_between}:{seconds_between}/{":".join(dur)}'
        # Response embed
        embed = discord.Embed(description='Now Playing', colour=discord.Colour.dark_teal())
        embed.set_thumbnail(url=video["snippet"]["thumbnails"]["high"]["url"])
        embed.add_field(
            name='Track Name:',
            value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]}) BY [{video["snippet"]["channelTitle"]}](https://youtube.com/channel/{video["snippet"]["channelId"]})',
            inline=False
        )
        embed.add_field(name='Progress:', value=progress_string, inline=False)
        embed.set_footer(
            text=f'Duration: {video["contentDetails"]["duration"].strip("PT")}, 🎥: {video["statistics"]["viewCount"]}, 👍: {video["statistics"]["likeCount"] if "likeCount" in video["statistics"].keys() else "Could not fetch likes"}')
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        await ctx.send(embed=embed)

    @nowplaying.error
    async def nowplaying_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the nowplaying command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, (PlayerNotConnectedToVoiceChannel, NoAudioPlaying)):
            await send_error_embed(ctx, f'Error: `{error}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the nowplaying command! The owner has been notified.')
            await inform_owner(self.bot, error)

    # Remove command
    @commands.command(aliases=['rm', 'del', 'delete'], description='Removes a certain track from the queue',
                      usage='remove <track_number>')
    async def remove(self, ctx: commands.Context, track_number: int):
        """
        Removes a certain track from the queue.
        
        :param ctx: The context of the command.
        :param track_number: The track number to remove.
        
        :type ctx: commands.Context
        :type track_number: int
        
        :return: None
        :rtype: None
        """
        if not ctx.author.voice:  # Checking if the user is in a voice channel
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = ctx.guild.voice_client  # Getting the voice client

        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if vc.channel != ctx.author.voice.channel:
            raise AuthorInDifferentVoiceChannel('You are not connected to the same voice channel as the player')

        queue_len = len(self.sql.select(elements=['title'], table='queue', where=f"guild_id = '{ctx.guild.id}'"))
        if queue_len == 0:
            raise NoTrack('There are no tracks in the queue')
        if track_number < 1 or track_number > queue_len:
            raise NotInRange('The track number is not in the range of the queue')

        # Removing the track from the queue
        remove = self.sql.select(elements=['title', 'url', 'source'], table='queue',
                                 where=f"guild_id = '{ctx.guild.id}'")
        remove_title = remove[track_number - 1][0].replace("'", "''")
        remove_url = remove[track_number - 1][1]
        if len(remove) > 1:
            self.sql.delete(table='queue',
                            where=f"guild_id = '{ctx.guild.id}' AND source = '{remove[track_number - 1][2]}' AND title = '{remove_title}'")
        else:
            self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}' AND title = '{remove_title}'")

        # Response embed
        remove_title = remove_title.replace("''", "'")
        embed = discord.Embed(description=f'Removed **[{remove_title}]({remove_url})** from the queue',
                              colour=discord.Colour.random())
        await ctx.send(embed=embed)

    # Error in removing a track
    @remove.error
    async def remove_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the remove command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, (AuthorNotConnectedToVoiceChannel, PlayerNotConnectedToVoiceChannel, NoTrack, NotInRange,
                              AuthorInDifferentVoiceChannel)):
            await send_error_embed(ctx, f'Error: `{error}`')
        elif isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   f'Specify the track to be removed\n\nProper Usage: `{self.bot.get_command("remove").usage}`')
        elif isinstance(error, commands.BadArgument):
            await send_error_embed(ctx,
                                   f'Enter a valid number\n\nProper Usage: `{self.bot.get_command("remove").usage}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the remove command! The owner has been notified.')
            await inform_owner(self.bot, error)

    # Lyrics command
    @commands.command(aliases=['ly'],
                      description='Gets the lyrics of the current track\nUse `-lyrics <song name>` to get the lyrics of a specific song\nAnd -lyrics to get the lyrics of the current playing track',
                      usage='-lyrics <query>')
    async def lyrics(self, ctx: commands.Context, *, query: str = None):
        """
        Gets the lyrics of the current track or the query if provided.
        
        :param ctx: The context of the command.
        :param query: The query to search for.

        :type ctx: commands.Context
        :type query: str | None

        :return: None
        :rtype: None
        """
        async with ctx.typing():
            vc = ctx.guild.voice_client
            lyrics = ''
            title = ''

            # If the query is of type None, this means the user wants the lyrics of the current playing track
            if query is None:
                # Basic responses to false calls
                if vc is None:
                    raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

                if not vc.is_playing():
                    raise NoAudioPlaying('No audio is being played')
                query = self.now_playing[ctx.guild.id]

            try:
                # Gets the lyrics of the current track
                extract_lyrics = lyrics_extractor.SongLyrics(os.getenv('json_api_key'), os.getenv('engine_id'))
                song = extract_lyrics.get_lyrics(query)
                title, lyrics = song['title'], song['lyrics']

                # Response embed
                embed = discord.Embed(title=title, description=lyrics, colour=discord.Colour.blue(),
                                      timestamp=datetime.datetime.now())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                embed.set_footer(text=f'Powered by genius.com and google custom search engine\nQuery: {query}')

                await ctx.send(embed=embed)

            # Lyrics not found exception
            except lyrics_extractor.lyrics.LyricScraperException:
                await send_error_embed(ctx,
                                       description=f'Lyrics for the song {query} could not be found')

            # Some songs' lyrics are too long to be sent, in that case, a text file is sent
            except discord.HTTPException:
                with open(f'lyrics_{ctx.author.id}.txt', 'w') as f:
                    f.write(f'{title}\n\n')

                    f.write(lyrics)
                    f.write(f'\n\nPowered by genius.com and google custom search engine\nQuery: {query}')

                await ctx.send(file=discord.File(f'lyrics_{ctx.author.id}.txt', 'lyrics.txt'))
                os.remove(f'lyrics_{ctx.author.id}.txt')

    # Error in lyrics command
    @lyrics.error
    async def lyrics_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the lyrics command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, (PlayerNotConnectedToVoiceChannel, NoAudioPlaying)):
            await send_error_embed(ctx, f'Error: `{error}`')
        elif isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   f'Specify the song to get the lyrics of\n\nProper Usage: `{self.bot.get_command("lyrics").usage}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the lyrics command! The owner has been notified.')
            await inform_owner(self.bot, error)

    loop = SlashCommandGroup('loop', 'Manage loops')

    @loop.command(name='enable', description='Enable loop')
    async def loop_enable(self, ctx: discord.ApplicationContext,
                          mode: Option(str, description='Loop mode', required=True, choices=['Track', 'Playlist']),
                          limit: Option(int, description='The number of times to loop. Leave blank for infinite loop',
                                        required=False, default=None)):
        """
        Enable loop.

        :param ctx: The context of the command.
        :param mode: The loop mode.
        :param limit: The number of times to loop.

        :type ctx: discord.ApplicationContext
        :type mode: str
        :type limit: int | None

        :return: None
        :rtype: None
        """
        await ctx.interaction.response.defer()

        # Basic responses to false calls
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = ctx.guild.voice_client

        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if not vc.is_playing():
            raise NoAudioPlaying('No audio is being played')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not connected to the same voice channel as the player')

        # Check if loop is already enabled
        if self.sql.select(['*'], 'loop', f"guild_id = '{ctx.guild.id}'"):
            await ctx.respond('Loop is already enabled!', ephemeral=True)
            return

        self.loop_limit[ctx.guild.id] = limit

        # Insert only in loop
        if mode == 'Track':
            self.sql.insert('loop', ['guild_id', 'source', 'title', 'url'],
                            [f"'{ctx.guild.id}'", f"'{self.source[ctx.guild.id]}'",
                             f"'{self.now_playing[ctx.guild.id]}'", f"'{self.now_playing_url[ctx.guild.id]}'"])

        # Insert in playlist and loop
        else:
            items = self.sql.select(['source', 'title', 'url'], 'queue', f"guild_id='{ctx.guild.id}'")
            self.sql.insert('loop', ['guild_id', 'source', 'title', 'url'],
                            [f"'{ctx.guild.id}'", f"'{self.source[ctx.guild.id]}'",
                             f"'{self.now_playing[ctx.guild.id]}'", f"'{self.now_playing_url[ctx.guild.id]}'"])

            self.sql.insert('playlist', ['guild_id', 'source', 'title', 'url', 'position'],
                            [f"'{ctx.guild.id}'", f"'{self.source[ctx.guild.id]}'",
                             f"'{self.now_playing[ctx.guild.id]}'", f"'{self.now_playing_url[ctx.guild.id]}'", "'0'"])

            for index, item in enumerate(items):
                self.sql.insert('playlist', ['guild_id', 'source', 'title', 'url', 'position'],
                                [f"'{ctx.guild.id}'", f"'{item[0]}'", f"'{item[1]}'", f"'{item[2]}'", f"'{index + 1}'"])

        await ctx.respond(
            embed=discord.Embed(description=f'Loop enabled for {mode}', colour=discord.Colour.blue()).set_footer(
                text=f'Limit: {limit or "Infinite"}'))

    @loop_enable.error
    async def loop_enable_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the loop enable command.

        :param ctx: The context of the command.
        :param error: The error that occurred.

        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError

        :return: None
        :rtype: None
        """
        if isinstance(error, (AuthorNotConnectedToVoiceChannel, PlayerNotConnectedToVoiceChannel, NoAudioPlaying,
                              AuthorNotConnectedToVoiceChannel)):
            await ctx.respond(f'Error: `{error}`', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the loop enable command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @loop.command(name='disable', description='Disable loop')
    async def loop_disable(self, ctx: discord.ApplicationContext):
        """
        Disable loop.

        :param ctx: The context of the command.

        :type ctx: discord.ApplicationContext

        :return: None
        :rtype: None
        """
        await ctx.interaction.response.defer()

        # Basic responses to false calls
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = ctx.guild.voice_client

        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if not vc.is_playing():
            raise NoAudioPlaying('No audio is being played')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not connected to the same voice channel as the player')

        # Check if loop is enabled first
        if not self.sql.select(['*'], 'loop', f"guild_id = '{ctx.guild.id}'"):
            await ctx.respond('Loop is not enabled!', ephemeral=True)
            return

        # Delete from database
        sources = self.sql.select(['source'], 'queue', f"guild_id = '{ctx.guild.id}'")
        for source in sources:
            self.sql.delete('queue', f"guild_id = '{ctx.guild.id}' AND source = '{source[0]}'")

        self.sql.delete('loop', f"guild_id = '{ctx.guild.id}'")
        self.sql.delete('playlist', f"guild_id = '{ctx.guild.id}'")

        # Delete from memory
        del self.loop_limit[ctx.guild.id]

        # Respond
        await ctx.respond(embed=discord.Embed(description='Loop disabled', colour=discord.Colour.blue()))

    @loop_disable.error
    async def loop_disable_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the loop disable command.

        :param ctx: The context of the command.
        :param error: The error that occurred.

        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError

        :return: None
        :rtype: None
        """
        if isinstance(error, (PlayerNotConnectedToVoiceChannel, NoAudioPlaying, AuthorNotConnectedToVoiceChannel,
                              AuthorInDifferentVoiceChannel)):
            await ctx.respond(f'Error: `{error}`', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the loop disable command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    # Volume command
    @commands.command(name='volume', aliases=['vol'], description='Set the volume of the voice client',
                      usage='volume <0-200>')
    async def volume_(self, ctx: commands.Context, volume: int):
        """
        Sets the volume of the voice client.
        
        :param ctx: The context of the command.
        :param volume: The volume to set.
        
        :type ctx: commands.Context
        :type volume: int
        
        :return: None
        :rtype: None
        """
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        if volume < 0 or volume > 200:  # Checks if the volume argument is outside the range
            raise NotInRange('The volume must be between 0 and 200')

        vc = ctx.guild.voice_client

        if not vc:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to the voice channel')

        if not vc.is_playing():
            raise NoAudioPlaying('No audio is being playing')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not connected to the same voice channel as the player')

        self.volume[ctx.guild.id] = volume
        vc.source.volume = volume / 100
        await ctx.send(embed=discord.Embed(description=f'Volume set to {volume}%', colour=discord.Colour.blue()))

    # Error in the volume command
    @volume_.error
    async def volume_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the volume command.
        
        :param ctx: The context of the command.
        :param error: The error that occurred.
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify the volume\n\nProper Usage: `{self.bot.get_command("volume").usage}`')
        elif isinstance(error, commands.BadArgument):
            await send_error_embed(ctx,
                                   description=f'Volume must be a whole number between 0 and 200\n\nProper Usage: `{self.bot.get_command("volume").usage}`')
        elif isinstance(error, (
                NoAudioPlaying, AuthorInDifferentVoiceChannel, PlayerNotConnectedToVoiceChannel, NotInRange,
                AuthorNotConnectedToVoiceChannel)):
            await send_error_embed(ctx, f'Error: `{error}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the volume command! The owner has been notified.')
            await inform_owner(self.bot, error)


# Setup
def setup(bot: commands.Bot):
    """
    Loads the Cog.
    
    :param bot: The bot object.
    
    :type bot: commands.Bot
    
    :return: None
    :rtype: None
    """
    bot.add_cog(Music(bot))

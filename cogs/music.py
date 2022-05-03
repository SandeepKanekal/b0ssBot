# Requirements for running this module:
# Linux/Mac - Install in terminal
# Windows - Add FFmpeg to PATH (https://windowsloop.com/install-ffmpeg-windows-10/)
import contextlib
import discord
import youtube_dl
import os
import asyncio
import datetime
import lyrics_extractor
from sql_tools import SQL
from discord.ext import commands
from discord.ext.commands import CommandError
from tools import send_error_embed, get_video_stats, format_time
from youtube_dl import YoutubeDL


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

    def __init__(self, bot):
        self.bot = bot
        self.now_playing = {}  # Stores the title of the currently playing track
        self.now_playing_url = {}  # Stores the url  of the currently playing track
        self.start_time = {}  # Stores the time when the track started playing
        self.source = {}  # Stores the source of the currently playing track
        self.volume = {}  # Stores the volume of the currently playing track
        self._ydl_options = {'format': 'bestaudio', 'noplaylist': 'True'}  # Options for youtube_dl
        self._ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                                'options': '-vn'}  # Options for ffmpeg
        self.sql = SQL('b0ssbot')  # SQL object

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState) -> None:
        with contextlib.suppress(AttributeError):
            # The player is disconnected when there is no one in the voice channel
            vc = discord.utils.get(self.bot.voice_clients, guild=member.guild)
            if len(before.channel.members) == 1 and after != before:
                await vc.disconnect()
                self.sql.delete(table='queue', where=f"guild_id = '{member.guild.id}'")
                self.sql.delete(table='loop', where=f"guild_id = '{member.guild.id}'")

    # Searches YouTube for the item.
    # Possible errors:
    # IndexError - Occurs when there is no proper video
    # youtube_dl.utils.DownloadError - Occurs in case the video cannot be accessed without an account, such as age restrictions
    def search_yt(self, item):
        with YoutubeDL(self._ydl_options) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]  # Get the required details
            except youtube_dl.utils.DownloadError as e:
                return e

        return {'source': info['formats'][0]['url'], 'title': info['title'],
                'url': info['webpage_url'], 'channel_title': info['channel'], 'channel_id': info['channel_id'],
                'view_count': info['view_count'], 'like_count': info['like_count'], 'thumbnail': info['thumbnail'],
                'duration': info['duration']}  # Return required details

    async def _send_embed_after_track(self, ctx):
        """
        Sends an embed after the track has finished playing
        """
        if self.sql.select(elements=['*'], table='queue', where=f"guild_id = '{ctx.guild.id}'"):
            track = self.sql.select(elements=['title', 'url'], table='queue', where=f"guild_id = '{ctx.guild.id}'")[0]
            embed = discord.Embed(title='Now Playing', description=f"[{track[0]}]({track[1]})",
                                  colour=discord.Colour.green())
        elif self.sql.select(elements=['*'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
            track = self.sql.select(elements=['title', 'url'], table='loop', where=f"guild_id = '{ctx.guild.id}'")[0]
            embed = discord.Embed(title='Now Playing', description=f"[{track[0]}]({track[1]})",
                                  colour=discord.Colour.green())
        else:
            embed = discord.Embed(description='Queue is over', colour=discord.Colour.red())
            embed.set_footer(text='Use the play command to add tracks')

        await ctx.send(embed=embed)

    # The play_next function is used when the player is already playing, this function is invoked when the player is done playing one of the tracks in the queue
    def play_next(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)  # Get the voice client
        asyncio.run_coroutine_threadsafe(self._send_embed_after_track(ctx), self.bot.loop)  # Send the embed
        if self.sql.select(['title'], 'queue',
                           f"guild_id = '{ctx.guild.id}'"):  # Check if there are any tracks in the queue
            self._play_next(ctx, vc)
        elif self.sql.select(['title'], 'loop', f"guild_id = '{ctx.guild.id}'"):  # Check if there are any loops
            self._play_next(ctx, vc)
        else:
            # If no track is present to play, all the variables store None
            self.now_playing[ctx.guild.id] = None
            self.now_playing_url[ctx.guild.id] = None
            self.start_time[ctx.guild.id] = None
            self.source[ctx.guild.id] = None

    def _play_next(self, ctx, vc):
        # Get the url to be played from the loop or queue table
        track = self.sql.select(['source', 'title', 'url'], 'loop', f"guild_id = '{ctx.guild.id}'") or self.sql.select(
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

    # The play_music function is used to play music when the player is not connected or nothing is being played
    async def play_music(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)  # Get the voice client
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
        print(track)  # Print the track that is being played

        vc.play(discord.FFmpegPCMAudio(m_url, **self._ffmpeg_options), after=lambda e: self.play_next(ctx))
        vc.source = discord.PCMVolumeTransformer(vc.source, volume=self.volume[ctx.guild.id] / 100)
        # Delete the track as it is being played
        if not self.sql.select(elements=['*'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
            title = track[0][1]
            title = title.replace("'", "''")
            self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}' AND title = '{title}'")

    @commands.command(aliases=['j', 'summon'], description='Joins the voice channel you are in', usage='join')
    async def join(self, ctx):
        if ctx.author.voice is None:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')
        voice_channel = ctx.author.voice.channel  # Get the voice channel
        try:
            await voice_channel.connect()
        except discord.ClientException as e:
            raise AlreadyConnectedToVoiceChannel('Already connected to a voice channel') from e

    @join.error
    async def join_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # The play or add command is just used for searching the internet, as well as appending the necessary information to the queue variables
    @commands.command(aliases=['p', 'add'],
                      description='Plays the searched song from YouTube or adds it to the queue, query can be a link or a search term',
                      usage='play <query>')
    async def play(self, ctx, *, query: str):

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)  # Get the voice client

        if ctx.author.voice is None:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')
        voice_channel = ctx.author.voice.channel  # Get the voice channel

        if self.sql.select(elements=['*'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
            # Do not let adding of new tracks if looping is enabled
            raise LoopingEnabled('Looping is enabled')

        if vc is None:
            await voice_channel.connect()
        elif vc.is_connected() and vc.channel != voice_channel:
            raise AuthorInDifferentVoiceChannel('You are in a different voice channel')

        if vc and vc.is_paused():
            raise PlayerPaused('The player is paused')

        song = self.search_yt(query)  # Get the track details
        if isinstance(song, youtube_dl.utils.DownloadError):
            await send_error_embed(ctx, description=f'Error: {song}')
            return
        if ctx.guild.id not in self.volume.keys():
            self.volume[ctx.guild.id] = 100
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
        song["title"] = song["title"].replace("''", "'")  # Replace the single quotes back for the response
        embed = discord.Embed(colour=discord.Colour.blue()).set_thumbnail(
            url=song['thumbnail'])
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.add_field(
            name='Song added to queue',
            value=f'[{song["title"]}]({song["url"]}) BY [{song["channel_title"]}](https://youtube.com/channel/{song["channel_id"]})'
        )
        embed.set_footer(
            text=f'Duration: {format_time(song["duration"])}, 📽️: {song["view_count"]}, 👍: {song["like_count"]}'
        )
        await ctx.send(
            'In case the music is not playing, please use the play command again since the access to the music player could be denied.',
            embed=embed
        )

        if not ctx.voice_client.is_playing():
            # Plays the music
            await self.play_music(ctx)

    # Sometimes, videos are not available, a response is required to inform the user
    @play.error
    async def play_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify a query\n\nProper Usage: `{self.bot.get_command("play").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    @commands.command(aliases=['q'], description='Shows the music queue', usage='queue')
    async def queue(self, ctx):
        # This command does not stop users outside the voice channel from accessing the command since it is a view-only command
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if vc is None:  # Player is not connected
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if not vc.is_playing():
            raise NoAudioPlaying('No audio is playing')

        if track := self.sql.select(elements=['title', 'url'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
            # If looping is enabled, show the looping track
            embed = discord.Embed(colour=discord.Colour.blue())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed.add_field(
                name='Looping',
                value=f'[{track[0][0]}]({track[0][1]})'
            )
            video = get_video_stats(track[0][1])
            embed.set_footer(
                text=f'Duration: {video["contentDetails"]["duration"].strip("PT")}, 📽️: {video["statistics"]["viewCount"]}, 👍: {video["statistics"]["likeCount"] if "likeCount" in video["statistics"].keys() else "Could not fetch likes"}'
            )
            await ctx.send(embed=embed)
            return

        # Response embed
        embed = discord.Embed(title='Music Queue', color=discord.Colour.dark_teal())
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        queue = self.sql.select(elements=['title', 'url'], table='queue', where=f"guild_id = '{ctx.guild.id}'")
        embed.add_field(name='Now Playing:',
                        value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})',
                        inline=False)
        for index, item in enumerate(queue):
            embed.add_field(name=f'Track Number {index + 1}', value=f'[{item[0]}]({item[1]})', inline=False)
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    @queue.error
    async def queue_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Self-explanatory
    @commands.command(name='pause', description='Pauses the current track', usage='pause')
    async def pause(self, ctx):
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if vc.is_paused():
            raise PlayerPaused('Player is already paused')

        if not vc.is_playing():
            raise NoAudioPlaying('No audio is playing')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

        vc.pause()
        # Response embed
        embed = discord.Embed(
            description=f'Paused [{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})',
            colour=discord.Colour.green())
        await ctx.send(embed=embed)

    @pause.error
    async def pause_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Self-explanatory
    @commands.command(aliases=['unpause', 'up'], description='Resumes the paused track', usage='resume')
    async def resume(self, ctx):
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if vc.is_playing():
            raise PlayerPlaying('Player is already playing')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

        vc.resume()
        # Response embed
        embed = discord.Embed(
            description=f'Resumed [{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})',
            colour=discord.Colour.green())
        await ctx.send(embed=embed)

    @resume.error
    async def resume_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Skips the current track
    @commands.command(name="skip", description="Skips the current track", usage="skip")
    async def skip(self, ctx):
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

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
    async def skip_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Stop command
    @commands.command(name='stop', description='Stops the current track and clears the queue', usage='stop')
    async def stop(self, ctx):
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if not vc.is_playing():
            raise NoAudioPlaying('No audio is playing')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

        embed = discord.Embed(description='Stopped', colour=discord.Colour.green())
        await ctx.send(embed=embed)
        vc.stop()  # Stopping the player

        # Clearing the queue variables
        self.now_playing[ctx.guild.id] = None
        self.now_playing_url[ctx.guild.id] = None

        # Clearing the queue for the guild
        self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}'")
        self.sql.delete(table='loop', where=f"guild_id = '{ctx.guild.id}'")

    @stop.error
    async def stop_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Disconnect command
    @commands.command(aliases=['dc', 'leave'], description="Disconnects the player from the voice channel",
                      usage='disconnect')
    async def disconnect(self, ctx):
        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not in the same voice channel as the player')

        embed = discord.Embed(description='Disconnected', colour=discord.Colour.green())
        await ctx.send(embed=embed)
        await vc.disconnect()  # Disconnecting the player

        with contextlib.suppress(KeyError):
            # Clearing the queue variables
            self.now_playing.pop(ctx.guild.id)
            self.now_playing_url.pop(ctx.guild.id)
            self.volume.pop(ctx.guild.id)

        # Clearing the queue for the guild
        self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}'")
        self.sql.delete(table='loop', where=f"guild_id = '{ctx.guild.id}'")

    @disconnect.error
    async def disconnect_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Nowplaying command
    @commands.command(aliases=['np', 'now'], description='Shows the current track being played', usage='nowplaying')
    async def nowplaying(self, ctx):
        # This command does not prevent users from outside the voice channel from accessing the command since it is view-only
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

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
    async def nowplaying_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Remove command
    @commands.command(aliases=['rm', 'del', 'delete'], description='Removes a certain track from the queue',
                      usage='remove <track_number>')
    async def remove(self, ctx, track_number: int):
        if not ctx.author.voice:  # Checking if the user is in a voice channel
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)  # Getting the voice client

        if vc is None:
            raise PlayerNotConnectedToVoiceChannel('The player is not connected to a voice channel')

        if vc.channel != ctx.author.voice.channel:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to the same voice channel as the player')

        queue_len = len(self.sql.select(elements=['title'], table='queue', where=f"guild_id = '{ctx.guild.id}'"))
        if queue_len == 0:
            raise NoTrack('There are no tracks in the queue')
        if track_number < 1 or track_number > queue_len:
            raise NotInRange('The track number is not in the range of the queue')

        # Removing the track from the queue
        remove = self.sql.select(elements=['title', 'url', 'source'], table='queue',
                                 where=f"guild_id = '{ctx.guild.id}'")
        remove_title = remove[track_number - 1][0]
        remove_url = remove[track_number - 1][1]
        if len(remove) > 1:
            self.sql.delete(table='queue',
                            where=f"guild_id = '{ctx.guild.id}' AND source = '{remove[track_number - 1][2]}' AND title = '{remove_title}'")
        else:
            self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}' AND title = '{remove_title}'")

        # Response embed
        embed = discord.Embed(description=f'Removed **[{remove_title}]({remove_url})** from the queue',
                              colour=discord.Colour.random())
        await ctx.send(embed=embed)

    # Error in removing a track
    @remove.error
    async def remove_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Specify the track to be removed\n\nProper Usage: {self.bot.get_command("remove").usage}.')
        elif isinstance(error, commands.BadArgument):
            await send_error_embed(ctx,
                                   description=f'Enter a valid number\n\nProper Usage: {self.bot.get_command("remove").usage}.')
        else:
            await send_error_embed(ctx, description=f'Error: `{error}`')

    # Lyrics command
    @commands.command(aliases=['ly'],
                      description='Gets the lyrics of the current track\nUse `-lyrics <song name>` to get the lyrics of a specific song\nAnd -lyrics to get the lyrics of the current playing track',
                      usage='-lyrics <query>')
    async def lyrics(self, ctx, *, query: str = None):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
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
            embed = discord.Embed(title=title, description=lyrics,
                                  colour=discord.Colour.blue())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed.set_footer(text=f'Powered by genius.com and google custom search engine\nQuery: {query}')
            embed.timestamp = datetime.datetime.now()
            await ctx.send(embed=embed)

        # Lyrics not found exception
        except lyrics_extractor.lyrics.LyricScraperException:
            await send_error_embed(ctx,
                                   description=f'Lyrics for the song {query} could not be found')

        # Some songs' lyrics are too long to be sent, in that case, a text file is sent
        except discord.HTTPException:
            with open('lyrics.txt', 'w') as f:
                f.write(f'Lyrics for the song {title}\n\n')
                f.write(lyrics)
                f.write(f'\n\nPowered by genius.com and google custom search engine\nQuery: {query}')
            await ctx.send(file=discord.File('lyrics.txt'))
            os.remove('lyrics.txt')

    # Error in lyrics command
    @lyrics.error
    async def lyrics_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Repeat/Loop command
    @commands.command(aliases=['repeat'], description='Use 0(false) or 1(true) to enable or disable loop mode', usage='loop <0/1>')
    async def loop(self, ctx, mode: int):
        # Basic responses to false calls
        if mode not in [0, 1]:  # Checks if the mode argument is valid
            await send_error_embed(ctx, description='The argument must be 0(disable loop) or 1(enable loop)')
            return

        if bool(mode) == bool(self.sql.select(elements=['*'], table='loop',
                                              where=f"guild_id = '{ctx.guild.id}'")):  # Checks if the loop mode is already set
            await send_error_embed(ctx, description=f'Loop mode already set to {bool(mode)}')
            return

        if not ctx.author.voice:
            raise AuthorNotConnectedToVoiceChannel('You are not connected to a voice channel')

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not vc.is_playing():
            raise NoAudioPlaying('No audio is being played')

        if ctx.author.voice.channel != vc.channel:
            raise AuthorInDifferentVoiceChannel('You are not connected to the same voice channel as the player')

        title = self.now_playing[ctx.guild.id]
        title = title.replace("'", "''")
        # Delete/Insert into the loop table
        if self.sql.select(elements=['*'], table='loop', where=f"guild_id = '{ctx.guild.id}'") and not bool(mode):
            self.sql.delete(table='loop', where=f"guild_id = '{ctx.guild.id}'")
            self.sql.delete(table='queue',
                            where=f"guild_id = '{ctx.guild.id}' AND title = '{title}'")
        else:
            self.sql.insert(table='loop', columns=['guild_id', 'source', 'title', 'url'],
                            values=[f"'{ctx.guild.id}'", f"'{self.source[ctx.guild.id]}'",
                                    f"'{title}'", f"'{self.now_playing_url[ctx.guild.id]}'"])
        await ctx.send(embed=discord.Embed(description=f'Loop mode set to {bool(mode)}', colour=discord.Colour.blue()))

    # Error in the loop command
    @loop.error
    async def loop_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify the mode\n\nProper Usage: `{self.bot.get_command("loop").usage}`')
        elif isinstance(error, commands.BadArgument):
            await send_error_embed(ctx,
                                   description=f'Mode can be either `0` or `1`\n\nProper Usage: `{self.bot.get_command("loop").usage}`')
        else:
            await send_error_embed(ctx, description=f'Error: `{error}`')

    # Volume command
    @commands.command(aliases=['vol'], description='Set the volume of the bot', usage='volume <0-200>')
    async def volume(self, ctx, volume: int):
        if volume < 0 or volume > 200:  # Checks if the volume argument is outside the range
            raise NotInRange('The volume must be between 0 and 200')

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

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
    @volume.error
    async def volume_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify the volume\n\nProper Usage: `{self.bot.get_command("volume").usage}`')
        elif isinstance(error, commands.BadArgument):
            await send_error_embed(ctx,
                                   description=f'Volume must be a whole number between 0 and 200\n\nProper Usage: `{self.bot.get_command("volume").usage}`')
        else:
            await send_error_embed(ctx, description=f'Error: `{error}`')


# Setup
def setup(bot):
    bot.add_cog(Music(bot))

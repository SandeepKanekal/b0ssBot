# Requirements for running this module:
# Linux/Mac - Install in terminal
# Windows - Add FFmpeg to PATH (https://windowsloop.com/install-ffmpeg-windows-10/)
import contextlib
import discord
import youtube_dl
import os
import datetime
import lyrics_extractor
from sql_tools import SQL
from googleapiclient.discovery import build
from discord.ext import commands
from youtube_dl import YoutubeDL


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description: str) -> None:
    # Response embed
    embed = discord.Embed(description=description, colour=discord.Colour.red())
    await ctx.send(embed=embed)


def get_video_stats(url: str) -> dict:
    """
    Gets the video stats from the url
    """
    youtube = build('youtube', 'v3', developerKey=os.environ.get('youtube_api_key'))
    video_id = url.split('v=')[1]
    response = youtube.videos().list(id=video_id, part='snippet,statistics,contentDetails').execute()
    return response['items'][0]


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.now_playing = {}  # Stores the title of the currently playing track
        self.now_playing_url = {}  # Stores the url  of the currently playing track
        self.start_time = {}  # Stores the time when the track started playing
        self.source = {}  # Stores the source of the currently playing track
        self._ydl_options = {'format': 'bestaudio', 'noplaylist': 'True'}
        self._ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                                'options': '-vn'}
        self.sql = SQL('b0ssbot')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState) -> None:
        with contextlib.suppress(
                AttributeError):  # The player is disconnected when there is no one in the voice channel
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
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
            except IndexError:
                return
            except youtube_dl.utils.DownloadError as e:
                return e

        return {'source': info['formats'][0]['url'], 'title': info['title'], 'url': info['webpage_url']}

    # The play_next function is used when the player is already playing, this function is invoked when the player is done playing one of the songs in the queue
    def play_next(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if self.sql.select(['title'], 'queue', f"guild_id = '{ctx.guild.id}'"):
            self._play_next(ctx, vc)
        elif self.sql.select(['title'], 'loop', f"guild_id = '{ctx.guild.id}'"):
            self._play_next(ctx, vc)
        else:
            self.now_playing[ctx.guild.id] = None
            self.now_playing_url[ctx.guild.id] = None
            self.start_time[ctx.guild.id] = None
            self.source[ctx.guild.id] = None

    def _play_next(self, ctx, vc):
        # Get the url to be played
        if self.sql.select(['source', 'title', 'url'], 'loop', f"guild_id = '{ctx.guild.id}'"):
            track = self.sql.select(['source', 'title', 'url'], 'loop', f"guild_id = '{ctx.guild.id}'")
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
        # Play the track
        vc.play(discord.FFmpegPCMAudio(m_url, **self._ffmpeg_options), after=lambda e: self.play_next(ctx))
        # Delete the track from the queue
        if not self.sql.select(elements=['*'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
            title = track[0][1]
            title = title.replace("'", "''")
            self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}' AND title = '{title}'")

    # The play_music function is used to play music when the player is not connected or nothing is being played
    async def play_music(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice_channel = ctx.author.voice.channel
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
        print(track)

        vc.play(discord.FFmpegPCMAudio(m_url, **self._ffmpeg_options), after=lambda e: self.play_next(ctx))
        # Delete the track as it is being played
        if not self.sql.select(elements=['*'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
            title = track[0][1]
            title = title.replace("'", "''")
            self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}' AND title = '{title}'")

    @commands.command(aliases=['j', 'summon'], description='Joins the voice channel you are in')
    async def join(self, ctx):
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await send_error_embed(ctx, description='You are not connected to the voice channel')
            return
        try:
            await voice_channel.connect()
        except discord.ClientException:
            await send_error_embed(ctx, description='Already connected to the voice channel')

    @join.error
    async def join_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # The play or add command is just used for searching the internet, as well as appending the necessary information to the queue variables
    @commands.command(aliases=['p', 'add'], description='Plays the searched song from YouTube or adds it to the queue')
    async def play(self, ctx, *, query=None):
        if query is None:
            await send_error_embed(ctx, description='No query provided')
            return

        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if ctx.author.voice is None:
            await send_error_embed(ctx, description='You are not connected to the voice channel')
            return
        voice_channel = ctx.author.voice.channel

        if self.sql.select(elements=['*'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
            await send_error_embed(ctx, description='Looping is enabled')
            return

        try:
            await voice_channel.connect()
        except discord.ClientException:
            await voice_client.move_to(voice_channel)

        song = self.search_yt(query)
        if isinstance(song, Exception):
            await send_error_embed(ctx, description=f'Error: {song}')
            return
        song["title"] = song["title"].replace("'", "''")

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
        song["title"] = song["title"].replace("''", "'")

        video = get_video_stats(song['url'])
        embed = discord.Embed(colour=discord.Colour.blue()).set_thumbnail(
            url=video['snippet']['thumbnails']['high']['url'])
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.add_field(
            name='Song added to queue',
            value=f'[{song["title"]}]({song["url"]}) BY [{video["snippet"]["channelTitle"]}](https://youtube.com/channel/{video["snippet"]["channelId"]})'
        )
        embed.set_footer(
            text=f'Duration: {video["contentDetails"]["duration"].strip("PT")}, 📽️: {video["statistics"]["viewCount"]}, 👍: {video["statistics"]["likeCount"]}'
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
        await send_error_embed(ctx, description=f'Error: {error}')

    @commands.command(aliases=['q'], description='Shows the music queue')
    async def queue(self, ctx):  # self.music_queue is not used since it is multidimensional
        # This command does not stop users outside the voice channel from accessing the command since it is a view-only command
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if vc is None:  # Player is not connected
            await send_error_embed(ctx, description='The Player is not connected to the voice channel')
            return

        if vc.is_playing():

            if track := self.sql.select(elements=['title', 'url'], table='loop', where=f"guild_id = '{ctx.guild.id}'"):
                embed = discord.Embed(colour=discord.Colour.blue())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                embed.add_field(
                    name='Looping',
                    value=f'[{track[0][0]}]({track[0][1]})'
                )
                video = get_video_stats(track[0][1])
                embed.set_footer(
                    text=f'Duration: {video["contentDetails"]["duration"].strip("PT")}, 📽️: {video["statistics"]["viewCount"]}, 👍: {video["statistics"]["likeCount"]}'
                )
                await ctx.send(embed=embed)
                return

            # Response embed
            embed = discord.Embed(title='Music Queue', color=discord.Colour.dark_teal())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            queue = self.sql.select(elements=['title', 'url'], table='queue', where=f"guild_id = '{ctx.guild.id}'")
            embed.add_field(name='Track Number 0:',
                            value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})',
                            inline=False)
            for index, item in enumerate(queue):
                embed.add_field(name=f'Track Number {index + 1}', value=f'[{item[0]}]({item[1]})', inline=False)
            embed.timestamp = datetime.datetime.now()
            await ctx.send(embed=embed)

        else:
            await send_error_embed(ctx, description='No audio is being played')

    @queue.error
    async def queue_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Self-explanatory
    @commands.command(name='pause', description='Pauses the current track')
    async def pause(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc.is_playing():
                # Response embed
                embed = discord.Embed(
                    description=f'Paused [{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})',
                    colour=discord.Colour.green())
                await ctx.send(embed=embed)
                vc.pause()
            else:
                await send_error_embed(ctx, description='No audio is being played')
        else:
            await send_error_embed(ctx, description='You are not connected to the voice channel')

    @pause.error
    async def pause_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Self-explanatory
    @commands.command(aliases=['unpause', 'up'], description='Resumes the paused track')
    async def resume(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc.is_paused():
                # Response embed
                embed = discord.Embed(
                    description=f'Resumed [{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})',
                    colour=discord.Colour.green())
                await ctx.send(embed=embed)
                vc.resume()
            else:
                await send_error_embed(ctx, description='Audio is being paused')
        else:
            await send_error_embed(ctx, description='You are not connected to the voice channel')

    @resume.error
    async def resume_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Skips the current track
    @commands.command(name="skip", description="Skips the current track")
    async def skip(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

            # Basic responses to false calls
            if vc is None:
                await send_error_embed(ctx, description='The Player is not connected to the voice channel')
                return

            if not vc.is_playing():
                await send_error_embed(ctx, description='No audio is being played')
                return

            if vc is not None:
                # Response embed
                embed = discord.Embed(
                    description=f'Skipped [{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})',
                    colour=discord.Colour.green())
                await ctx.send(embed=embed)
                vc.stop()  # Stopping the player
        else:
            await send_error_embed(ctx, description='You are not connected to the voice channel')

    @skip.error
    async def skip_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Stop command
    @commands.command(name='stop', description='Stops the current track and clears the queue')
    async def stop(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

            # Basic response to false calls
            if vc is None:
                await send_error_embed(ctx, description='The Player is not connected to the voice channel')
                return

            if not vc.is_playing():
                await send_error_embed(ctx, description='No audio is being played')

            else:
                embed = discord.Embed(description='Stopped', colour=discord.Colour.green())
                await ctx.send(embed=embed)
                vc.stop()  # Stopping the player

                # Clearing the queue variables
                self.now_playing[ctx.guild.id] = None
                self.now_playing_url[ctx.guild.id] = None

                # Clearing the queue for the guild
                self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}'")
                self.sql.delete(table='loop', where=f"guild_id = '{ctx.guild.id}'")

        else:
            await send_error_embed(ctx, description='You are not connected to the voice channel')

    @stop.error
    async def stop_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Disconnect command
    @commands.command(aliases=['dc', 'leave'], description="Disconnecting bot from VC")
    async def disconnect(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc is None:
                await send_error_embed(ctx, description='The Player is not connected to the voice channel')

            else:
                embed = discord.Embed(description='Disconnected', colour=discord.Colour.green())
                await ctx.send(embed=embed)
                await vc.disconnect()  # Disconnecting the player

                with contextlib.suppress(KeyError):
                    # Clearing the queue variables
                    self.now_playing.pop(ctx.guild.id)
                    self.now_playing_url.pop(ctx.guild.id)

                # Clearing the queue for the guild
                self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}'")
                self.sql.delete(table='loop', where=f"guild_id = '{ctx.guild.id}'")
        else:
            await send_error_embed(ctx, description='You are not connected to the voice channel')

    @disconnect.error
    async def disconnect_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Nowplaying command
    @commands.command(aliases=['np', 'now'], description='Shows the current track being played')
    async def nowplaying(self, ctx):
        # This command does not prevent users from outside the voice channel from accessing the command since it is view-only
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        # Basic responses to false calls
        if vc is None:
            await send_error_embed(ctx, description='The Player is not connected to the voice channel')
            return

        if not vc.is_playing():
            await send_error_embed(ctx, description='No audio is being played')
            return

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
        embed.add_field(
            name='Track Name:',
            value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]}) BY [{video["snippet"]["channelTitle"]}](https://youtube.com/channel/{video["snippet"]["channelId"]})',
            inline=False
        )
        embed.add_field(name='Progress:', value=progress_string, inline=False)
        embed.set_footer(
            text=f'Duration: {video["contentDetails"]["duration"].strip("PT")}, 🎥: {video["statistics"]["viewCount"]}, 👍: {video["statistics"]["likeCount"]}')
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        await ctx.send(embed=embed)

    @nowplaying.error
    async def nowplaying_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Remove command
    @commands.command(aliases=['rm', 'del', 'delete'], description='Removed a certain track from the queue')
    async def remove(self, ctx, track_number: int):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

            # Basic responses to false calls
            if vc is None:
                await send_error_embed(ctx, description='The Player is not connected to the voice channel')
                return

            queue_len = len(self.sql.select(elements=['title'], table='queue', where=f"guild_id = '{ctx.guild.id}'"))
            if track_number < 1 or track_number > queue_len:
                await send_error_embed(ctx,
                                       description=f'Enter a number between 1 and {queue_len}')
                return

            # Removing the track from the queue
            remove = self.sql.select(elements=['title', 'url'], table='queue', where=f"guild_id = '{ctx.guild.id}'")
            remove_title = remove[0][0]
            remove_url = remove[0][1]
            self.sql.delete(table='queue', where=f"guild_id = '{ctx.guild.id}' AND title = '{remove_title}'")

            # Response embed
            embed = discord.Embed(description=f'Removed **[{remove_title}]({remove_url})** from the queue',
                                  colour=discord.Colour.random())
            await ctx.send(embed=embed)

        else:
            await send_error_embed(ctx, description='You are not connected to the voice channel')

    # Error in removing a track
    @remove.error
    async def remove_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Lyrics command
    @commands.command(aliases=['ly'], description='Gets the lyrics of the current track')
    async def lyrics(self, ctx, *, query=None):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        # If the query is of type None, this means the user wants the lyrics of the current playing track
        if query is None:
            # Basic responses to false calls
            if vc is None:
                await send_error_embed(ctx, description='The player is not connected to a voice channel')

            if not vc.is_playing():
                await send_error_embed(ctx, description='No audio is being played')
                return
            query = self.now_playing[ctx.guild.id]

        try:
            # Gets the lyrics of the current track
            extract_lyrics = lyrics_extractor.SongLyrics(os.getenv('json_api_key'), os.getenv('engine_id'))
            song = extract_lyrics.get_lyrics(query)
            lyrics = song['lyrics']

            # Response embed
            embed = discord.Embed(title=f'Lyrics for {query}', description=lyrics,
                                    colour=discord.Colour.blue())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed.set_footer(text='Powered by genius.com and google custom search engine')
            embed.timestamp = datetime.datetime.now()
            await ctx.send(embed=embed)

        # Lyrics not found exception
        except lyrics_extractor.lyrics.LyricScraperException:
            await send_error_embed(ctx,
                                    description=f'Lyrics for the song {self.now_playing[ctx.guild.id]} could not be found')

        # Some songs' lyrics are too long to be sent, in that case, a text file is sent
        except discord.HTTPException:
            with open('lyrics.txt', 'w') as f:
                f.write(lyrics)
                f.write('\n\nPowered by genius.com and google custom search engine')
            await ctx.send(file=discord.File('lyrics.txt'))
            os.remove('lyrics.txt')

    # Error in lyrics command
    @lyrics.error
    async def lyrics_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Repeat/Loop command
    @commands.command(aliases=['repeat'], description='Use 0(false) or 1(true) to enable or disable loop mode')
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
            await send_error_embed(ctx, description='You are not connected to the voice channel')
            return

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not vc.is_playing():
            await send_error_embed(ctx, description='Nothing is playing')
            return

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
        await send_error_embed(ctx, description=f'Error: {error}')


# Setup
def setup(bot):
    bot.add_cog(Music(bot))

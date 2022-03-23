# Requirements for running this module:
# Linux/Mac - Install in terminal
# Windows - Add FFmpeg to PATH (https://windowsloop.com/install-ffmpeg-windows-10/)
import contextlib
import discord
import pafy
import youtube_dl
import os
import datetime
import lyrics_extractor
import pafy.backend_youtube_dl
from discord.ext import commands
from youtube_dl import YoutubeDL


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description):
    # Response embed
    embed = discord.Embed(description=description, colour=discord.Colour.red())
    await ctx.send(embed=embed)


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.now_playing = {}  # Stores the data in index position of self.music_queue[0][0]['title'] of the guild(currently
        # playing)
        self.title = None  # Used in the play command response
        self.music_queue = []  # Contains the queue list
        self.queue = {}  # Titles for the queue command is stored here
        self.urls = {}  # URLS for the queue command is stored here
        self.now_playing_url = {}  # Stores the data in index position of self.music_queue[0][0]['url'] of the guild(currently
        # playing track's url)
        self.url = None  # Used in the play command response
        self._ydl_options = {'format': 'bestaudio', 'noplaylist': 'True'}
        self._ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                                'options': '-vn'}
        self.repeat = {}  # Stores if the guild has loop enabled
        self.repeat_details = {}  # Stores the details of the first track

    # Searches YouTube for the item.
    # Possible errors:
    # IndexError - Occurs when there is no proper video
    # youtube_dl.utils.DownloadError - Occurs in case the video cannot be accessed without an account, such as age restrictions
    def search_yt(self, item):
        with YoutubeDL(self._ydl_options) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
                self.url = info['webpage_url']
                self.title = info['title']
            except IndexError:
                return
            except youtube_dl.utils.DownloadError as e:
                return e

        return {'source': info['formats'][0]['url'], 'title': info['title'], 'url': info['webpage_url']}

    # The play_next function is used when the player is already playing, this function is invoked when the player is done playing one of the songs in the queue
    def play_next(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice_channel = ctx.author.voice.channel
        if len(self.music_queue):  # The function must not be executed if there is nothing to play
            self._play_next(voice_channel, ctx, vc)
        else:
            # Pop the variables
            # This is done to avoid repetition of the same title in the queue command
            with contextlib.suppress(IndexError):
                self.queue[ctx.guild.id].pop(0)
                self.urls[ctx.guild.id].pop(0)
            self.now_playing[ctx.guild.id] = None
            self.now_playing_url[ctx.guild.id] = None
            self.repeat_details.pop(ctx.guild.id)

    def _play_next(self, voice_channel, ctx, vc):
        # get the url to be played by the player
        index = 0
        for item in self.music_queue:
            # This loop is to ensure the correct url is played for the guild and avoid crossing of the urls being played
            if item[1] == voice_channel:
                break
            index += 1
        m_url = self.music_queue[index][0]['source']
        self.repeat_details[ctx.guild.id] = self.music_queue[index]
        self.now_playing[ctx.guild.id] = self.music_queue[index][0]['title']
        self.now_playing_url[ctx.guild.id] = self.music_queue[index][0]['url']
        with contextlib.suppress(IndexError):
            # The queue is emptied when the stop command is used, hence, it raises IndexError when the player tries to play the music again. Thus, the suppression
            if not self.repeat[ctx.guild.id]:
                self.queue[ctx.guild.id].pop(0)
                self.urls[ctx.guild.id].pop(0)
        # Popping is done to ensure the finished songs are not left in the queue

        vc.play(discord.FFmpegPCMAudio(m_url, **self._ffmpeg_options), after=lambda e: self.play_next(ctx))
        # remove the first element as you are currently playing it
        if not self.repeat[ctx.guild.id]:
            self.music_queue.pop(index)

    # The play_music function is used to play music when the player is not connected or nothing is being played
    async def play_music(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice_channel = ctx.author.voice.channel
        try:
            index = 0
            for index, item in enumerate(self.music_queue):
                # This loop is to ensure the correct url is played for the guild and avoid crossing of the urls being played
                if item[1] == voice_channel:
                    break
            self.now_playing.update({ctx.guild.id: self.music_queue[index][0]['title']})
            self.now_playing_url.update({ctx.guild.id: self.music_queue[index][0]['url']})
            self.repeat_details.update({ctx.guild.id: self.music_queue[index]})
            m_url = self.music_queue[index][0]['source']
            # Popping is done to ensure the finished songs are not left in the queue
        except IndexError:
            return

        # try to connect to voice channel if you are not already connected
        try:
            vc = await self.music_queue[index][1].connect()
        except discord.ClientException:
            await vc.move_to(self.music_queue[index][1])
        print(self.music_queue)

        vc.play(discord.FFmpegPCMAudio(m_url, **self._ffmpeg_options), after=lambda e: self.play_next(ctx))
        # try to pop as you are playing it
        if not self.repeat[ctx.guild.id]:
            self.music_queue.pop(index)
    
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
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await send_error_embed(ctx, description='Connect to a voice channel')
            return

        try:
            await voice_channel.connect()
        except discord.ClientException:
            await voice_client.move_to(voice_channel)

        song = self.search_yt(query)

        if isinstance(song, bool):  # Happens in case the video format is not playable
            await send_error_embed(ctx,
                                   description="Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
            return

        if isinstance(song,
                      youtube_dl.utils.DownloadError):  # Happens if the download request fails. This happens when the video cannot be accessed, for example, age restrictions
            await send_error_embed(ctx, description=f"Could not download the song. Error: {song}")
            return

        else:

            try:
                video = pafy.new(self.url)
            except ValueError:  # The video does not exist if ValueError is raised
                await send_error_embed(ctx,
                                       description='Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.')
                return

            self.music_queue.append([song, voice_channel])
            if ctx.guild.id not in self.repeat.keys():
                self.repeat[ctx.guild.id] = False
            if ctx.guild.id not in self.queue.keys():
                self.queue.update({ctx.guild.id: [self.title]})
                self.urls.update({ctx.guild.id: [self.url]})
            else:
                self.queue[ctx.guild.id].append(self.title)
                self.urls[ctx.guild.id].append(self.url)

            if not ctx.voice_client.is_playing():
                # Plays the music
                await self.play_music(ctx)

            # Response embed
            embed = discord.Embed(colour=discord.Colour.dark_blue())

            if video.username in video.author:
                embed.add_field(name='Song added to queue',
                                value=f'[{self.title}]({self.url}) BY [{video.author}](https://youtube.com/c/{video.author})')
            else:
                embed.add_field(name='Song added to queue',
                                value=f'[{self.title}]({self.url}) BY [{video.author}](https://youtube.com/channel/{video.username})')

            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed.set_thumbnail(url=video.bigthumbhd)
            embed.set_footer(text=f'Duration: {video.duration}, 🎥: {video.viewcount}, 👍: {video.likes}')
            await ctx.send(
                'In case the music is not playing, please use the play command again since the access to the music player could be denied.')
            await ctx.send(embed=embed)

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

            # Response embed
            embed = discord.Embed(description='QUEUE', colour=discord.Colour.dark_teal())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)

            for index, item in enumerate(self.queue[ctx.guild.id]):
                embed.add_field(name=f'Track Number {index}:', value=f'[{item}]({self.urls[ctx.guild.id][index]})',
                                inline=False)

            embed.set_footer(text=f'Loop mode set to {self.repeat[ctx.guild.id]}')
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
                embed = discord.Embed(description=f'Paused [{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})', colour=discord.Colour.green())
                await ctx.send(embed=embed)
                vc.pause()
            else:
                await send_error_embed(ctx, description='Already paused')
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
                embed = discord.Embed(description=f'Resumed [{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})', colour=discord.Colour.green())
                await ctx.send(embed=embed)
                vc.resume()
            else:
                await send_error_embed(ctx, description='No track has been paused')
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
                embed = discord.Embed(description=f'Skipped [{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})', colour=discord.Colour.green())
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
            voice_channel = ctx.author.voice.channel

            # Basic response to false calls
            if vc is None:
                await send_error_embed(ctx, description='The Player is not connected to the voice channel')
                return

            if not vc.is_playing():
                await send_error_embed(ctx, description='No audio is being played')

            else:
                with contextlib.suppress(IndexError):
                    for index, item in enumerate(self.music_queue):
                        # This loop is to ensure the correct url is played for the guild and avoid crossing of the urls being played
                        if item[1] == voice_channel:
                            self.music_queue.pop(index)

                embed = discord.Embed(description='Stopped', colour=discord.Colour.green())
                await ctx.send(embed=embed)
                vc.stop()  # Stopping the player
                # Clearing the queue variables
                self.queue[ctx.guild.id] = []
                self.urls[ctx.guild.id] = []
                self.now_playing[ctx.guild.id] = None
                self.now_playing_url[ctx.guild.id] = None
                with contextlib.suppress(KeyError):
                    self.repeat.pop(ctx.guild.id)

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
            voice_channel = ctx.author.voice.channel
            if vc is None:
                await send_error_embed(ctx, description='The Player is not connected to the voice channel')

            else:
                with contextlib.suppress(IndexError):
                    for index, item in enumerate(self.music_queue):
                        # This loop is to ensure the correct url is played for the guild and avoid crossing of the urls being played
                        if item[1] == voice_channel:
                            self.music_queue.pop(index)

                embed = discord.Embed(description='Disconnected', colour=discord.Colour.green())
                await ctx.send(embed=embed)
                await vc.disconnect()  # Disconnecting the player
                # Clearing the queue variables
                self.urls[ctx.guild.id] = []
                self.queue[ctx.guild.id] = []
                self.now_playing[ctx.guild.id] = None
                self.now_playing_url[ctx.guild.id] = None
                with contextlib.suppress(KeyError):
                    self.repeat.pop(ctx.guild.id)
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

        else:
            # Response embed
            video = pafy.new(url=self.now_playing_url[ctx.guild.id])
            embed = discord.Embed(description='Now Playing', colour=discord.Colour.dark_teal())
            if video.username in video.author:
                embed.add_field(name='Track Name:',
                                value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]}) by [{video.author}](https://youtube.com/c/{video.author})')
            else:
                embed.add_field(name='Track Name:',
                                value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]}) by [{video.author}](https://youtube.com/channel/{video.username})')
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed.set_thumbnail(url=video.bigthumbhd)
            embed.set_footer(text=f'Duration: {video.duration}, 🎥: {video.viewcount}, 👍: {video.likes}')
            await ctx.send(embed=embed)

    @nowplaying.error
    async def nowplaying_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Remove command
    @commands.command(aliases=['rm', 'del', 'delete'], description='Removed a certain track from the queue')
    async def remove(self, ctx, track_number: int):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            voice_channel = ctx.author.voice.channel

            # Basic responses to false calls
            if vc is None:
                await send_error_embed(ctx, description='The Player is not connected to the voice channel')
                return

            if track_number < 1 or track_number > len(self.music_queue):
                await send_error_embed(ctx,
                                       description=f'Enter a number between 1 and {len(self.music_queue[ctx.guild.id])}')
                return

            # Response embed
            embed = discord.Embed(
                description=f'Removed **[{self.queue[ctx.guild.id][track_number]}]({self.urls[ctx.guild.id][track_number]})** from the queue',
                colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

            remove_title = self.queue[ctx.guild.id][track_number]
            for i in range(len(self.music_queue)):
                if self.music_queue[0][1] == voice_channel and self.music_queue[0][0]['title'] == remove_title:
                    self.music_queue.pop(i)

            self.queue[ctx.guild.id].pop(track_number)
            self.urls[ctx.guild.id].pop(track_number)

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

            try:
                # Gets the lyrics of the current track
                query = self.now_playing[ctx.guild.id]
                extract_lyrics = lyrics_extractor.SongLyrics(os.getenv('json_api_key'), os.getenv('engine_id'))
                song = extract_lyrics.get_lyrics(query)
                lyrics = song['lyrics']

                # Response embed
                embed = discord.Embed(title=f'Lyrics for {self.now_playing[ctx.guild.id]}', description=lyrics,
                                      colour=discord.Colour.blue())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                embed.set_footer(text=f'Requested by {ctx.author}', icon_url=str(ctx.author.avatar))
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)

            # Lyrics not found exception
            except lyrics_extractor.lyrics.LyricScraperException:
                await send_error_embed(ctx,
                                       description=f'Lyrics for the song {self.now_playing[ctx.guild.id]} could not be found')

            # Some songs' lyrics are too long to be sent, in that case, this response is sent
            except discord.HTTPException:
                await send_error_embed(ctx,
                                       description=f'The lyrics for {self.now_playing[ctx.guild.id]} is too long to be sent')

        # If there is a query, the user is asking the lyrics for a specific song
        else:
            try:
                # Gets the lyrics
                extract_lyrics = lyrics_extractor.SongLyrics(os.getenv('json_api_key'), os.getenv('engine_id'))
                song = extract_lyrics.get_lyrics(query)
                lyrics = song['lyrics']

                embed = discord.Embed(title=f'Lyrics for {query}', description=lyrics,
                                      colour=discord.Colour.blue())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                embed.set_footer(text=f'Requested by {ctx.author}', icon_url=str(ctx.author.avatar))
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)

            # Lyrics not found exception
            except lyrics_extractor.lyrics.LyricScraperException:
                await send_error_embed(ctx,
                                       description=f'Lyrics for the song {query} could not be found')

            # Some songs' lyrics are too long to be sent, in that case, this response is sent
            except discord.HTTPException:
                await send_error_embed(ctx,
                                       description=f'The lyrics for {query} is too long to be sent')

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

        with contextlib.suppress(KeyError):
            if bool(mode) == self.repeat[ctx.guild.id]:  # Checks if the loop mode is already set
                await send_error_embed(ctx, description=f'Loop mode already set to {bool(mode)}')
                return

        if not ctx.author.voice:
            await send_error_embed(ctx, description='You are not connected to the voice channel')
            return
            
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if self.music_queue and not bool(mode):
            voice_channel = ctx.author.voice.channel
            self.repeat[ctx.guild.id] = bool(mode)
            for index, item in enumerate(self.music_queue):
                if item[1] == voice_channel:
                    self.music_queue.pop(index)
                    break
            
            embed = discord.Embed(
                description=f'Loop mode set to {self.repeat[ctx.guild.id]}',
                colour = discord.Colour.green()
            )
            await ctx.send(embed=embed)
            return

        # This is done when the loop mode has been set to True
        self.repeat[ctx.guild.id] = bool(mode)
        if vc.is_playing():  # Addition of the current track's details to the music queue, in order to loop it. Works only if a track is being played
            music_queue = self.music_queue.copy()
            self.music_queue = []
            self.music_queue.append(self.repeat_details[ctx.guild.id])
            self.music_queue.append(music_queue)
        embed = discord.Embed(
            description=f'Loop mode set to {self.repeat[ctx.guild.id]}\n',
            colour = discord.Colour.green()
        )
        await ctx.send(embed=embed)
    
    # Error in the loop command
    @loop.error
    async def loop_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

# Setup
def setup(bot):
    bot.add_cog(Music(bot))

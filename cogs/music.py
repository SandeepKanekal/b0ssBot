# Add ffmpeg.exe to the "Scripts" folder for proper functioning of the command or use 'sudo apt install ffmpeg' on linux
import discord
import pafy
import youtube_dl
import os
import datetime
import lyrics_extractor
import pafy.backend_youtube_dl
from discord.ext import commands
from youtube_dl import YoutubeDL


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
        self.ydl_options = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}

    # Searches YouTube for the item.
    # Possible errors:
    # IndexError - Occurs when there is no proper video
    # youtube_dl.utils.DownloadError - Occurs in case the video cannot be accessed without an account, such as age restrictions
    def search_yt(self, item):
        with YoutubeDL(self.ydl_options) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
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
        if len(self.music_queue) > 0:  # The function must not be executed if there is nothing to play

            # get the url to be played by the player
            index = 0
            for index, item in enumerate(self.music_queue):
                # This loop is to ensure the correct url is played for the guild and avoid crossing of the urls being played
                if item[1] == voice_channel:
                    break
            m_url = self.music_queue[index][0]['source']
            self.now_playing[ctx.guild.id] = self.music_queue[index][0]['title']
            self.now_playing_url[ctx.guild.id] = self.music_queue[index][0]['url']
            self.queue[ctx.guild.id].pop(0)
            self.urls[ctx.guild.id].pop(0)
            # Popping is done to ensure the finished songs are not left in the queue

            vc.play(discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options), after=lambda e: self.play_next(ctx))
            # remove the first element as you are currently playing it
            self.music_queue.pop(index)

        else:
            # If there is nothing in the queue the variables must be made to contain no value
            try:
                # This is done to avoid repetition of the same title in the queue command
                self.queue[ctx.guild.id].pop(0)
                self.urls[ctx.guild.id].pop(0)
            except IndexError:
                pass
            self.now_playing[ctx.guild.id] = None
            self.now_playing_url[ctx.guild.id] = None

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

        vc.play(discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options), after=lambda e: self.play_next(ctx))
        # try to pop as you are playing it
        self.music_queue.pop(index)

    # The play or add command is just used for searching the internet, as well as appending the necessary information to the queue variables
    @commands.command(aliases=['p', 'add'], description='Plays the searched song from YouTube or adds it to the queue')
    async def play(self, ctx, *, query):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        try:
            voice_channel = ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(description='Connect to a voice channel first!', colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            return

        try:
            await voice_channel.connect()
        except discord.ClientException:
            await voice_client.move_to(voice_channel)

        if voice_channel is not None:
            song = self.search_yt(query)

            if isinstance(song, bool):  # Happens in case the video format is not playable
                embed = discord.Embed(
                    title="Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.",
                    colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            if isinstance(song,
                          youtube_dl.utils.DownloadError):  # Happens if the download request fails. This happens when the video cannot be accessed, for example, age restrictions
                embed = discord.Embed(
                    title=f"Could not download the song. Error: {song}",
                    colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            else:

                try:
                    video = pafy.new(self.url)
                except ValueError:  # The video does not exist if ValueError is raised
                    embed = discord.Embed(
                        title="Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.",
                        colour=discord.Colour.random())
                    embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                    await ctx.send(embed=embed)
                    return

                self.music_queue.append([song, voice_channel])
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

                if video.author == video.username:
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

    @commands.command(aliases=['q'], description='Shows the music queue')
    async def queue(self, ctx):  # self.music_queue is not used since it is multidimensional
        # This command does not stop users outside the voice channel from accessing the command since it is a view-only command
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if vc is None:  # Player is not connected
            embed = discord.Embed(
                description='The player is not connected to a voice channel, use the play command to do so',
                colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            return

        if vc.is_playing():

            # Response embed
            embed = discord.Embed(description='QUEUE', colour=discord.Colour.dark_teal())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)

            for index, item in enumerate(self.queue[ctx.guild.id]):
                embed.add_field(name=f'Track Number {index}:', value=f'[{item}]({self.urls[ctx.guild.id][index]})',
                                inline=False)

            embed.set_footer(text=f'Use the play command if you want to add more audio tracks to the queue\nRequested by {ctx.author}',
                             icon_url=ctx.author.avatar)
            embed.timestamp = datetime.datetime.now()
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(description='No audio is being played', colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed.set_footer(text='Use the play command if you want to add more audio tracks to the queue')
            await ctx.send(embed=embed)

    # Self-explanatory
    @commands.command(name='pause', description='Pauses the current track')
    async def pause(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc.is_playing():
                # Response embed
                embed = discord.Embed(description='Paused', colour=discord.Colour.random())
                embed.add_field(name='Paused Track:',
                                value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})')
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                vc.pause()
            else:
                embed = discord.Embed(description='Already paused', colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description='You are not connected to the voice channel',
                                  colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    # Self-explanatory
    @commands.command(aliases=['unpause'], description='Resumes the paused track')
    async def resume(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc.is_paused():
                # Response embed
                embed = discord.Embed(description='Resumed', colour=discord.Colour.random())
                embed.add_field(name='Resumed Track:',
                                value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})')
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                vc.resume()
            else:
                embed = discord.Embed(description='Nothing has been paused', colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description='You are not connected to the voice channel',
                                  colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    # Skips the current track
    @commands.command(name="skip", description="Skips the current track")
    async def skip(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

            # Basic responses to false calls
            if vc is None:
                embed = discord.Embed(description='The player is not connected to a voice channel',
                                      colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            if not vc.is_playing():
                embed = discord.Embed(description='No audio is being played', colour=discord.Colour.random())
                embed.set_footer(text='Use the play command if you want to add more audio tracks to the queue')
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            if vc is not None:
                vc.stop()  # Stopping the player
                # Response embed
                embed = discord.Embed(description='Skipped', colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                embed.add_field(name='Skipped Track:',
                                value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]})')
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description='You are not connected to the voice channel',
                                  colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    # Stop command
    @commands.command(name='stop', description='Stops the current track and clears the queue')
    async def stop(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            voice_channel = ctx.author.voice.channel

            # Basic response to false calls
            if vc is None:
                embed = discord.Embed(description='The player is not connected to a voice channel',
                                      colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            if not vc.is_playing():
                embed = discord.Embed(description='No audio is being played', colour=discord.Colour.random())
                embed.set_footer(text='Use the play command if you want to add more audio tracks to the queue')
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)

            else:
                for index, item in enumerate(self.music_queue):
                    # This loop is to ensure the correct url is played for the guild and avoid crossing of the urls being played
                    if item[1] == voice_channel:
                        self.music_queue.pop(index)

                embed = discord.Embed(description='Stopped', colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                vc.stop()  # Stopping the player
                # Clearing the queue variables
                self.queue[ctx.guild.id] = []
                self.urls[ctx.guild.id] = []
                self.now_playing[ctx.guild.id] = None
                self.now_playing_url[ctx.guild.id] = None

        else:
            embed = discord.Embed(description='You are not connected to the voice channel',
                                  colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    # Disconnect command
    @commands.command(aliases=['dc', 'leave'], description="Disconnecting bot from VC")
    async def disconnect(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            voice_channel = ctx.author.voice.channel
            if vc is None:
                embed = discord.Embed(description='The player is not connected to a voice channel',
                                      colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)

            else:
                for index, item in enumerate(self.music_queue):
                    # This loop is to ensure the correct url is played for the guild and avoid crossing of the urls being played
                    if item[1] == voice_channel:
                        self.music_queue.pop(index)

                embed = discord.Embed(description='Disconnected', colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                await vc.disconnect()  # Disconnecting the player
                # Clearing the queue variables
                self.urls[ctx.guild.id] = []
                self.queue[ctx.guild.id] = []
                self.now_playing[ctx.guild.id] = None
                self.now_playing_url[ctx.guild.id] = None
        else:
            embed = discord.Embed(description='You are not connected to the voice channel',
                                  colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    # Nowplaying command
    @commands.command(aliases=['np', 'now'], description='Shows the current track being played')
    async def nowplaying(self, ctx):
        # This command does not prevent users from outside the voice channel from accessing the command since it is view-only
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        # Basic responses to false calls
        if vc is None:
            embed = discord.Embed(description='The player is not connected to the voice channel',
                                  colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            return

        if not vc.is_playing():
            embed = discord.Embed(description='No audio is being played', colour=discord.Colour.random())
            embed.set_footer(text='Use the play command if you want to add more audio tracks to the queue')
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            return

        else:
            # Response embed
            video = pafy.new(url=self.now_playing_url[ctx.guild.id])
            embed = discord.Embed(description='Now Playing', colour=discord.Colour.dark_teal())
            if video.author == video.username:
                embed.add_field(name='Track Name:',
                                value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]}) by [{video.author}](https://youtube.com/c/{video.author})')
            else:
                embed.add_field(name='Track Name:',
                                value=f'[{self.now_playing[ctx.guild.id]}]({self.now_playing_url[ctx.guild.id]}) by [{video.author}](https://youtube.com/channel/{video.username})')
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed.set_thumbnail(url=video.bigthumbhd)
            embed.set_footer(text=f'Duration: {video.duration}, 🎥: {video.viewcount}, 👍: {video.likes}')
            await ctx.send(embed=embed)

    # Remove command
    @commands.command(aliases=['rm', 'del', 'delete'], description='Removed a certain track from the queue')
    async def remove(self, ctx, track_number: int):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            voice_channel = ctx.author.voice.channel

            # Basic responses to false calls
            if vc is None:
                embed = discord.Embed(description='The player is not connected to the voice channel',
                                      colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            if track_number < 1 or track_number > len(self.music_queue):
                embed = discord.Embed(description=f'Enter a number between 1 and {len(self.music_queue)}',
                                      colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            # Response embed
            embed = discord.Embed(
                description=f'Removed **[{self.queue[ctx.guild.id][track_number]}]({self.urls[ctx.guild.id][track_number]})** from the queue',
                colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

            remove_title = self.queue[ctx.guild.id][track_number]
            for index, item in enumerate(self.music_queue):
                if item[0] == remove_title and item[1] == voice_channel:
                    self.music_queue.pop(index)

            self.queue[ctx.guild.id].pop(track_number)
            self.urls[ctx.guild.id].pop(track_number)

        else:
            embed = discord.Embed(description='You are not connected to the voice channel',
                                  colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    @commands.command(aliases=['ly'], description='Gets the lyrics of the current track')
    async def lyrics(self, ctx, *, query=None):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        # If the query is of type None, this means the user wants the lyrics of the current playing track
        if query is None:
            # Basic responses to false calls
            if vc is None:
                embed = discord.Embed(description='The player is not connected to the voice channel',
                                      colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            if not vc.is_playing():
                embed = discord.Embed(description='No audio is being played', colour=discord.Colour.random())
                embed.set_footer(text='Use the play command if you want to add more audio tracks to the queue')
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
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
                embed = discord.Embed(
                    description=f'Lyrics for the song {self.now_playing[ctx.guild.id]} could not be found',
                    colour=discord.Colour.red())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)

            # Some songs' lyrics are too long to be sent, in that case, this response is sent
            except discord.HTTPException:
                embed = discord.Embed(
                    description=f'The lyrics for {self.now_playing[ctx.guild.id]} is too long to be sent',
                    colour=discord.Colour.red())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)

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
                embed = discord.Embed(
                    description=f'Lyrics for the song {query} could not be found',
                    colour=discord.Colour.red())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)

            # Some songs' lyrics are too long to be sent, in that case, this response is sent
            except discord.HTTPException:
                embed = discord.Embed(description=f'The lyrics for {query} is too long to be sent',
                                      colour=discord.Colour.red())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)


# Setup
def setup(bot):
    bot.add_cog(Music(bot))

# Add ffmpeg.exe to the "Scripts" folder for proper functioning of the command or use 'sudo apt install ffmpeg' on linux
import discord
import pafy
import youtube_dl
import pafy.backend_youtube_dl
from discord.ext import commands
from youtube_dl import YoutubeDL


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.now_playing = None  # Stores the data in index position of self.music_queue[0][0]['title'](currently
        # playing)
        self.title = None  # Used in the play command response
        self.music_queue = []  # Contains the queue list
        self.queue = []  # Titles for the queue command is stored here
        self.urls = []  # URLS for the queue command is stored here
        self.now_playing_url = None  # Stores the data in index position of self.music_queue[0][0]['url'](currently
        # playing track's url)
        self.url = None  # Used in the play command response
        self.ydl_options = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}

    def search_yt(self, item):
        with YoutubeDL(self.ydl_options) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
                self.url = info['webpage_url']
                self.title = info['title']
                self.urls.append(info['webpage_url'])
                self.queue.append(info['title'])
            except IndexError:
                return
            except youtube_dl.utils.DownloadError as e:
                return e

        return {'source': info['formats'][0]['url'], 'title': info['title'], 'url': info['webpage_url']}

    def play_next(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if len(self.music_queue) > 0:

            # get the first url
            m_url = self.music_queue[0][0]['source']
            self.now_playing = self.music_queue[0][0]['title']
            self.now_playing_url = self.music_queue[0][0]['url']
            self.queue.pop(0)
            self.urls.pop(0)
            vc.play(discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options), after=lambda e: self.play_next(ctx))
            # remove the first element as you are currently playing it
            try:
                self.music_queue.pop(0)
            except IndexError:
                pass

        else:
            try:
                self.queue.pop(0)
                self.urls.pop(0)
            except IndexError:
                pass
            self.now_playing = None
            self.now_playing_url = None

    async def play_music(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        try:
            self.now_playing = self.music_queue[0][0]['title']
            self.now_playing_url = self.music_queue[0][0]['url']
            m_url = self.music_queue[0][0]['source']
        except IndexError:
            return

        # try to connect to voice channel if you are not already connected
        try:
            vc = await self.music_queue[0][1].connect()
        except discord.ClientException:
            await vc.move_to(self.music_queue[0][1])
        print(self.music_queue)
        
        vc.play(discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options), after=lambda e: self.play_next(ctx))
        # try to pop as you are playing it
        self.music_queue.pop(0)

    @commands.command(aliases=['p', 'add'], description='Plays the searched song from YouTube')
    async def play(self, ctx, *, query):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        try:
            voice_channel = ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title='Connect to a voice channel first!', colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            return

        try:
            await voice_channel.connect()
        except discord.ClientException:
            await voice_client.move_to(voice_channel)

        if voice_channel is not None:
            song = self.search_yt(query)

            if isinstance(song, bool):
                embed = discord.Embed(
                    title="Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.",
                    colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return
            
            if isinstance(song, youtube_dl.utils.DownloadError):
                embed = discord.Embed(
                    title="Could not download the song since the video is rated inappropriate for young audiences.",
                    colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            else:

                try:
                    video = pafy.new(self.url)
                except ValueError:
                    embed = discord.Embed(
                        title="Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.",
                        colour=discord.Colour.random())
                    embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                    await ctx.send(embed=embed)
                    return

                self.music_queue.append([song, voice_channel])
                if not ctx.voice_client.is_playing():
                    await self.play_music(ctx)

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
    async def queue(self, ctx):  # self.music_queue is not used since it is a multidimensional list of dictionaries
        track_num = 1
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if vc is None:
            embed = discord.Embed(title='The player is not connected to a voice channel, use the play command to do so',
                                  colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            return

        if vc.is_playing():

            if self.now_playing is None or self.now_playing_url is None:
                embed = discord.Embed(title='No music in queue', colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                self.queue = []
                self.urls = []
                return

            embed = discord.Embed(title='QUEUE', colour=discord.Colour.dark_teal())
            embed.add_field(name='Now Playing', value=f'[{self.queue[0]}]({self.urls[0]})', inline=False)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)

            for i in range(1, len(self.queue)):
                embed.add_field(name=f'Track number {str(track_num)}:',
                                value=f'[{self.queue[i]}]({self.urls[i]})',
                                inline=False)
                track_num += 1

            embed.set_footer(text='Use the play command if you want to add more audio tracks to the queue',
                             icon_url=self.bot.user.avatar)

            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(title='No audio is being played', colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed.set_footer(text='Use the play command if you want to add more audio tracks to the queue')
            await ctx.send(embed=embed)

    @commands.command(name='pause', description='Pauses the current track')
    async def pause(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc.is_playing():
                embed = discord.Embed(title='Paused', colour=discord.Colour.random())
                embed.add_field(name='Paused Track:', value=f'[{self.now_playing}]({self.now_playing_url})')
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                vc.pause()
            else:
                embed = discord.Embed(title='Already paused', colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title='You are not connected to the voice channel', colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    @commands.command(aliases=['unpause'], description='Resumes the paused track')
    async def resume(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc.is_paused():
                embed = discord.Embed(title='Resumed', colour=discord.Colour.random())
                embed.add_field(name='Resumed Track:', value=f'[{self.now_playing}]({self.now_playing_url})')
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                vc.resume()
            else:
                embed = discord.Embed(title='Nothing has been paused', colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title='You are not connected to the voice channel', colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    @commands.command(name="skip", description="Skips the current song being played")
    async def skip(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

            if vc is None:
                embed = discord.Embed(title='The player is not connected to a voice channel',
                                      colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            if not vc.is_playing():
                embed = discord.Embed(title='No audio is being played', colour=discord.Colour.random())
                embed.set_footer(text='Use the play command if you want to add more audio tracks to the queue')
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            if vc is not None:
                vc.stop()
                embed = discord.Embed(title='Skipped', colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                embed.add_field(name='Skipped Track:', value=f'[{self.now_playing}]({self.now_playing_url})')
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title='You are not connected to the voice channel', colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    @commands.command(name='stop', description='Stops the music being played and clears the queue')
    async def stop(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

            if vc is None:
                embed = discord.Embed(title='The player is not connected to a voice channel',
                                      colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            if not vc.is_playing():
                embed = discord.Embed(title='No audio is being played', colour=discord.Colour.random())
                embed.set_footer(text='Use the play command if you want to add more audio tracks to the queue')
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)

            else:
                embed = discord.Embed(title='Stopped', colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                vc.stop()
                self.queue = []
                self.urls = []
                self.music_queue = []
                self.now_playing = None
                self.now_playing_url = None

        else:
            embed = discord.Embed(title='You are not connected to the voice channel', colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    @commands.command(aliases=['dc', 'leave'], description="Disconnecting bot from VC")
    async def disconnect(self, ctx):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc is None:
                embed = discord.Embed(title='The player is not connected to a voice channel',
                                      colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)

            else:
                embed = discord.Embed(title='Disconnected', colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                await vc.disconnect()
                self.music_queue = []
                self.urls = []
                self.queue = []
                self.now_playing = None
                self.now_playing_url = None
        else:
            embed = discord.Embed(title='You are not connected to the voice channel', colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    @commands.command(aliases=['np', 'now'], description='Shows the current track being played')
    async def nowplaying(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if vc is None:
            embed = discord.Embed(title='The player is not connected to the voice channel',
                                  colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            return

        if not vc.is_playing():
            embed = discord.Embed(title='No audio is being played', colour=discord.Colour.random())
            embed.set_footer(text='Use the play command if you want to add more audio tracks to the queue')
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            return

        else:
            if self.now_playing is not None:
                video = pafy.new(url=self.now_playing_url)
                embed = discord.Embed(title='Now Playing', colour=discord.Colour.dark_teal())
                if video.author == video.username:
                    embed.add_field(name='Track Name:',
                                    value=f'[{self.now_playing}]({self.now_playing_url}) by [{video.author}](https://youtube.com/c/{video.author})')
                else:
                    embed.add_field(name='Track Name:',
                                    value=f'[{self.title}]({self.url}) by [{video.author}](https://youtube.com/channel/{video.username})')
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                embed.set_thumbnail(url=video.bigthumbhd)
                embed.set_footer(text=f'Duration: {video.duration}, 🎥: {video.viewcount}, 👍: {video.likes}')
                await ctx.send(embed=embed)

    @commands.command(aliases=['rm', 'del', 'delete'], description='Removed a certain track from the queue')
    async def remove(self, ctx, track_number: int):
        if ctx.author.voice:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

            if vc is None:
                embed = discord.Embed(title='The player is not connected to the voice channel',
                                      colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            if track_number < 1 or track_number > len(self.music_queue):
                embed = discord.Embed(title=f'Enter a number between 1 and {len(self.music_queue)}',
                                      colour=discord.Colour.random())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(title=f'Removed {self.music_queue[track_number - 1][0]["title"]} from the queue',
                                  colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

            title = self.music_queue[track_number - 1][0]['title']
            self.music_queue.pop(track_number - 1)
            i = 0
            for i in range(len(self.queue)):
                if self.queue[i] == title:
                    break
            self.queue.pop(i)
            self.urls.pop(i)

        else:
            embed = discord.Embed(title='You are not connected to the voice channel', colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Music(bot))

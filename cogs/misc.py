# All misc commands stored here
import datetime
import json
import discord
import requests
import os
import wikipedia
import time
from googleapiclient.discovery import build
from discord.ext import commands
from discord.ui import Button, View


# Gets quote from https://zenquotes.io api
def get_quote() -> list:
    response = requests.get('https://zenquotes.io/api/random')
    return json.loads(response.text)


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description: str) -> None:
    # Response embed
    embed = discord.Embed(description=description, colour=discord.Colour.red())
    await ctx.send(embed=embed)


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Quote command
    @commands.command(aliases=['qu'], description='Replies with an inspirational quote')
    async def quote(self, ctx):
        quote = get_quote()
        embed = discord.Embed(colour=discord.Colour.orange())
        embed.add_field(name=quote[0]['q'], value=quote[0]['a'], inline=True)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(text=f'Requested by {ctx.author}',
                         icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(ctx.author.default_avatar))
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    @quote.error
    async def quote_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Spam command
    @commands.command(aliases=['s'], description='Spams text or users')
    async def spam(self, ctx, *, message):
        for _ in range(5):
            await ctx.send(message)

    @spam.error
    async def spam_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Av command
    @commands.command(aliases=['av', 'pfp'], description='Shows the specified user\'s avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        # Getting the urls
        png_url = str(member.avatar) if member.avatar else str(member.default_avatar)
        webp_url = png_url.replace('png', 'webp')
        jpg_url = png_url.replace('png', 'jpg')
        # Response embed
        embed = discord.Embed(colour=member.colour)
        embed.set_author(name=str(member), icon_url=png_url)
        embed.set_image(url=png_url)
        embed.add_field(name='Download this image', value=f'[webp]({webp_url}) | [png]({png_url}) | [jpg]({jpg_url})')
        await ctx.reply(embed=embed)

    @avatar.error
    async def avatar_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Servericon command
    @commands.command(aliases=['serverpfp', 'serverav', 'serveravatar'], description='Shows the server\'s icon')
    async def servericon(self, ctx):
        if ctx.guild.icon is None:
            await send_error_embed(ctx, description='This server has no icon')
            return
        # Getting the urls
        png_url = str(ctx.guild.icon)
        webp_url = png_url.replace('png', 'webp')
        jpg_url = png_url.replace('png', 'jpg')
        # Response embed
        embed = discord.Embed(colour=discord.Colour.random())
        embed.set_author(name=ctx.guild.name, icon_url=png_url)
        embed.set_image(url=png_url)
        embed.add_field(name='Download this image', value=f'[webp]({webp_url}) | [png]({png_url}) | [jpg]({jpg_url})')
        embed.set_footer(text=f'Requested by {ctx.author}',
                         icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(ctx.author.default_avatar))
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    @servericon.error
    async def servericon_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Megaspam command
    @commands.command(aliases=['ms'], description='Spams a message 25 times')
    async def megaspam(self, ctx, *, message):
        await ctx.message.delete()
        for _ in range(25):
            await ctx.send(message)

    @megaspam.error
    async def megaspam_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Search command
    @commands.command(aliases=['yt', 'youtube', 'ytsearch'],
                      description='Searches YouTube and responds with the top result')
    async def youtubesearch(self, ctx, *, query):
        youtube = build('youtube', 'v3', developerKey=os.getenv('youtube_api_key'))
        req = youtube.search().list(q=query, part='snippet', type='video', maxResults=100)
        res = req.execute()

        video_ids = []
        thumbnails = []
        titles = []
        publish_dates = []
        channel_ids = []
        authors = []

        for item in res['items']:
            # Getting the video details
            video_ids.append(item['id']['videoId'])
            thumbnails.append(item['snippet']['thumbnails']['high']['url'])
            titles.append(item['snippet']['title'])
            channel_ids.append(item['snippet']['channelId'])
            authors.append(item['snippet']['channelTitle'])

            # Getting the publishing date and converting it to unix time
            publish_date = item['snippet']['publishedAt']
            publish_date = publish_date.strip('Z')
            publish_date = publish_date.split('T')
            publish_date = list(publish_date[0].split('-'))
            publish_date.extend(publish_date[1].split('.'))
            publish_date = [int(x) for x in publish_date]
            publish_date = tuple(publish_date)
            publish_date = datetime.datetime(*publish_date)
            publish_date = f'<t:{int(time.mktime(publish_date.timetuple()))}:R>'
            publish_dates.append(publish_date)

        # Gets the next video
        async def next_video_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            embed.clear_fields()
            video_ids.pop(0)
            thumbnails.pop(0)
            titles.pop(0)
            publish_dates.pop(0)
            channel_ids.pop(0)
            authors.pop(0)
            if not video_ids:
                await interaction.response.edit_message('No more results available', embed=None)
                return

            statistics = youtube.videos().list(part='statistics,contentDetails', id=video_ids[0]).execute()

            embed.add_field(name='Result:', value=f'[{titles[0]}](https://www.youtube.com/watch?v={video_ids[0]})')
            embed.add_field(name='Video Author:', value=f'[{authors[0]}](https://youtube.com/channel/{channel_ids[0]})')
            embed.add_field(name='Publish Date:', value=f'{publish_dates[0]}')
            embed.set_image(url=thumbnails[0])
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed.set_footer(
                text=f'Duration: {statistics["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {statistics["items"][0]["statistics"]["viewCount"]}, 👍: {statistics["items"][0]["statistics"]["likeCount"]}')
            watch_video.url = f'https://www.youtube.com/watch?v={video_ids[0]}'
            view.remove_item(watch_video)
            view.add_item(watch_video)
            await interaction.response.edit_message(embed=embed, view=view)

        # Ends the interaction
        async def end_interaction_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return
            view.remove_item(next_video)
            view.remove_item(end_interaction)
            await interaction.response.edit_message(view=view)

        stats = youtube.videos().list(id=video_ids[0], part='statistics,contentDetails').execute()
        # Response embed
        embed = discord.Embed(colour=discord.Colour.red())
        embed.add_field(name=f'Result:', value=f'[{titles[0]}](https://www.youtube.com/watch?v={video_ids[0]})')
        embed.add_field(name='Video Author:', value=f'[{authors[0]}](https://youtube.com/channel/{channel_ids[0]})')
        embed.add_field(name='Publish Date:', value=f'{publish_dates[0]}')
        embed.set_image(url=thumbnails[0])
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(
            text=f'Duration: {stats["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {stats["items"][0]["statistics"]["viewCount"]}, 👍: {stats["items"][0]["statistics"]["likeCount"]}')
        next_video = Button(label='Next Video ⏭️', style=discord.ButtonStyle.green)
        end_interaction = Button(label='End Interaction', style=discord.ButtonStyle.red)
        watch_video = Button(label='Watch Video', url=f'https://www.youtube.com/watch?v={video_ids[0]}')
        view = View()
        view.add_item(next_video)
        view.add_item(end_interaction)
        view.add_item(watch_video)
        await ctx.send(embed=embed, view=view)
        next_video.callback = next_video_trigger
        end_interaction.callback = end_interaction_trigger

    @youtubesearch.error
    async def search_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Code command
    @commands.command(name='code', description='Shows the code of the module')
    async def code(self, ctx, module):
        module = module.lower()
        try:
            with open(f'cogs/{module}.py') as code_file:  # Open module
                code = code_file.read()
                with open(f'Code for {module}.txt', 'w+') as text_file:  # Write the file to be sent
                    text_file.write(code)

            await ctx.send(file=discord.File(f'Code for {module}.txt'))
            os.remove(f'Code for {module}.txt')  # Remove file to avoid problems in version control

        except FileNotFoundError:
            await send_error_embed(ctx, description=f'Module {module} not found')

    @code.error
    async def code_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Wikipedia command
    @commands.command(aliases=['wiki'], description='Gets a summary of the query from wikipedia')
    async def wikipedia(self, ctx, *, query):
        # Gets the data from wikipedia
        try:
            summary = wikipedia.summary(query, sentences=5)
            thumbnail = wikipedia.page(query).images[0]
            url = wikipedia.page(query).url
            # Response embed
            summary += f'[ Read More...]({url})'
            embed = discord.Embed(title=wikipedia.page(query).title, url=url, description=summary,
                                  colour=discord.Colour.random())
            embed.set_thumbnail(url=thumbnail)
            await ctx.send(embed=embed)

        except wikipedia.exceptions.WikipediaException as e:
            await send_error_embed(ctx, description=str(e))

    @wikipedia.error
    async def wikipedia_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')


# Setup
def setup(bot):
    bot.add_cog(Misc(bot))

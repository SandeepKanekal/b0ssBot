import discord
import os
import datetime
import time
import requests
import wikipedia
import asyncpraw
import asyncprawcore
from googleapiclient.discovery import build
from discord.ui import Button, View
from discord.ext import commands


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description: str) -> None:
    # Response embed
    embed = discord.Embed(description=description, colour=discord.Colour.red())
    await ctx.send(embed=embed)


# Gets post from the specified subreddit
async def get_post(subreddit: str) -> list:
    reddit = asyncpraw.Reddit('bot', user_agent='bot user agent')
    subreddit = await reddit.subreddit(subreddit)
    return [post async for post in subreddit.hot()]


class Internet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # YouTubeSearch command
    @commands.command(aliases=['yt', 'youtube', 'ytsearch'],
                      description='Searches YouTube and responds with the top result', usage='youtubesearch <query>')
    async def youtubesearch(self, ctx, *, query):
        # sourcery no-metrics
        youtube = build('youtube', 'v3', developerKey=os.getenv('youtube_api_key'))
        res = youtube.search().list(q=query, part='snippet', type='video', maxResults=100).execute()

        if not res['items']:
            await send_error_embed(ctx, description='No results found')
            return

        index = 0
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

        # Creating the embed
        stats = youtube.videos().list(id=video_ids[0], part='statistics, contentDetails').execute()
        embed = discord.Embed(colour=discord.Colour.red())
        embed.add_field(name=f'Result:', value=f'[{titles[0]}](https://www.youtube.com/watch?v={video_ids[0]})')
        embed.add_field(name='Video Author:', value=f'[{authors[0]}](https://youtube.com/channel/{channel_ids[0]})')
        embed.add_field(name='Publish Date:', value=f'{publish_dates[0]}')
        embed.set_image(url=thumbnails[0])
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(
            text=f'Duration: {stats["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {stats["items"][0]["statistics"]["viewCount"]}, 👍: {stats["items"][0]["statistics"]["likeCount"] if "likeCount" in stats["items"][0]["statistics"].keys() else "Could not fetch likes"}')
        next_video = Button(emoji='⏭️', style=discord.ButtonStyle.green)
        previous_video = Button(emoji='⏮️', style=discord.ButtonStyle.green)
        end_interaction = Button(label='End Interaction', style=discord.ButtonStyle.red)
        watch_video = Button(label='Watch Video', style=discord.ButtonStyle.green)
        view = View()
        view.add_item(previous_video)
        view.add_item(next_video)
        view.add_item(end_interaction)
        view.add_item(watch_video)
        await ctx.send(embed=embed, view=view)

        # Gets the next video
        async def next_video_trigger(interaction):
            nonlocal index
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            embed.clear_fields()
            index += 1
            if index == len(video_ids) - 1:
                index = 0  # Resetting the index

            statistics = youtube.videos().list(part='statistics, contentDetails', id=video_ids[index]).execute()

            embed.add_field(name='Result:',
                            value=f'[{titles[index]}](https://www.youtube.com/watch?v={video_ids[index]})')
            embed.add_field(name='Video Author:',
                            value=f'[{authors[index]}](https://youtube.com/channel/{channel_ids[index]})')
            embed.add_field(name='Publish Date:', value=f'{publish_dates[index]}')
            embed.set_image(url=thumbnails[index])
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed.set_footer(
                text=f'Duration: {statistics["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {statistics["items"][0]["statistics"]["viewCount"]}, 👍: {statistics["items"][0]["statistics"]["likeCount"] if "likeCount" in statistics["items"][0]["statistics"].keys() else "Could not fetch likes"}')
            await interaction.response.edit_message(embed=embed)

        # Gets the previous video
        async def previous_video_trigger(interaction):
            nonlocal index
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            embed.clear_fields()

            if index == 0:
                await interaction.response.send_message('This is the first video!', ephemeral=True)
                return

            index -= 1

            statistics = youtube.videos().list(part='statistics, contentDetails', id=video_ids[index]).execute()

            embed.add_field(name='Result:',
                            value=f'[{titles[index]}](https://www.youtube.com/watch?v={video_ids[index]})')
            embed.add_field(name='Video Author:',
                            value=f'[{authors[index]}](https://youtube.com/channel/{channel_ids[index]})')
            embed.add_field(name='Publish Date:', value=f'{publish_dates[index]}')
            embed.set_image(url=thumbnails[index])
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed.set_footer(
                text=f'Duration: {statistics["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {statistics["items"][0]["statistics"]["viewCount"]}, 👍: {statistics["items"][0]["statistics"]["likeCount"]}')
            await interaction.response.edit_message(embed=embed)

        # Replies with the link of the video
        async def watch_video_trigger(interaction):
            nonlocal index
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            await interaction.response.send_message(f'https://youtube.com/watch?v={video_ids[index]}')

        # Ends the interaction
        async def end_interaction_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return
            await interaction.response.edit_message(view=None)

        next_video.callback = next_video_trigger
        previous_video.callback = previous_video_trigger
        end_interaction.callback = end_interaction_trigger
        watch_video.callback = watch_video_trigger

    @youtubesearch.error
    async def search_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please enter a search term!\n\nProper Usage: `{self.bot.get_command("youtubesearch").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Wikipedia command
    @commands.command(aliases=['wiki', 'wikisearch'], description='Gets a summary of the query from wikipedia',
                      usage='wikipedia <query>')
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
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please enter a search term!\n\nProper Usage: `{self.bot.get_command("wikipedia").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: {error}')

    # Weather command
    @commands.command(name='weather', description='Get the weather for a location', usage='weather <location>')
    async def weather(self, ctx, *, location: str = None):
        if not location:
            await send_error_embed(ctx, description='Please enter a location')
            return

        weather_data = requests.get(
            f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={os.getenv("weather_api_key")}&units=metric').json()
        if weather_data['cod'] == '404':
            await send_error_embed(ctx, description='Location not found')
            return

        if weather_data['cod'] == '429':
            await send_error_embed(ctx, description='Too many requests. Please use the command after some time')
            return

        embed = discord.Embed(
            title=f'Weather for {weather_data["name"]}, {weather_data["sys"]["country"]}',
            description=f'{weather_data["weather"][0]["description"].capitalize()}',
            colour=discord.Colour.blue()
        )
        embed.set_thumbnail(url=f'https://openweathermap.org/img/wn/{weather_data["weather"][0]["icon"]}@2x.png')
        embed.add_field(name='Max. Temperature', value=f'{weather_data["main"]["temp_max"]}°C')
        embed.add_field(name='Min. Temperature', value=f'{weather_data["main"]["temp_min"]}°C')
        embed.add_field(name='Temperature', value=f'{weather_data["main"]["temp"]}°C')
        embed.add_field(name='Feels Like', value=f'{weather_data["main"]["feels_like"]}°C')
        embed.add_field(name='Humidity', value=f'{weather_data["main"]["humidity"]}%')
        embed.add_field(name='Wind Speed', value=f'{weather_data["wind"]["speed"]}m/s')
        embed.add_field(name='Pressure', value=f'{weather_data["main"]["pressure"]}hPa')
        embed.add_field(name='Sunrise', value=f'<t:{weather_data["sys"]["sunrise"]}:R>')
        embed.add_field(name='Sunset', value=f'<t:{weather_data["sys"]["sunset"]}:R>')
        embed.set_footer(text='Powered by OpenWeatherMap')
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    @weather.error
    async def weather_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Post command
    @commands.command(aliases=['reddit', 'post', 'rp'], description='Gets a post from the specified subreddit',
                      usage='redditpost <subreddit>')
    async def redditpost(self, ctx, subreddit):  # sourcery no-metrics
        index = 0

        async def next_post_trigger(interaction):
            nonlocal index
            # Callback to next_post triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            if index == len(submissions) - 1:
                index = 0
            else:
                index += 1  # Increment index

            embed_next = discord.Embed(colour=discord.Colour.orange())
            embed_next.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed_next.title = submissions[index].title
            embed_next.description = submissions[index].selftext
            embed_next.url = f'https://reddit.com{submissions[index].permalink}'
            embed_next.set_footer(
                text=f'⬆️ {submissions[index].ups} | ⬇️ {submissions[index].downs} | 💬 {submissions[index].num_comments}\nSession for {ctx.author}')
            embed_next.timestamp = datetime.datetime.now()

            # Checking if the submission is text-only
            if not submissions[index].is_self:
                embed_next.set_image(url=submissions[index].url)

            try:
                await interaction.response.edit_message(embed=embed_next)
            except discord.HTTPException:
                embed_next.description = 'The post content was too long to be sent'
                await ctx.send(embed=embed_next)

        async def previous_post_trigger(interaction):
            nonlocal index
            # Callback to previous_post triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            if index == 0:
                await interaction.response.send_message(content='This is the first post', ephemeral=True)
                return

            index -= 1  # Decrement index

            embed_previous = discord.Embed(colour=discord.Colour.orange())
            embed_previous.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed_previous.title = submissions[index].title
            embed_previous.description = submissions[index].selftext
            embed_previous.url = f'https://reddit.com{submissions[index].permalink}'
            embed_previous.set_footer(
                text=f'⬆️ {submissions[index].ups} | ⬇️ {submissions[index].downs} | 💬 {submissions[index].num_comments}\nSession for {ctx.author}')
            embed_previous.timestamp = datetime.datetime.now()

            # Checking if the submission is text-only
            if not submissions[index].is_self:
                embed_previous.set_image(url=submissions[index].url)

            try:
                await interaction.response.edit_message(embed=embed_previous)
            except discord.HTTPException:
                embed_previous.description = 'The post content was too long to be sent'
                await ctx.send(embed=embed_previous)

        async def end_interaction_trigger(interaction):
            # Callback to end_interaction triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return
            await interaction.response.edit_message(view=None)

        try:
            submissions = await get_post(subreddit)
            if not ctx.channel.is_nsfw():  # Filters out nsfw posts if the channel is not marked NSFW
                submissions = list(filter(lambda s: not s.over_18, submissions))
            if not len(submissions):
                await send_error_embed(ctx,
                                       description=f'The subreddit **r/{subreddit}** has been marked as NSFW, please use the same command in a NSFW channel.')
            embed = discord.Embed(colour=discord.Colour.orange())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            next_post = Button(emoji='⏭️', style=discord.ButtonStyle.green)
            previous_post = Button(emoji='⏮️', style=discord.ButtonStyle.green)
            end_interaction = Button(label='End Interaction', style=discord.ButtonStyle.red)
            view = View()
            view.add_item(previous_post)
            view.add_item(next_post)
            view.add_item(end_interaction)
            next_post.callback = next_post_trigger
            end_interaction.callback = end_interaction_trigger
            previous_post.callback = previous_post_trigger

            embed.title = submissions[0].title
            embed.description = submissions[0].selftext
            embed.url = submissions[0].url
            embed.set_footer(
                text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nSession for {ctx.author}')
            embed.timestamp = datetime.datetime.now()

            # Checking if the submission is text-only
            if not submissions[0].is_self:
                embed.set_image(url=submissions[0].url)

            try:
                await ctx.send(embed=embed, view=view)
            except discord.HTTPException:
                embed = discord.Embed(description='The post content was too long to be sent',
                                      colour=discord.Colour.orange())
                await ctx.send(embed=embed, view=view)

        except AttributeError:
            # Could not get a post
            await send_error_embed(ctx, description='Could not retrieve a post from **r/{subreddit}**')

        except asyncprawcore.exceptions.AsyncPrawcoreException as e:
            await send_error_embed(ctx, description=str(e))

    @redditpost.error
    async def post_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify a subreddit\n\nProper Usage: `{self.bot.get_command("redditpost").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')


def setup(bot):
    bot.add_cog(Internet(bot))

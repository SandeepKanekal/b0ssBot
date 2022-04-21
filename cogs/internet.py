import contextlib

import discord
import os
import datetime
import time
import requests
import wikipedia
import asyncpraw
import asyncprawcore
from sql_tools import SQL
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
    sub = []
    submissions = subreddit.hot()
    async for submission in submissions:
        sub.append(submission)
    return sub


class Internet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # YouTubeSearch command
    @commands.command(aliases=['yt', 'youtube', 'ytsearch'],
                      description='Searches YouTube and responds with the top result')
    async def youtubesearch(self, ctx, *, query):
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
        stats = youtube.videos().list(id=video_ids[0], part='statistics,contentDetails').execute()
        embed = discord.Embed(colour=discord.Colour.red())
        embed.add_field(name=f'Result:', value=f'[{titles[0]}](https://www.youtube.com/watch?v={video_ids[0]})')
        embed.add_field(name='Video Author:', value=f'[{authors[0]}](https://youtube.com/channel/{channel_ids[0]})')
        embed.add_field(name='Publish Date:', value=f'{publish_dates[0]}')
        embed.set_image(url=thumbnails[0])
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(
            text=f'Duration: {stats["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {stats["items"][0]["statistics"]["viewCount"]}, 👍: {stats["items"][0]["statistics"]["likeCount"]}')
        next_video = Button(emoji='⏭️', style=discord.ButtonStyle.green)
        previous_video = Button(emoji='⏮️', style=discord.ButtonStyle.green)
        end_interaction = Button(label='End Interaction', style=discord.ButtonStyle.red)
        watch_video = Button(label='Watch Video', url=f'https://www.youtube.com/watch?v={video_ids[0]}')
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
                text=f'Duration: {statistics["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {statistics["items"][0]["statistics"]["viewCount"]}, 👍: {statistics["items"][0]["statistics"]["likeCount"]}')
            watch_video.url = f'https://www.youtube.com/watch?v={video_ids[0]}'
            view.remove_item(watch_video)
            view.add_item(watch_video)
            await interaction.response.edit_message(embed=embed, view=view)

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
            watch_video.url = f'https://www.youtube.com/watch?v={video_ids[index]}'
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
            view.remove_item(previous_video)
            await interaction.response.edit_message(view=view)

        next_video.callback = next_video_trigger
        previous_video.callback = previous_video_trigger
        end_interaction.callback = end_interaction_trigger

    @youtubesearch.error
    async def search_error(self, ctx, error):
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

    # YouTube notify command
    @commands.command(name='youtubenotification', aliases=['ytnotification', 'ytnotify'],
                      description='Configure YouTube notifications for the server\nMode can be add/remove/view\nAdd: `-youtubenotification add #new-videos https://www.youtube.com/c/MrBeast6000`\nRemove: `-youtubenotification remove #new-videos https://www.youtube.com/c/MrBeast6000`\nView: `-youtubenotification view`')
    async def youtubenotification(self, ctx, mode: str, text_channel: discord.TextChannel = None, *,
                                  youtube_channel: str = None):
        # sourcery no-metrics
        if mode not in ['add', 'remove', 'view']:
            await send_error_embed(ctx, description='Mode must be add, remove or view')
            return

        sql = SQL('b0ssbot')
        youtube = build('youtube', 'v3', developerKey=os.getenv('youtube_api_key'))
        if mode == 'add':
            channel_id = requests.get(
                f"https://www.googleapis.com/youtube/v3/search?part=id&q={youtube_channel.split('/c/')[1]}&type=channel&key={os.getenv('youtube_api_key')}").json()[
                'items'][0]['id']['channelId'] if '/c/' in youtube_channel else youtube_channel.split('/channel/')[1]

            if sql.select(elements=['*'], table='youtube',
                          where=f"guild_id='{ctx.guild.id}' and channel_id = '{channel_id}'"):
                await send_error_embed(ctx, description='Channel already added')
                return

            channel = youtube.channels().list(id=channel_id, part='snippet, contentDetails').execute()
            latest_video_id = youtube.playlistItems().list(
                playlistId=channel['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
                part='contentDetails').execute()['items'][0]['contentDetails']['videoId']
            channel_name = channel['items'][0]['snippet']['title'].replace("'", "''")

            sql.insert(table='youtube',
                       columns=['guild_id', 'text_channel_id', 'channel_id', 'channel_name', 'latest_video_id'],
                       values=[f"'{ctx.guild.id}'", f"'{text_channel.id}'", f"'{channel['items'][0]['id']}'",
                               f"'{channel_name}'", f"'{latest_video_id}'"])
            await ctx.send(
                f'NOTE: This command requires **Send Webhooks** to be enabled in {text_channel.mention}',
                embed=discord.Embed(
                    colour=discord.Colour.green(),
                    description=f'YouTube notifications for the channel **[{channel["items"][0]["snippet"]["title"]}](https://youtube.com/channel{channel["items"][0]["id"]})** will now be sent to {text_channel.mention}').set_thumbnail(
                    url=channel["items"][0]["snippet"]["thumbnails"]["high"]["url"]).set_footer(
                    text='Use the command again to update the channel')
            )

        elif mode == 'remove':
            channel_id = requests.get(
                f"https://www.googleapis.com/youtube/v3/search?part=id&q={youtube_channel.split('/c/')[1]}&type=channel&key={os.getenv('youtube_api_key')}").json()[
                'items'][0]['id']['channelId'] if '/c/' in youtube_channel else youtube_channel.split('/channel/')[1]
            channel = youtube.channels().list(id=channel_id, part='snippet, contentDetails').execute()

            if not sql.select(elements=['*'], table='youtube',
                              where=f"guild_id='{ctx.guild.id}' and channel_id = '{channel_id}'"):
                await send_error_embed(ctx, description='Channel not added')
                return

            sql.delete(table='youtube',
                       where=f'guild_id = \'{ctx.guild.id}\' AND channel_id = \'{channel["items"][0]["id"]}\'')
            await ctx.send(embed=discord.Embed(
                colour=discord.Colour.green(),
                description=f'YouTube notifications for the channel **[{channel["items"][0]["snippet"]["title"]}](https://youtube.com/channel{channel["items"][0]["id"]})** will no longer be sent to {text_channel.mention}').set_thumbnail(
                url=channel["items"][0]["snippet"]["thumbnails"]["high"]["url"]))

        else:
            channels = sql.select(elements=['channel_name', 'channel_id', 'text_channel_id'], table='youtube',
                                  where=f'guild_id = \'{ctx.guild.id}\'')
            if not channels:
                await send_error_embed(ctx, description='No channels are currently set up for notifications')
                return
            embed = discord.Embed(
                description='',
                colour=discord.Colour.dark_red()
            )
            for index, channel in enumerate(channels):
                text_channel = discord.utils.get(ctx.guild.text_channels, id=int(channel[2]))
                embed.description += f'{index + 1}. **[{channel[0]}](https://youtube.com/channel/{channel[1]})** in {text_channel.mention}\n'
            if ctx.guild.icon:
                embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
            else:
                embed.set_author(name=ctx.guild.name)
            embed.set_thumbnail(
                url='https://yt3.ggpht.com/584JjRp5QMuKbyduM_2k5RlXFqHJtQ0qLIPZpwbUjMJmgzZngHcam5JMuZQxyzGMV5ljwJRl0Q=s176-c-k-c0x00ffffff-no-rj')
            await ctx.send(embed=embed)

    @youtubenotification.error
    async def youtubenotification_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Weather command
    @commands.command(name='weather', description='Get the weather for a location')
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
        await send_error_embed(ctx, description=f'Error: {error}')

    # Post command
    @commands.command(aliases=['reddit', 'post', 'rp'], description='Gets a post from the specified subreddit')
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
        await send_error_embed(ctx, description=f'Error: {error}')

    # Hourlyweather command
    @commands.command(name='hourlyweather', aliases=['hw'],
                      description='Get the hourly weather of a location. b0ssB0t will send the current weather periodically.\nmode can be `add`, `remove`, or `view`\nAdd: `-hourlyweather add #weather <location>`\nRemove: `-hourlyweather remove #weather <location>`\nView: `-hourlyweather view`\nIf a location has already been added, the channel will be updated on using the `add` mode')
    @commands.has_permissions(manage_guild=True)
    async def hourlyweather(self, ctx, mode: str, channel: discord.TextChannel = None, *, location: str = None):
        # sourcery no-metrics
        sql = SQL('b0ssbot')
        original_location = ''
        if location:
            original_location = location
            location = location.lower().replace("'", "''")  # Make sure the location is lowercase

        if mode == 'add':
            if channel is None or location is None:  # If the channel or location is not specified
                await send_error_embed(ctx, description='Please provide a channel and location')
                return

            with contextlib.suppress(IndexError):
                if location == \
                        sql.select(elements=['location'], table='hourlyweather', where=f"guild_id = '{ctx.guild.id}'")[
                            0][0]:  # If the location is already in the database
                    sql.update(table='hourlyweather', column='channel_id', value=f'{channel.id}',
                               where=f"guild_id = '{ctx.guild.id}'")  # Update the channel
                    await ctx.send(
                        embed=discord.Embed(description=f'Updated the hourly weather channel to {channel.mention}',
                                            colour=discord.Colour.green()))  # Send a success embed
                    return

            sql.insert(table='hourlyweather', columns=['guild_id', 'channel_id', 'location'],
                       values=[f"'{ctx.guild.id}'", f"'{channel.id}'", f"'{location}'"])  # Insert the location
            await ctx.send(embed=discord.Embed(description=f'Added hourly weather for {original_location}',
                                               colour=discord.Colour.green()))  # Send a success embed

        elif mode == 'remove':

            if channel is None or location is None:  # If the channel or location is not specified
                await send_error_embed(ctx, description='Please provide a channel and location')
                return

            with contextlib.suppress(IndexError):
                if location == \
                        sql.select(elements=['location'], table='hourlyweather',
                                   where=f"guild_id = '{ctx.guild.id}' AND location = '{location}'")[0][
                            0]:  # If the location is in the database
                    sql.delete(table='hourlyweather',
                               where=f"guild_id = '{ctx.guild.id}' AND location = '{location}'")  # Delete the location
                    await ctx.send(
                        embed=discord.Embed(description=f'Removed hourly weather for {original_location}',
                                            colour=discord.Colour.green()))  # Send a success embed
                else:
                    await send_error_embed(ctx, description='This location not found')

        elif mode == 'view':
            response = sql.select(elements=['location', 'channel_id'], table='hourlyweather',
                                  where=f"guild_id = '{ctx.guild.id}'")  # Get the locations and channels
            if not response:
                await send_error_embed(ctx, description='No locations are monitored')
                return

            embed = discord.Embed(title=f'Hourly Weather Locations for {ctx.guild.name}', description='',
                                  colour=discord.Colour.blue())
            for item in response:  # Append each location to embed.description along with the text channel
                channel = discord.utils.get(ctx.guild.text_channels, id=int(item[1]))
                location = item[0].replace("''", "'")
                embed.description += f'{location} in {channel.mention}\n'

            await ctx.send(embed=embed)

        else:
            await send_error_embed(ctx, description='Please provide a valid mode')

    @hourlyweather.error
    async def hourlyweather_error(self, ctx, error):
        await send_error_embed(ctx, description=f'{error}')


def setup(bot):
    bot.add_cog(Internet(bot))

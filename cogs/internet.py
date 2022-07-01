import discord
import os
import datetime
import time
import requests
import wikipedia
import asyncprawcore
from googleapiclient.discovery import build
from discord.ui import Button, View
from discord.ext import commands
from tools import send_error_embed, get_posts, get_quote, convert_to_unix_time


class Internet(commands.Cog):
    def __init__(self, bot):
        """
        Initialize the cog

        :param bot: The bot
        :type bot: commands.Bot

        :return: None
        :rtype: None
        """
        self.bot = bot  # type: commands.Bot

    # YouTubeSearch command
    @commands.command(aliases=['yt', 'youtube', 'ytsearch'],
                      description='Searches YouTube and responds with the top 50 results',
                      usage='youtubesearch <query>')
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.guild_only()
    async def youtubesearch(self, ctx, *, query):
        """
        Searches YouTube and responds with the top 50 results
        
        :param ctx: The context of where the message was sent
        :param query: The query to search YouTube for
        
        :type ctx: commands.Context
        :type query: str
        
        :return: None
        :rtype: None
        """
        async with ctx.typing():
            youtube = build('youtube', 'v3', developerKey=os.getenv('youtube_api_key'))
            res = youtube.search().list(q=query, part='snippet', type='video', maxResults=50).execute()  # type: dict

            if not res['items']:
                await send_error_embed(ctx, description='No results found')
                return

            index = 0  # type: int
            video_ids = []  # type: list[str]
            thumbnails = []  # type: list[str]
            titles = []  # type: list[str]
            publish_dates = []  # type: list[str]
            channel_ids = []  # type: list[str]
            authors = []  # type: list[str]

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

            embed = discord.Embed(colour=0xff0000)
            embed.add_field(name=f'Result:', value=f'[{titles[0]}](https://www.youtube.com/watch?v={video_ids[0]})')
            embed.add_field(name='Video Author:', value=f'[{authors[0]}](https://youtube.com/channel/{channel_ids[0]})')
            embed.add_field(name='Publish Date:', value=f'{publish_dates[0]}')
            embed.set_image(url=thumbnails[0])
            embed.set_author(name='YouTube', icon_url='https://yt3.ggpht.com/584JjRp5QMuKbyduM_2k5RlXFqHJtQ0qLIPZpwbUjMJmgzZngHcam5JMuZQxyzGMV5ljwJRl0Q=s176-c-k-c0x00ffffff-no-rj', url='https://www.youtube.com/')
            embed.set_footer(
                text=f'Duration: {stats["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {stats["items"][0]["statistics"]["viewCount"]}, 👍: {stats["items"][0]["statistics"]["likeCount"] if "likeCount" in stats["items"][0]["statistics"].keys() else "Could not fetch likes"}\nResult {index + 1} out of 50')
            next_video = Button(emoji='⏭️', style=discord.ButtonStyle.green)
            previous_video = Button(emoji='⏮️', style=discord.ButtonStyle.green)
            end_interaction = Button(label='End Interaction', style=discord.ButtonStyle.red)
            watch_video = Button(label='Watch Video', style=discord.ButtonStyle.green)
            play = Button(label='Play audio in VC', style=discord.ButtonStyle.green)

            view = View(timeout=None)

            view.add_item(previous_video)
            view.add_item(next_video)
            view.add_item(end_interaction)
            view.add_item(watch_video)
            view.add_item(play)

        await ctx.send(embed=embed, view=view)

        # Gets the next video
        async def next_video_trigger(interaction):
            nonlocal index
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            embed.clear_fields()

            if index == len(video_ids) - 1:
                index = 0  # Resetting the index
            else:
                index += 1

            statistics = youtube.videos().list(part='statistics, contentDetails', id=video_ids[index]).execute()

            embed.add_field(name='Result:',
                            value=f'[{titles[index]}](https://www.youtube.com/watch?v={video_ids[index]})')
            embed.add_field(name='Video Author:',
                            value=f'[{authors[index]}](https://youtube.com/channel/{channel_ids[index]})')
            embed.add_field(name='Publish Date:', value=f'{publish_dates[index]}')
            embed.set_image(url=thumbnails[index])
            embed.set_footer(
                text=f'Duration: {statistics["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {statistics["items"][0]["statistics"]["viewCount"]}, 👍: {statistics["items"][0]["statistics"]["likeCount"] if "likeCount" in statistics["items"][0]["statistics"].keys() else "Could not fetch likes"}\nResult {index + 1} out of 50')
            await interaction.response.edit_message(embed=embed)

        # Gets the previous video
        async def previous_video_trigger(interaction):
            nonlocal index
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            embed.clear_fields()

            if index == 0:
                index = len(video_ids) - 1
            else:
                index -= 1

            statistics = youtube.videos().list(part='statistics, contentDetails', id=video_ids[index]).execute()

            embed.add_field(name='Result:',
                            value=f'[{titles[index]}](https://www.youtube.com/watch?v={video_ids[index]})')
            embed.add_field(name='Video Author:',
                            value=f'[{authors[index]}](https://youtube.com/channel/{channel_ids[index]})')
            embed.add_field(name='Publish Date:', value=f'{publish_dates[index]}')
            embed.set_image(url=thumbnails[index])
            embed.set_footer(
                text=f'Duration: {statistics["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {statistics["items"][0]["statistics"]["viewCount"]}, 👍: {statistics["items"][0]["statistics"]["likeCount"]}\nResult {index + 1} out of 50')
            await interaction.response.edit_message(embed=embed)

        # Replies with the link of the video
        async def watch_video_trigger(interaction):
            nonlocal index
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'https://youtube.com/watch?v={video_ids[index]}', ephemeral=True)
            else:
                await interaction.response.send_message(f'https://youtube.com/watch?v={video_ids[index]}')

        # Ends the interaction
        async def end_interaction_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            next_video.disabled = True
            previous_video.disabled = True
            end_interaction.disabled = True
            watch_video.disabled = True
            play.disabled = True
            await interaction.response.edit_message(view=view)

        async def play_callback(interaction):
            nonlocal index
            await interaction.response.defer()
            try:
                await ctx.invoke(self.bot.get_command('play'), query=titles[index])
                await interaction.followup.send('Audio added to queue!')
            except Exception as e:
                await send_error_embed(ctx, description=f'Error: {e}')

        next_video.callback = next_video_trigger
        previous_video.callback = previous_video_trigger
        end_interaction.callback = end_interaction_trigger
        watch_video.callback = watch_video_trigger
        play.callback = play_callback

    @youtubesearch.error
    async def youtubesearch_error(self, ctx, error):
        """
        Handles errors in the youtubesearch command
        
        :param ctx: The context of where the command was used
        :param error: The error that was raised
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'You are on cooldown! Try again in {error.retry_after:.2f} seconds.')
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please enter a search term!\n\nProper Usage: `{self.bot.get_command("youtubesearch").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Wikipedia command
    @commands.command(aliases=['wiki', 'wikisearch'], description='Gets a summary of the query from wikipedia',
                      usage='wikipedia <query>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wikipedia(self, ctx, *, query: str):
        """
        Gets a summary of the query from wikipedia
        
        :param ctx: The context of where the command was used
        :param query: The query to search for

        :type ctx: commands.Context
        :type query: str

        :return: None
        :rtype: None
        """
        try:
            async with ctx.typing():
                summary = wikipedia.summary(query, sentences=5)  # type: str
                thumbnail = wikipedia.page(query).images[0]  # type: str
                url = wikipedia.page(query).url  # type: str
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
        """
        Handles errors in the wikipedia command
        
        :param ctx: The context of where the command was used
        :param error: The error that was raised
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'You are on cooldown! Try again in {error.retry_after:.2f} seconds.')
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please enter a search term!\n\nProper Usage: `{self.bot.get_command("wikipedia").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: {error}')

    # Weather command
    @commands.command(name='weather', description='Get the weather for a location', usage='weather <location>')
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def weather(self, ctx, *, location: str):
        """
        Gets the weather for a location
        
        :param ctx: The context of where the command was used
        :param location: The location to get the weather for
        
        :type ctx: commands.Context
        :type location: str
        
        :return: None
        :rtype: None
        """
        async with ctx.typing():
            weather_data = requests.get(
                f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={os.getenv("weather_api_key")}&units=metric').json()  # type: dict
            if weather_data['cod'] == '404':
                await send_error_embed(ctx, description='Location not found')
                return

            if weather_data['cod'] == '429':
                await send_error_embed(ctx, description='Too many requests. Please use the command after some time')
                return

            pollution_data = requests.get(
                f'https://api.openweathermap.org/data/2.5/air_pollution?lat={weather_data["coord"]["lat"]}&lon={weather_data["coord"]["lon"]}&appid={os.getenv("weather_api_key")}').json()  # type: dict

            embed = discord.Embed(
                title=f'Weather for {weather_data["name"]}',
                description=f'{weather_data["weather"][0]["description"].capitalize()}.',
                colour=discord.Colour.blue(),
                timestamp=datetime.datetime.now()
            )
            embed.title += f', {weather_data["sys"]["country"]}' if "country" in weather_data["sys"].keys() else ''
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
            embed.add_field(name='Air Quality Index', value=pollution_data['list'][0]['main']['aqi'])
            embed.add_field(name='Pollution', value='\n'.join(
                f'**{key.replace("_", ".").upper()}**: {value}' for key, value in
                pollution_data['list'][0]['components'].items()), inline=False)
            embed.set_footer(text=f'Powered by OpenWeatherMap | ID: {weather_data["id"]}')

        await ctx.send(embed=embed)

    @weather.error
    async def weather_error(self, ctx, error):
        """
        Handles errors in the weather command
        
        :param ctx: The context of where the command was used
        :param error: The error that was raised
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'You are on cooldown! Try again in {error.retry_after:.2f} seconds.')
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please enter a location!\n\nProper Usage: `{self.bot.get_command("weather").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Post command
    @commands.command(aliases=['reddit', 'post', 'rp'], description='Gets a post from the specified subreddit',
                      usage='redditpost <subreddit>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def redditpost(self, ctx, subreddit):
        """
        Gets a post from the specified subreddit
        
        :param ctx: The context of where the command was used
        :param subreddit: The subreddit to get a post from
        
        :type ctx: commands.Context
        :type subreddit: str
        
        :return: None
        :rtype: None
        """
        index = 0  # type: int
        async with ctx.typing():
            try:
                submissions = await get_posts(subreddit)
                submissions = list(filter(lambda p: not p.stickied, submissions))  # type: list
                if not ctx.channel.is_nsfw():  # Filters out nsfw posts if the channel is not marked NSFW
                    submissions = list(filter(lambda s: not s.over_18, submissions))
                if not len(submissions):
                    await send_error_embed(ctx,
                                           description=f'The subreddit **r/{subreddit}** has been marked as NSFW, please use the same command in a NSFW channel.')

                embed = discord.Embed(title=submissions[index].title, description=submissions[index].selftext,
                                      url=f'https://reddit.com{submissions[index].permalink}', colour=0xff4300,
                                      timestamp=datetime.datetime.now())
                embed.set_author(name=f'r/{subreddit}',
                                 icon_url='https://www.redditinc.com/assets/images/site/reddit-logo.png',
                                 url=f'https://reddit.com/r/{subreddit}')
                embed.set_footer(
                    text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nPost {index + 1} out of {len(submissions)}')

                next_post = Button(emoji='⏭️', style=discord.ButtonStyle.green)
                previous_post = Button(emoji='⏮️', style=discord.ButtonStyle.green)
                end_interaction = Button(label='End Interaction', style=discord.ButtonStyle.red)

                view = View(timeout=None)
                view.add_item(previous_post)
                view.add_item(next_post)
                view.add_item(end_interaction)

                # Checking if the submission is text-only
                if not submissions[0].is_self:
                    if submissions[0].is_video:
                        embed.description += f'\n[Video Link]({submissions[0].url})'
                    else:
                        embed.set_image(url=submissions[0].url)

                try:
                    await ctx.send(embed=embed, view=view)
                except discord.HTTPException:
                    embed = discord.Embed(description='The post content was too long to be sent', colour=0xff4300)
                    await ctx.send(embed=embed, view=view)

            except AttributeError:
                # Could not get a post
                await send_error_embed(ctx, description='Could not retrieve a post from **r/{subreddit}**')

            except asyncprawcore.exceptions.AsyncPrawcoreException as e:
                await send_error_embed(ctx, description=str(e))

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

            embed.title = submissions[index].title
            embed.description = submissions[index].selftext
            embed.url = f'https://reddit.com{submissions[index].permalink}'
            embed.set_footer(
                text=f'⬆️ {submissions[index].ups} | ⬇️ {submissions[index].downs} | 💬 {submissions[index].num_comments}\nPost {index + 1} out of {len(submissions)}')

            # Checking if the submission is text-only
            if submissions[index].is_self:
                embed.set_image(url=discord.Embed.Empty)

            elif submissions[index].is_video:
                embed.description += f'\n[Video Link]({submissions[index].url})'
                embed.set_image(url=submissions[index].thumbnail)

            else:
                embed.set_image(url=submissions[index].url)
                embed.description = ''

            try:
                await interaction.response.edit_message(embed=embed)
            except discord.HTTPException:
                embed.description = 'The post content was too long to be sent'
                await interaction.response.edit_message(embed=embed)

        async def previous_post_trigger(interaction):
            nonlocal index
            # Callback to previous_post triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            if index == 0:
                index = len(submissions) - 1
            else:
                index -= 1

            embed.title = submissions[index].title
            embed.description = submissions[index].selftext if submissions[index].is_self else ''
            embed.url = f'https://reddit.com{submissions[index].permalink}'
            embed.set_footer(
                text=f'⬆️ {submissions[index].ups} | ⬇️ {submissions[index].downs} | 💬 {submissions[index].num_comments}\nPost {index + 1} out of {len(submissions)}')

            if submissions[index].is_video:
                embed.description += f'\n[Video Link]({submissions[index].url})'
                embed.set_image(url=submissions[index].thumbnail)
            else:
                embed.set_image(url=submissions[index].url)

            try:
                await interaction.response.edit_message(embed=embed)
            except discord.HTTPException:
                embed.description = 'The post content was too long to be sent'
                await interaction.response.edit_message(embed=embed)

        async def end_interaction_trigger(interaction):
            # Callback to end_interaction triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            next_post.disabled = True
            previous_post.disabled = True
            end_interaction.disabled = True
            await interaction.response.edit_message(view=view)

        next_post.callback = next_post_trigger
        end_interaction.callback = end_interaction_trigger
        previous_post.callback = previous_post_trigger

    @redditpost.error
    async def post_error(self, ctx, error):
        """
        Error handler for the redditpost command
        
        :param ctx: The context of the command
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'This command is on cooldown for {error.retry_after:.2f} seconds')
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify a subreddit\n\nProper Usage: `{self.bot.get_command("redditpost").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    @commands.command(name='trivia', aliases=['fact'], description='Get random trivia', usage='trivia')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def trivia(self, ctx):
        """
        Gets a random trivia fact from the Trivia API
        
        :param ctx: The context of the command
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """

        async def next_trivia_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            nonlocal index
            index += 1
            if index >= len(trivia['results']):
                index = 0

            embed.title = trivia['results'][index]['question']
            embed.description = f'**Answer: {trivia["results"][index]["correct_answer"]}**'
            await interaction.response.edit_message(embed=embed)

        async def previous_trivia_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            nonlocal index
            index -= 1
            if index < 0:
                index = len(trivia['results']) - 1

            embed.title = trivia['results'][index]['question']
            embed.description = f'**Answer: {trivia["results"][index]["correct_answer"]}**'
            await interaction.response.edit_message(embed=embed)

        async def end_interaction_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            next_trivia.disabled = True
            previous_trivia.disabled = True
            end_interaction.disabled = True

            await interaction.response.edit_message(view=view)

        async with ctx.typing():
            trivia = requests.get('https://opentdb.com/api.php?amount=100').json()  # type: dict
            if not trivia['results']:
                await send_error_embed(ctx, description='Could not retrieve a trivia question')
                return

            for item in trivia['results']:
                item['question'] = item['question'].replace('&quot;', '"').replace('&#039;', "'")
                item['correct_answer'] = item['correct_answer'].replace('&quot;', '"').replace('&#039;', "'")

            index = 0  # type: int

            next_trivia = Button(emoji='⏭️', style=discord.ButtonStyle.green)
            previous_trivia = Button(emoji='⏮️', style=discord.ButtonStyle.green)
            end_interaction = Button(label='End Interaction', style=discord.ButtonStyle.red)

            question = trivia['results'][index]['question'].replace('&quot;', '"').replace('&#039;', "'")
            answer = trivia['results'][index]['correct_answer'].replace('&quot;', '"').replace('&#039;', "'")

            embed = discord.Embed(title=question, description=f'**Answer: {answer}**', colour=0xff4300)

            view = View(timeout=None)
            view.add_item(previous_trivia)
            view.add_item(next_trivia)
            view.add_item(end_interaction)

        await ctx.send(embed=embed, view=view)

        next_trivia.callback = next_trivia_trigger
        previous_trivia.callback = previous_trivia_trigger
        end_interaction.callback = end_interaction_trigger

    @trivia.error
    async def trivia_error(self, ctx, error):
        """
        Error handler for the trivia command
        
        :param ctx: The context of the command
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'This command is on cooldown for {error.retry_after:.2f} seconds')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Quote command
    @commands.command(aliases=['qu'], description='Replies with an inspirational quote', usage='quote')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def quote(self, ctx):
        """
        Gets a random quote from zenquotes.io API

        :param ctx: The context of the command

        :type ctx: commands.Context

        :return: None
        :rtype: None
        """

        async def next_quote_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            q = get_quote()
            if q[0]['a'] == 'zenquotes.io':
                await interaction.response.send_message('Please wait for a few seconds', ephemeral=True)
                return

            embed.description = f'> **{q[0]["q"]}**'
            embed.set_author(name=q[0]['a'])
            await interaction.response.edit_message(embed=embed)

        async def end_interaction_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            next_quote.disabled = True
            end_interaction.disabled = True
            await interaction.response.edit_message(view=view)

        async with ctx.typing():
            quote = get_quote()  # type: list[dict[str, str]]

            if quote[0]['a'] == 'zenquotes.io':
                await send_error_embed(ctx, description='Please wait for a few seconds before using this command again')
                return

            embed = discord.Embed(
                description=f'**> {quote[0]["q"]}**',
                colour=discord.Colour.blue()
            )
            embed.set_author(name=quote[0]['a'])

            next_quote = Button(emoji='⏭️', style=discord.ButtonStyle.green)
            end_interaction = Button(emoji='❌', style=discord.ButtonStyle.gray)

            view = View(timeout=None)
            view.add_item(next_quote)
            view.add_item(end_interaction)

        await ctx.send(embed=embed, view=view)

        next_quote.callback = next_quote_trigger
        end_interaction.callback = end_interaction_trigger

    @quote.error
    async def quote_error(self, ctx, error):
        """
        Error handler for the quote command

        :param ctx: The context of the command
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'This command is on cooldown for {error.retry_after:.2f} seconds')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Joke command
    @commands.command(name='joke', description='Get jokes from r/Jokes', usage='joke')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def joke(self, ctx):
        """
        Get a random joke from r/Jokes
        
        :param ctx: The context of the command
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        await ctx.invoke(self.bot.get_command('redditpost'), subreddit='Jokes')

    @joke.error
    async def joke_error(self, ctx, error):
        """
        Error handler for the joke command

        :param ctx: The context of the command
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'This command is on cooldown for {error.retry_after:.2f} seconds')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    @commands.command(name='github',
                      description='Get information on any public github repository\nExample: `github SandeepKanekal/b0ssBot`',
                      usage='github <repository_owner/repository>')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def github(self, ctx, repository):
        """
        Get information on any public github repository
        
        :param ctx: The context of the command
        :param repository: The repository to get information on

        :type ctx: commands.Context
        :type repository: str

        :return: None
        :rtype: None
        """
        async with ctx.typing():
            # Get repository information
            repo_information = requests.get(
                f'https://api.github.com/repos/{repository.split("/")[0]}/{repository.split("/")[1]}').json()

            if 'message' in repo_information:
                await send_error_embed(ctx, description=f'Error: `{repo_information["message"]}`')
                return

            # Make embed
            embed = discord.Embed(
                title=repo_information['name'],
                description=repo_information['description'],
                url=repo_information['html_url'],
                colour=discord.Colour.blurple(),
                timestamp=datetime.datetime.now()
            )
            embed.set_author(name=repo_information['owner']['login'], icon_url=repo_information['owner']['avatar_url'],
                             url=repo_information['owner']['html_url'])
            embed.set_thumbnail(url=repo_information['owner']['avatar_url'])
            embed.set_footer(text='Information retrieved using the GitHub API')

            embed.add_field(name='Language', value=repo_information['language'])
            embed.add_field(name='Forks', value=repo_information['forks'])
            embed.add_field(name='Watchers', value=repo_information['watchers_count'])
            embed.add_field(name='Created at', value=convert_to_unix_time(
                repo_information['created_at'].replace('T', ' ').replace('Z', '')))
            embed.add_field(name='Updated at', value=convert_to_unix_time(
                repo_information['updated_at'].replace('T', ' ').replace('Z', '')))
            embed.add_field(name='Pushed at', value=convert_to_unix_time(
                repo_information['pushed_at'].replace('T', ' ').replace('Z', '')))
            embed.add_field(name='License',
                            value=repo_information['license']['name'] if repo_information['license'] else
                            repo_information['license'])
            embed.add_field(name='Default Branch', value=repo_information['default_branch'])
            embed.add_field(name='Open Issues', value=repo_information['open_issues_count'])

            await ctx.send(embed=embed)

    @github.error
    async def github_error(self, ctx, error):
        """
        Error handler for the github command

        :param ctx: The context of the command
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'This command is on cooldown for {error.retry_after:.2f} seconds')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')


def setup(bot):
    """
    Loads the cog
    
    :param bot: The bot to load the cog into
    
    :type bot: commands.Bot
    
    :return: None
    :rtype: None
    """
    bot.add_cog(Internet(bot))

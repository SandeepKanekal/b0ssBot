# Copyright (c) 2022 Sandeep Kanekal
# Contains all internet commands
import discord
import os
import datetime
import time
import requests
import wikipedia
import asyncprawcore
import ui_components as ui
import imgurpython as imgur
from googleapiclient.discovery import build
from discord.ext import commands
from tools import send_error_embed, get_posts, get_quote, convert_to_unix_time, inform_owner


class Internet(commands.Cog):
    def __init__(self, bot: commands.Bot):
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
    async def youtubesearch(self, ctx: commands.Context, *, query):
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
            embed.add_field(name='Result:', value=f'[{titles[0]}](https://www.youtube.com/watch?v={video_ids[0]})')
            embed.add_field(name='Video Author:', value=f'[{authors[0]}](https://youtube.com/channel/{channel_ids[0]})')
            embed.add_field(name='Publish Date:', value=f'{publish_dates[0]}')
            embed.set_image(url=thumbnails[0])
            embed.set_author(name='YouTube',
                             icon_url='https://yt3.ggpht.com/584JjRp5QMuKbyduM_2k5RlXFqHJtQ0qLIPZpwbUjMJmgzZngHcam5JMuZQxyzGMV5ljwJRl0Q=s176-c-k-c0x00ffffff-no-rj',
                             url='https://www.youtube.com/')
            embed.set_footer(
                text=f'Duration: {stats["items"][0]["contentDetails"]["duration"].strip("PT")}, 🎥: {stats["items"][0]["statistics"]["viewCount"]}, 👍: {stats["items"][0]["statistics"]["likeCount"] if "likeCount" in stats["items"][0]["statistics"].keys() else "Could not fetch likes"}\nResult {index + 1} out of 50')

            items = {
                'titles': titles,
                'thumbnails': thumbnails,
                'video_ids': video_ids,
                'publish_dates': publish_dates,
                'authors': authors,
                'channel_ids': channel_ids
            }

        await ctx.send(embed=embed,
                       view=ui.YouTubeSearchView(ctx=ctx, items=items, youtube=youtube, embed=embed,
                                                 bot=self.bot,
                                                 timeout=None))

    @youtubesearch.error
    async def youtubesearch_error(self, ctx: commands.Context, error: commands.CommandError):
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
        await send_error_embed(ctx,
                               description='An error has occurred while running the youtubesearch command! The owner has been notified.')
        await inform_owner(self.bot, error)

    # Wikipedia command
    @commands.command(aliases=['wiki', 'wikisearch'], description='Gets a summary of the query from wikipedia',
                      usage='wikipedia <query>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wikipedia(self, ctx: commands.Context, *, query: str):
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
    async def wikipedia_error(self, ctx: commands.Context, error: commands.CommandError):
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
        await send_error_embed(ctx,
                               description='An error has occurred while running the wikipedia command! The owner has been notified.')
        await inform_owner(self.bot, error)

    # Weather command
    @commands.command(name='weather', description='Get the weather for a location', usage='weather <location>')
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def weather(self, ctx: commands.Context, *, location: str):
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
    async def weather_error(self, ctx: commands.Context, error: commands.CommandError):
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
        await send_error_embed(ctx,
                               description='An error has occurred while running the weather command! The owner has been notified.')
        await inform_owner(self.bot, error)

    # Post command
    @commands.command(aliases=['reddit', 'post', 'rp'], description='Gets a post from the specified subreddit',
                      usage='redditpost <subreddit>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def redditpost(self, ctx: commands.Context, subreddit):
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

                # Checking if the submission is text-only
                if not submissions[0].is_self:
                    if submissions[0].is_video:
                        embed.description += f'\n[Video Link]({submissions[0].url})'
                    else:
                        embed.set_image(url=submissions[0].url)

                try:
                    await ctx.send(embed=embed,
                                   view=ui.RedditPostView(ctx=ctx, submissions=submissions, embed=embed,
                                                          timeout=None))
                except discord.HTTPException:
                    embed = discord.Embed(description='The post content was too long to be sent', colour=0xff4300)
                    await ctx.send(embed=embed,
                                   view=ui.RedditPostView(ctx=ctx, submissions=submissions, embed=embed,
                                                          timeout=None))

            except AttributeError:
                # Could not get a post
                await send_error_embed(ctx, description='Could not retrieve a post from **r/{subreddit}**')

            except asyncprawcore.exceptions.AsyncPrawcoreException as e:
                await send_error_embed(ctx, description=str(e))

    @redditpost.error
    async def post_error(self, ctx: commands.Context, error: commands.CommandError):
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
        await send_error_embed(ctx,
                               description='An error has occurred while running the redditpost command! The owner has been notified.')
        await inform_owner(self.bot, error)

    @commands.command(name='trivia', aliases=['fact'], description='Get random trivia', usage='trivia')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def trivia(self, ctx: commands.Context):
        """
        Gets a random trivia fact from the Trivia API
        
        :param ctx: The context of the command
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        async with ctx.typing():
            trivia = requests.get('https://opentdb.com/api.php?amount=100').json()  # type: dict
            if not trivia['results']:
                await send_error_embed(ctx, description='Could not retrieve a trivia question')
                return

            question = trivia['results'][0]['question'].replace('&quot;', '"').replace('&#039;', "'")
            answer = trivia['results'][0]['correct_answer'].replace('&quot;', '"').replace('&#039;', "'")

            embed = discord.Embed(title=question, description=f'**Answer:** ||**{answer}**||', colour=0xff4300)
            embed.set_footer(text=f'Question 1 out of {len(trivia["results"])}')

        await ctx.send(embed=embed, view=ui.TriviaView(ctx=ctx, items=trivia, embed=embed, timeout=None))

    @trivia.error
    async def trivia_error(self, ctx: commands.Context, error: commands.CommandError):
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
        await send_error_embed(ctx,
                               description='An error has occurred while running the trivia command! The owner has been notified.')
        await inform_owner(self.bot, error)

    # Quote command
    @commands.command(aliases=['qu'], description='Replies with an inspirational quote', usage='quote')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def quote(self, ctx: commands.Context):
        """
        Gets a random quote from zenquotes.io API

        :param ctx: The context of the command

        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
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

        await ctx.send(embed=embed,
                       view=ui.QuoteView(ctx=ctx, url='https://zenquotes.io/api/random', embed=embed,
                                         timeout=None))

    @quote.error
    async def quote_error(self, ctx: commands.Context, error: commands.CommandError):
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
        await send_error_embed(ctx,
                               description='An error has occurred while running the quote command! The owner has been notified.')
        await inform_owner(self.bot, error)

    # Joke command
    @commands.command(name='joke', description='Get jokes from r/Jokes', usage='joke')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def joke(self, ctx: commands.Context):
        """
        Get a random joke from r/Jokes
        
        :param ctx: The context of the command
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        await ctx.invoke(self.bot.get_command('redditpost'), subreddit='Jokes')

    @joke.error
    async def joke_error(self, ctx: commands.Context, error: commands.CommandError):
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
        await send_error_embed(ctx,
                               description='An error has occurred while running the joke command! The owner has been notified.')
        await inform_owner(self.bot, error)

    @commands.command(name='github',
                      description='Get information on any public github repository\nExample: `github SandeepKanekal/b0ssBot`',
                      usage='github <repository_owner/repository>')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def github(self, ctx: commands.Context, repository):
        """
        Get information on any public GitHub repository
        
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

            if repository.lower() == 'sandeepkanekal/b0ssbot':
                embed.set_footer(text='This is my source code 😂')
            else:
                embed.set_footer(text='Information retrieved using the GitHub API')

            embed.add_field(name='Language', value=repo_information['language'])
            embed.add_field(name='Forks', value=repo_information['forks'])
            embed.add_field(name='Watchers', value=repo_information['watchers_count'])
            embed.add_field(name='Created on', value=convert_to_unix_time(
                repo_information['created_at'].replace('T', ' ').replace('Z', ''), 'D'))
            embed.add_field(name='Last Update', value=convert_to_unix_time(
                repo_information['updated_at'].replace('T', ' ').replace('Z', '')))
            embed.add_field(name='Last Push', value=convert_to_unix_time(
                repo_information['pushed_at'].replace('T', ' ').replace('Z', '')))
            embed.add_field(name='License',
                            value=repo_information['license']['name'] if repo_information['license'] else
                            repo_information['license'])
            embed.add_field(name='Default Branch', value=repo_information['default_branch'])
            embed.add_field(name='Open Issues', value=repo_information['open_issues_count'])

        await ctx.send(embed=embed)

    @github.error
    async def github_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the GitHub command

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
        await send_error_embed(ctx,
                               description='An error has occurred while running the github command! The owner has been notified.')
        await inform_owner(self.bot, error)

    @commands.command(name='imgur', description='Get an image from imgur', usage='imgur <query>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def imgur(self, ctx: commands.Context, *, query: str):
        """
        Get the images on the imgur frontpage library

        :param ctx: The context of the command
        :param query: The query to search for

        :type ctx: commands.Context
        :type query: str
        
        :return: None
        :rtype: None
        """
        async with ctx.typing():
            client = imgur.ImgurClient(client_id='03482b4803edf31', client_secret=os.getenv('imgur_client_secret'))
            images = client.gallery_search(q=query, sort='top', window='all', page=0)
            if not images:
                await send_error_embed(ctx, description='No images found')
                return

            await ctx.send(content=f'Image 1 out of {len(images)}\n{images[0].link}',
                           view=ui.ImgurView(ctx=ctx, items=images, timeout=None))

    @imgur.error
    async def imgur_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the imgur command

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
        await send_error_embed(ctx,
                               description='An error has occurred while running the imgur command! The owner has been notified.')
        await inform_owner(self.bot, error)


def setup(bot: commands.Bot):
    """
    Loads the cog
    
    :param bot: The bot to load the cog into
    
    :type bot: commands.Bot
    
    :return: None
    :rtype: None
    """
    bot.add_cog(Internet(bot))

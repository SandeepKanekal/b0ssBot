import random
import discord
import asyncpraw
import asyncprawcore
import datetime
from discord.ext import commands
from discord.ui import Button, View


# Gets post from the specified subreddit
async def get_post(subreddit):
    reddit = asyncpraw.Reddit('bot', user_agent='bot user agent')
    subreddit = await reddit.subreddit(subreddit)
    sub = []
    submissions = subreddit.hot()
    async for submission in submissions:
        sub.append(submission)
    return sub


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 8ball for fun
    @commands.command(name='8ball', description='Ask a question, and get a reply!')
    async def eight_ball(self, ctx, *, question):
        # Response list
        responses = [
            'Yes!',
            'No!',
            'Hell yea!',
            'Never',
            'Of course that\'s a NO!',
            'Maybe',
            'Probably',
            'Are you kidding me? Yes!',
            'Nope, straight nope',
        ]

        response = random.choice(responses)
        if 'tiktok' in question or 'tik tok' in question:
            # TikTok is just horrible
            response = 'tiktok IS THE ABSOLUTE WORST, PLEASE STOP WASTING MY TIME ASKING SUCH OBVIOUS QUESTIONS!'
        embed = discord.Embed(title=f':8ball: {question}', description=response, colour=discord.Colour.random())
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(text=f'Requested by {ctx.author}')
        await ctx.send(embed=embed)

    # Meme command
    @commands.command(aliases=['m'], description='Posts memes from the most famous meme subreddits')
    async def meme(self, ctx):
        subreddit = random.choice(['memes', 'dankmemes', 'meme'])
        submissions = await get_post(subreddit)
        submissions.pop(0)  # Pops the pinned post

        button1 = Button(label='Next Meme', style=discord.ButtonStyle.green)  # The button for going to the next meme
        button2 = Button(label='End Interaction', style=discord.ButtonStyle.red)  # The button the end the interaction

        async def next_meme(interaction):
            # Callback to button1 triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            if len(submissions) == 0:
                # This probably will never happen
                await interaction.response.edit_message(content='No more memes available.')
                return

            submissions.pop(0)  # Pop the previous submission
            embed.title = submissions[0].title
            embed.url = f'https://reddit.com{submissions[0].permalink}'
            embed.set_image(url=submissions[0].url)
            embed.set_footer(
                text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nRequested by {ctx.author}')
            embed.timestamp = datetime.datetime.now()
            await interaction.response.edit_message(embed=embed)

        async def end_interaction(interaction):
            # Callback to button2 triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            await interaction.response.edit_message(view=None)

        view = View()
        view.add_item(button1)
        view.add_item(button2)
        embed = discord.Embed(title=submissions[0].title, url=f'https://reddit.com{submissions[0].permalink}',
                              colour=discord.Colour.random())
        embed.set_image(url=submissions[0].url)
        embed.set_footer(
            text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nRequested by {ctx.author}')
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed, view=view)
        # Callbacks
        button1.callback = next_meme
        button2.callback = end_interaction

    # Dankvideo command
    @commands.command(aliases=['dv', 'dankvid'], description='Posts dank videos from r/dankvideos')
    async def dankvideo(self, ctx):
        submission = await get_post('dankvideos')
        submission = random.choice(submission)
        await ctx.send('https://reddit.com' + submission.permalink)

    # Coinflip command
    @commands.command(aliases=['cf'], description='Heads or Tails?')
    async def coinflip(self, ctx):
        result = random.choice(['Heads', 'Tails'])
        embed = discord.Embed(title=':coin: Coinflip!', colour=discord.Colour.random())
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.add_field(name='Result:', value=result)
        await ctx.send(embed=embed)

    # Post command
    @commands.command(aliases=['reddit', 'redditpost', 'rp'], description='Gets a post from the specified subreddit')
    async def post(self, ctx, subreddit):

        async def next_post_trigger(interaction):
            # Callback to next_post triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            submissions.pop(0)  # Popping previous submission
            embed_next = discord.Embed(colour=discord.Colour.orange())
            embed_next.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)

            if len(submissions) == 0:
                embed_next.description = f'No more posts available in {subreddit}'
                embed_next.title = None
                embed_next.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                await interaction.response.edit_message(embed=embed_next, view=None)

            if not submissions[0].over_18:
                # NSFW posts are not allowed
                embed_next.title = submissions[0].title
                embed_next.description = submissions[0].selftext
                embed_next.url = f'https://reddit.com{submissions[0].permalink}'
                embed_next.set_footer(
                    text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nRequested by {ctx.author}')
                embed.timestamp = datetime.datetime.now()

                # Checking if the attachment is a video
                if submissions[0].url.startswith('https://v.redd.it/') \
                        and submissions[0].url.startswith('http://www.youtube.com/') \
                        and submissions[0].url.startswith('https://youtu.be/'):
                    embed_next.description = 'Attachment contains video'

                # Checking if the submission is text-only
                if not submissions[0].is_self:
                    embed_next.set_image(url=submissions[0].url)

                try:
                    await interaction.response.edit_message(embed=embed_next, view=view)
                except discord.HTTPException:
                    embed_next.description = 'The post content was too long to be sent'
                    await ctx.send(embed=embed_next)

            else:
                # NSFW posts are not shown
                embed_next = discord.Embed(description='This post has been marked as NSFW',
                                           colour=discord.Colour.orange())
                embed_next.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                embed_next.set_footer(
                    text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nRequested by {ctx.author}')
                embed.timestamp = datetime.datetime.now()
                view_post_in = Button(label='View Post', url=f'https://reddit.com{submissions[0].permalink}')
                view.add_item(view_post_in)
                await interaction.response.edit_message(embed=embed_next, view=view)
                view.remove_item(view_post_in)

        async def end_interaction_trigger(interaction):
            # Callback to end_interaction triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            await interaction.response.edit_message(view=None)

        try:
            submissions = await get_post(subreddit)
            embed = discord.Embed(colour=discord.Colour.orange())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            next_post = Button(label='Next Post', style=discord.ButtonStyle.green)
            end_interaction = Button(label='End Interaction', style=discord.ButtonStyle.red)
            view = View()
            view.add_item(next_post)
            view.add_item(end_interaction)
            next_post.callback = next_post_trigger
            end_interaction.callback = end_interaction_trigger

            if not submissions[0].over_18:
                # NSFW posts are not allowed
                embed.title = submissions[0].title
                embed.description = submissions[0].selftext
                embed.url = submissions[0].url
                embed.set_footer(
                    text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nRequested by {ctx.author}')
                embed.timestamp = datetime.datetime.now()

                # Checking if the attachment is a video
                if submissions[0].url.startswith('https://v.redd.it/') \
                        and submissions[0].url.startswith('http://www.youtube.com/') \
                        and submissions[0].url.startswith('https://youtu.be/'):
                    embed.description = 'Attachment contains video'
                    video_button = Button(label='Open Video', url=submissions[0].url)
                    view.add_item(video_button)

                # Checking if the submission is text-only
                if not submissions[0].is_self:
                    embed.set_image(url=submissions[0].url)

                try:
                    await ctx.send(embed=embed, view=view)
                except discord.HTTPException:
                    embed = discord.Embed(description='The post content was too long to be sent',
                                          colour=discord.Colour.orange())
                    await ctx.send(embed=embed, view=view)

            else:
                # NSFW posts are not shown
                embed = discord.Embed(description='This post has been marked as NSFW', colour=discord.Colour.orange())
                embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                next_post = Button(label='Next Post', style=discord.ButtonStyle.green)
                end_interaction = Button(label='End Interaction', style=discord.ButtonStyle.red)
                view_post = Button(label='View Post', url=f'https://reddit.com{submissions[0].permalink}')
                view = View()
                view.add_item(next_post)
                view.add_item(end_interaction)
                view.add_item(view_post)
                embed.set_footer(
                    text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nRequested by {ctx.author}')
                embed.timestamp = datetime.datetime.now()
                await ctx.send(embed=embed)

        except AttributeError:
            # Could not get a post
            embed = discord.Embed(
                description=f'Could not get posts from r/**{subreddit}**',
                colour=discord.Colour.orange())
            button = Button(label=f'Open r/{subreddit} in Reddit', url=f'https://reddit.com/r/{subreddit}')
            view = View()
            view.add_item(button)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed, view=view)

        except asyncprawcore.exceptions.NotFound:
            # Subreddit does not exist
            embed = discord.Embed(description=f'The subreddit r/**{subreddit}** does not exist',
                                  colour=discord.Colour.orange())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

        except asyncprawcore.exceptions.Forbidden:
            # Private subreddits
            embed = discord.Embed(description=f'The subreddit r/**{subreddit}** is a private community',
                                  colour=discord.Colour.orange())
            button = Button(label='Join Community', url=f'https://reddit.com/r/{subreddit}')
            view = View()
            view.add_item(button)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed, view=view)

        except asyncprawcore.exceptions.Redirect:
            embed = discord.Embed(description=f'The subreddit r/**{subreddit}** redirects to another website',
                                  colour=discord.Colour.orange())
            button = Button(label='Open in Reddit', url=f'https://reddit.com/r/{subreddit}')
            view = View()
            view.add_item(button)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed, view=view)

        except asyncprawcore.exceptions.ServerError:
            embed = discord.Embed(description='Server Error', colour=discord.Colour.orange())
            button = Button(label='Open in Reddit', url=f'https://reddit.com/r/{subreddit}')
            view = View()
            view.add_item(button)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed, view=view)

        except asyncprawcore.exceptions.TooManyRequests:
            embed = discord.Embed(description='Too many requests, use the command after some time',
                                  colour=discord.Colour.orange())
            button = Button(label='Open in Reddit', url=f'https://reddit.com/r/{subreddit}')
            view = View()
            view.add_item(button)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed, view=view)

        except asyncprawcore.exceptions.UnavailableForLegalReasons:
            embed = discord.Embed(
                description=f'Could not get posts from r/**{subreddit}** for legal reasons',
                colour=discord.Colour.orange())
            button = Button(label='Open in Reddit', url=f'https://reddit.com/r/{subreddit}')
            view = View()
            view.add_item(button)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed, view=view)


def setup(bot):
    bot.add_cog(Fun(bot))

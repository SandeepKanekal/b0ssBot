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


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description):
    # Response embed
    embed = discord.Embed(description=description, colour=discord.Colour.red())
    await ctx.send(embed=embed)


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 8ball for fun
    @commands.command(name='8ball', aliases=['8b'], description='Ask a question, and get a reply!')
    async def eight_ball(self, ctx, *, question):
        # Response list
        responses = [
            "As I see it, yes.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "It is certain.",
            "It is decidedly so.",
            "Most likely.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Outlook good.",
            "Reply hazy, try again.",
            "Signs point to yes.",
            "Very doubtful.",
            "Without a doubt.",
            "Yes.",
            "Yes - definitely.",
            "You may rely on it."
        ]

        response = random.choice(responses)
        if 'tiktok' in question.lower() or 'tik tok' in question.lower():
            # TikTok is just horrible
            response = 'tiktok IS THE ABSOLUTE WORST, PLEASE STOP WASTING MY TIME ASKING SUCH OBVIOUS QUESTIONS!'
        embed = discord.Embed(title=f':8ball: {question}', description=response, colour=discord.Colour.random())
        await ctx.send(embed=embed)

    @eight_ball.error
    async def eight_ball_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Meme command
    @commands.command(aliases=['m'], description='Posts memes from the most famous meme subreddits')
    async def meme(self, ctx):
        subreddit = random.choice(['memes', 'dankmemes', 'meme'])
        submissions = await get_post(subreddit)
        submissions.pop(0)  # Pops the pinned post
        if not ctx.channel.is_nsfw():  # Filters out nsfw posts if the channel is not marked NSFW
            submissions = list(filter(lambda s: not s.over_18, submissions))

        next_meme = Button(label='Next Meme', style=discord.ButtonStyle.green)  # The button for going to the next meme
        end_interaction = Button(label='End Interaction',
                                 style=discord.ButtonStyle.red)  # The button the end the interaction
        view_post = Button(label='View Post',
                           url=f'https://reddit.com{submissions[0].permalink}')  # The button to open the post in Reddit

        async def next_meme_trigger(interaction):
            # Callback to button1 triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            if not len(submissions):
                # This probably will never happen
                await interaction.response.edit_message(content='No more memes available.')
                return

            submissions.pop(0)  # Pop the previous submission
            view.remove_item(view_post)
            view_post.url = f'https://reddit.com{submissions[0].permalink}'
            view.add_item(view_post)

            embed.title = submissions[0].title
            embed.url = f'https://reddit.com{submissions[0].permalink}'
            embed.set_image(url=submissions[0].url)
            embed.set_footer(
                text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nSession for {ctx.author}')
            embed.timestamp = datetime.datetime.now()
            await interaction.response.edit_message(embed=embed, view=view)

        async def end_interaction_trigger(interaction):
            # Callback to button2 triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            view.remove_item(next_meme)
            view.remove_item(end_interaction)
            await interaction.response.edit_message(view=view)

        view = View()
        view.add_item(next_meme)
        view.add_item(end_interaction)
        view.add_item(view_post)
        embed = discord.Embed(title=submissions[0].title, url=f'https://reddit.com{submissions[0].permalink}',
                              colour=discord.Colour.random())
        embed.set_image(url=submissions[0].url)
        embed.set_footer(
            text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nSession for {ctx.author}')
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed, view=view)
        # Callbacks
        next_meme.callback = next_meme_trigger
        end_interaction.callback = end_interaction_trigger
    
    @meme.error
    async def meme_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Dankvideo command
    @commands.command(aliases=['dv', 'dankvid'], description='Posts dank videos from r/dankvideos')
    async def dankvideo(self, ctx):
        submission = await get_post(random.choice(['dankvideos', 'cursed_videomemes']))
        if not ctx.channel.is_nsfw():  # Filters out nsfw posts if the channel is not marked NSFW
            submission = list(filter(lambda s: not s.over_18, submission))
        submission = random.choice(submission)
        await ctx.send(f'https://reddit.com{submission.permalink}')
    
    @dankvideo.error
    async def dankvideo_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Coinflip command
    @commands.command(aliases=['cf'], description='Heads or Tails?')
    async def coinflip(self, ctx):
        result = random.choice(['Heads', 'Tails'])
        embed = discord.Embed(title=':coin: Coinflip!', colour=discord.Colour.random())
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.add_field(name='Result:', value=result)
        await ctx.send(embed=embed)
    
    @coinflip.error
    async def coinflip_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Post command
    @commands.command(aliases=['reddit', 'redditpost', 'rp'], description='Gets a post from the specified subreddit')
    async def post(self, ctx, subreddit):

        async def next_post_trigger(interaction):
            # Callback to next_post triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            if not len(submissions):
                await send_error_embed(ctx, description=f'No more posts available in r/{subreddit}')
                return

            submissions.pop(0)  # Popping previous submission
            view.remove_item(view_post)
            view_post.url = f'https://reddit.com{submissions[0].permalink}'
            view.add_item(view_post)
            embed_next = discord.Embed(colour=discord.Colour.orange())
            embed_next.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            embed_next.title = submissions[0].title
            embed_next.description = submissions[0].selftext
            embed_next.url = f'https://reddit.com{submissions[0].permalink}'
            embed_next.set_footer(
                text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nSession for {ctx.author}')
            embed_next.timestamp = datetime.datetime.now()

            # Checking if the submission is text-only
            if not submissions[0].is_self:
                embed_next.set_image(url=submissions[0].url)

            try:
                await interaction.response.edit_message(embed=embed_next, view=view)
            except discord.HTTPException:
                embed_next.description = 'The post content was too long to be sent'
                await ctx.send(embed=embed_next)

        async def end_interaction_trigger(interaction):
            # Callback to end_interaction triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            view.remove_item(next_post)
            view.remove_item(end_interaction)
            await interaction.response.edit_message(view=view)

        try:
            submissions = await get_post(subreddit)
            if not ctx.channel.is_nsfw():  # Filters out nsfw posts if the channel is not marked NSFW
                submissions = list(filter(lambda s: not s.over_18, submissions))
            if not len(submissions):
                await send_error_embed(ctx, description=f'The subreddit **r/{subreddit}** has been marked as NSFW, please use the same command in a NSFW channel.')
            embed = discord.Embed(colour=discord.Colour.orange())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            next_post = Button(label='Next Post', style=discord.ButtonStyle.green)
            end_interaction = Button(label='End Interaction', style=discord.ButtonStyle.red)
            view_post = Button(label='View Post', url=f'https://reddit.com{submissions[0].permalink}')
            view = View()
            view.add_item(next_post)
            view.add_item(end_interaction)
            view.add_item(view_post)
            next_post.callback = next_post_trigger
            end_interaction.callback = end_interaction_trigger

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
            await send_error_embed(description='Could not retrieve a post from **r/{subreddit}**')

        except asyncprawcore.exceptions.AsyncPrawcoreException as e:
            await send_error_embed(description=e)

    @post.error
    async def post_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')


def setup(bot):
    bot.add_cog(Fun(bot))

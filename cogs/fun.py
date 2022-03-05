import random
import discord
import asyncpraw
import datetime
from discord.ext import commands
from discord.ui import Button, View

today = datetime.date.today()


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
        embed = discord.Embed(title='8ball', colour=discord.Colour.random())
        embed.add_field(name=question, value=f':8ball:{response}')
        await ctx.send(embed=embed)

    # Meme command
    @commands.command(aliases=['m'], description='Posts memes from the most famous meme subreddits')
    async def meme(self, ctx):
        subreddit = random.choice(['memes', 'dankmemes', 'meme'])
        submissions = await get_post(subreddit)
        submissions.pop(0)

        button1 = Button(label='Next Meme', style=discord.ButtonStyle.green)
        button2 = Button(label='End Interaction', style=discord.ButtonStyle.red)

        async def next_meme(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            if len(submissions) == 0:
                await interaction.response.edit_message(content='No more memes available.')
                return

            submissions.pop(0)
            embed.title = submissions[0].title
            embed.url = f'https://reddit.com{submissions[0].permalink}'
            embed.set_image(url=submissions[0].url)
            embed.set_footer(
                text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}')
            await interaction.response.edit_message(embed=embed)

        async def end_interaction(interaction):
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
            text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}')
        await ctx.send(embed=embed, view=view)
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


def setup(bot):
    bot.add_cog(Fun(bot))

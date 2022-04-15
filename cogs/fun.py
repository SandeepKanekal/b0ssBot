import random
import discord
import asyncpraw
import datetime
from discord.ext import commands
from sql_tools import SQL
from discord.ui import Button, View


# Gets post from the specified subreddit
async def get_post(subreddit: str) -> list:
    reddit = asyncpraw.Reddit('bot', user_agent='bot user agent')
    subreddit = await reddit.subreddit(subreddit)
    sub = []
    submissions = subreddit.hot()
    async for submission in submissions:
        sub.append(submission)
    return sub


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description: str) -> None:
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
            "As I see it, yes",
            "Ask again later",
            "Better not tell you now",
            "Cannot predict now",
            "Concentrate and ask again",
            "Don't count on it",
            "It is certain",
            "It is decidedly so",
            "Most likely",
            "My reply is no",
            "My sources say no",
            "Outlook not so good",
            "Outlook good",
            "Reply hazy, try again",
            "Signs point to yes",
            "Very doubtful",
            "Without a doubt",
            "Yes",
            "Yes - definitely",
            "You may rely on it"
        ]

        response = random.choice(responses)
        if 'tiktok' in question.lower() or 'tik tok' in question.lower():
            # TikTok is just horrible
            response = 'tiktok IS THE ABSOLUTE WORST, PLEASE STOP WASTING MY TIME ASKING SUCH OBVIOUS QUESTIONS[!](https://bit.ly/3JgQ1QH)'
        else:
            response = f'{response}[.](https://bit.ly/3JgQ1QH)'
        embed = discord.Embed(title=f':8ball: {question}', description=response, colour=discord.Colour.random())
        await ctx.send(embed=embed)

    @eight_ball.error
    async def eight_ball_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    @commands.command(aliases=['roll'], description='Rolls a dice')
    async def dice(self, ctx):

        async def callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return
            await interaction.response.edit_message(content='**Rolling**')
            await interaction.followup.edit_message(content='**Rolling.**', message_id=msg.id)
            await interaction.followup.edit_message(content='**Rolling..**', message_id=msg.id)
            await interaction.followup.edit_message(content='**Rolling...**', message_id=msg.id)
            await interaction.followup.edit_message(content=f'**You rolled a {random.randint(1, 6)}!** :game_die:',
                                                    message_id=msg.id)

        async def end_interaction_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return
            await interaction.response.edit_message(view=None)

        msg = await ctx.send('**Rolling**')
        await msg.edit('**Rolling.**')
        await msg.edit('**Rolling..**')
        await msg.edit('**Rolling...**')
        roll = Button(label='Roll again', style=discord.ButtonStyle.green)
        end_interaction = Button(label='Stop Rolling', style=discord.ButtonStyle.red)
        view = View()
        view.add_item(roll)
        view.add_item(end_interaction)
        await msg.edit(f'**You rolled a {random.randint(1, 6)}! :game_die:**', view=view)
        roll.callback = callback
        end_interaction.callback = end_interaction_trigger

    # Meme command
    @commands.command(aliases=['m'], description='Posts memes from the most famous meme subreddits')
    async def meme(self, ctx):
        index = 0
        subreddit = random.choice(['memes', 'dankmemes', 'meme'])
        submissions = await get_post(subreddit)
        submissions.pop(0)  # Pops the pinned post
        if not ctx.channel.is_nsfw():  # Filters out nsfw posts if the channel is not marked NSFW
            submissions = list(filter(lambda s: not s.over_18, submissions))

        next_meme = Button(style=discord.ButtonStyle.green, emoji='⏭️')  # The button for going to the next meme
        end_interaction = Button(label='End Interaction',
                                 style=discord.ButtonStyle.red)  # The button the end the interaction
        previous_meme = Button(emoji='⏮️', style=discord.ButtonStyle.green)  # The button for going to the previous meme

        view = View()
        view.add_item(previous_meme)
        view.add_item(next_meme)
        view.add_item(end_interaction)
        embed = discord.Embed(title=submissions[0].title, url=f'https://reddit.com{submissions[0].permalink}',
                              colour=discord.Colour.random())
        embed.set_image(url=submissions[0].url)
        embed.set_footer(
            text=f'⬆️ {submissions[0].ups} | ⬇️ {submissions[0].downs} | 💬 {submissions[0].num_comments}\nSession for {ctx.author}')
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed, view=view)

        async def next_meme_trigger(interaction):
            nonlocal index  # index variable is nonlocal
            # Callback to button1 triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            if index == len(submissions) - 1:  # If the index is at the last meme, go back to the first one
                index = 0
            else:
                index += 1  # Otherwise, go to the next meme

            embed.title = submissions[index].title
            embed.url = f'https://reddit.com{submissions[index].permalink}'
            embed.set_image(url=submissions[index].url)
            embed.set_footer(
                text=f'⬆️ {submissions[index].ups} | ⬇️ {submissions[index].downs} | 💬 {submissions[index].num_comments}\nSession for {ctx.author}')
            embed.timestamp = datetime.datetime.now()
            await interaction.response.edit_message(embed=embed)

        async def previous_meme_trigger(interaction):
            nonlocal index  # index variable is nonlocal
            # Callback to button2 triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            if index == 0:
                await interaction.response.send_message(content='This is the first meme.', ephemeral=True)
                index += 1
                return

            index -= 1
            embed.title = submissions[index].title
            embed.url = f'https://reddit.com{submissions[index].permalink}'
            embed.set_image(url=submissions[index].url)
            embed.set_footer(
                text=f'⬆️ {submissions[index].ups} | ⬇️ {submissions[index].downs} | 💬 {submissions[index].num_comments}\nSession for {ctx.author}')
            embed.timestamp = datetime.datetime.now()
            await interaction.response.edit_message(embed=embed)

        async def end_interaction_trigger(interaction):
            # Callback to button2 triggers this function
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            view.remove_item(next_meme)
            view.remove_item(end_interaction)
            view.remove_item(previous_meme)
            await interaction.response.edit_message(view=None)

        # Callbacks
        next_meme.callback = next_meme_trigger
        end_interaction.callback = end_interaction_trigger
        previous_meme.callback = previous_meme_trigger

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
        async def callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return
            await interaction.response.edit_message(content='**Flipping**')
            await interaction.followup.edit_message(content='**Flipping.**', message_id=msg.id)
            await interaction.followup.edit_message(content='**Flipping..**', message_id=msg.id)
            await interaction.followup.edit_message(content='**Flipping...**', message_id=msg.id)
            await interaction.followup.edit_message(
                content=f'**You flipped a {random.choice(["Heads", "Tails"])}!** :coin:',
                message_id=msg.id)

        async def end_interaction_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return
            await interaction.response.edit_message(view=None)

        msg = await ctx.send('**Flipping**')
        await msg.edit('**Flipping.**')
        await msg.edit('**Flipping..**')
        await msg.edit('**Flipping...**')
        flip = Button(label='Flip again', style=discord.ButtonStyle.green)
        end_interaction = Button(label='Stop Flipping', style=discord.ButtonStyle.red)
        view = View()
        view.add_item(flip)
        view.add_item(end_interaction)
        await msg.edit(f'**You flipped a {random.choice(["Heads", "Tails"])}! :coin:**', view=view)
        flip.callback = callback
        end_interaction.callback = end_interaction_trigger

    @coinflip.error
    async def coinflip_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Message Response Command
    @commands.command(name='messageresponse', aliases=['message', 'msg', 'response', 'mr'],
                      description='Add a response to be sent when a word or sentence is typed\nSeparate the response from the message using ` | `\nPut a space before and after the `|`\nThis command is case insensitive\nUse 1(True) to add and 0(False) to remove a response\nExample: `-messageresponse 1 hello | Hello there! `\nRemoving does not require a response parameter')
    @commands.has_permissions(manage_guild=True)
    async def message_response(self, ctx, mode: int, *, message_response: str = None):
        # sourcery no-metrics
        sql = SQL('b0ssbot')
        if mode == 0:
            if message_response is None:
                await ctx.send(embed=discord.Embed(description='Please provide a message', colour=discord.Colour.red()))
                return
            if not message_response.strip():
                await ctx.send(embed=discord.Embed(description='Please provide a message', colour=discord.Colour.red()))
                return
            if ' | ' in message_response:
                await ctx.send(embed=discord.Embed(description='Use mode 1 instead to add a response',
                                                   colour=discord.Colour.red()))
                return
            message_response = message_response.replace("'", "''").lower()
            if not sql.select(elements=['message'], table='message_responses',
                              where=f"guild_id = '{ctx.guild.id}' AND message = '{message_response}'"):
                await ctx.send(embed=discord.Embed(description=f'No response found for **{message_response}**',
                                                   colour=discord.Colour.red()))
                return
            sql.delete(table='message_responses',
                       where=f"guild_id = '{ctx.guild.id}' AND message = '{message_response}'")
            message_response = message_response.replace("''", "'")
            await ctx.send(embed=discord.Embed(description=f'Removed the response for **{message_response}**',
                                               colour=discord.Colour.green()))

        elif mode == 1:
            if message_response is None:
                await ctx.send(
                    embed=discord.Embed(description='Please provide a message response', colour=discord.Colour.red()))
                return

            if '|' not in message_response:
                await ctx.send(
                    embed=discord.Embed(description='Please separate the message from the response using `|`',
                                        colour=discord.Colour.red()))
                return

            message, response = message_response.split(' | ')
            if message.strip() == '' or response.strip() == '':
                await ctx.send(
                    embed=discord.Embed(description='Please provide a message and response',
                                        colour=discord.Colour.red()))
                return

            message = message.replace("'", "''").lower()
            response = response.replace("'", "''")
            if sql.select(elements=['message', 'response'], table='message_responses',
                          where=f"guild_id = '{ctx.guild.id}' AND message = '{message}'"):
                sql.update(table='message_responses', column='response', value=f"'{response}'",
                           where=f"guild_id = '{ctx.guild.id}' AND message = '{message}'")
                message = message.replace("'", "''")
                await ctx.send(embed=discord.Embed(description=f'Updated the response for **{message}**',
                                                   colour=discord.Colour.green()))
            else:
                sql.insert(table='message_responses', columns=['guild_id', 'message', 'response'],
                           values=[f"'{ctx.guild.id}'", f"'{message}'", f"'{response}'"])
                message = message.replace("''", "'")
                await ctx.send(
                    embed=discord.Embed(description=f'Added the response for **{message}**',
                                        colour=discord.Colour.green()))

        else:
            await ctx.send(embed=discord.Embed(
                description='Please provide a valid mode\n1(True) adds a response\n0(False) removes a response',
                colour=discord.Colour.red()))

    @message_response.error
    async def message_response_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await send_error_embed(ctx,
                                   description='Please separate the message and the response using ` | ` (with a space in front and back)')
            return
        await send_error_embed(ctx, description=f'Error: {error}')


def setup(bot):
    bot.add_cog(Fun(bot))

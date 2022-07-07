import discord
import random
import requests
import time
import asyncio
import view
from discord.ext import commands
from discord.ui import Button, View
from tools import send_error_embed


class Games(commands.Cog):
    def __init__(self, bot):
        """
        Initialize the cog.
        
        :param bot: The bot object.
        
        :type bot: commands.Bot
        
        :return: None
        :rtype: None
        """
        self.bot = bot  # type: commands.Bot

    # 8ball for fun
    @commands.command(name='8ball', aliases=['8b'], description='Ask a question, and get a reply!',
                      usage='8ball <question>')
    async def eight_ball(self, ctx, *, question: str):
        """
        8ball command

        :param ctx: The context of where the message was sent
        :param question: The question to ask the 8ball

        :type ctx: commands.Context
        :type question: str

        :return: None
        :rtype: None
        """

        if question.lower().startswith('what') \
                or question.lower().startswith('how') \
                or question.lower().startswith('why') \
                or question.lower().startswith('who') \
                or question.lower().startswith('when') \
                or question.lower().startswith('where'):
            # If the question cannot be answered with YES or NO, inform the user to ask a question likewise.
            await send_error_embed(ctx, description='Please ask a question that can be answered with `yes` or `no`')
            return

        # Response list
        responses = [
            'Yes.',
            'No.',
            'Never.',
            'Hell Yea.',
            'Without a Doubt.',
            'Highly doubt that.',
            'Ask again later.',
            'Maybe.',
            'I don\'t know.',
            'I\'m not sure.',
            'I don\'t think so.',
            'Probably.'
        ]

        response = random.choice(responses)
        if 'tiktok' in question.lower() or 'tik tok' in question.lower():
            # TikTok is just horrible
            response = 'tiktok IS THE ABSOLUTE WORST, PLEASE STOP WASTING MY TIME ASKING SUCH OBVIOUS QUESTIONS.'
        embed = discord.Embed(title=f':8ball: {question}', description=response, colour=discord.Colour.random())
        await ctx.send(embed=embed)

    @eight_ball.error
    async def eight_ball_error(self, ctx, error):
        """
        Error handler for the 8ball command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please ask a question!\n\nProper Usage: `{self.bot.get_command("8ball").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    @commands.command(aliases=['roll'], description='Rolls a dice', usage='dice')
    @commands.guild_only()
    async def dice(self, ctx):
        """
        Dice command
        
        :param ctx: The context of where the message was sent

        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """

        msg = await ctx.send('**Rolling**')
        await msg.edit('**Rolling.**')
        await msg.edit('**Rolling..**')
        await msg.edit('**Rolling...**')
        await msg.edit(f'**You rolled a {random.randint(1, 6)}! :game_die:**', view=view.RollView(ctx=ctx, message_id=msg.id, timeout=None))

    # Coinflip command
    @commands.command(aliases=['cf'], description='Heads or Tails?', usage='coinflip')
    @commands.guild_only()
    async def coinflip(self, ctx):
        """
        Coinflip command
        
        :param ctx: The context of where the message was sent

        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        msg = await ctx.send('**Flipping**')
        await msg.edit('**Flipping.**')
        await msg.edit('**Flipping..**')
        await msg.edit('**Flipping...**')
        await msg.edit(f'**You flipped a {random.choice(["Heads", "Tails"])}! :coin:**', view=view.FlipView(ctx=ctx, message_id=msg.id, timeout=None))

    @commands.command(name='truth', description='Get a truth question', usage='truth <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def truth(self, ctx, rating: str = None):
        """
        Truth command
        
        :param ctx: The context of where the message was sent
        :param rating: The rating of the question

        :type ctx: commands.Context
        :type rating: Optional[str]
        
        :return: None
        :rtype: None
        """
        if rating and rating.upper() not in ['PG', 'PG13', 'R']:
            await send_error_embed(ctx,
                                   description='Please enter a valid rating! Valid ratings are `PG`, `PG13`, and `R`')
            return

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/truth?rating={rating}').json() if rating else requests.get(
            f'https://api.truthordarebot.xyz/v1/truth').json()  # type: dict

        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Truth', icon_url=self.bot.user.avatar)

        next_truth = Button(label='Next truth', style=discord.ButtonStyle.green)

        view = View(timeout=None)
        view.add_item(next_truth)

        async def next_truth_trigger(interaction):
            next_truth.disabled = True
            await interaction.response.edit_message(view=view)
            view.stop()
            await self.truth(ctx, rating) if rating else await self.truth(ctx)

        await ctx.send(embed=embed, view=view)
        next_truth.callback = next_truth_trigger

    @truth.error
    async def truth_error(self, ctx, error):
        """
        Truth error handler
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await send_error_embed(ctx,
                                   description=f'You are on cooldown! Please wait {round(error.retry_after, 2)} seconds')

    @commands.command(name='dare', description='Get a dare', usage='dare <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def dare(self, ctx, rating: str = None):
        """
        Dare command
        
        :param ctx: The context of where the message was sent
        :param rating: The rating of the question

        :type ctx: commands.Context
        :type rating: Optional[str]
        
        :return: None
        :rtype: None
        """
        if rating and rating.upper() not in ['PG', 'PG13', 'R']:
            await send_error_embed(ctx,
                                   description='Please enter a valid rating! Valid ratings are `PG`, `PG13`, and `R`')
            return

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/dare?rating={rating}').json() if rating else requests.get(
            f'https://api.truthordarebot.xyz/v1/dare').json()  # type: dict

        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Dare', icon_url=self.bot.user.avatar)

        next_dare = Button(label='Next Dare', style=discord.ButtonStyle.green)

        view = View(timeout=None)
        view.add_item(next_dare)

        async def next_dare_trigger(interaction):
            next_dare.disabled = True
            await interaction.response.edit_message(view=view)
            view.stop()
            
            await self.dare(ctx, rating) if rating else await self.dare(ctx)

        await ctx.send(embed=embed, view=view)
        next_dare.callback = next_dare_trigger

    @dare.error
    async def dare_error(self, ctx, error):
        """
        Dare error handler
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await send_error_embed(ctx,
                                   description=f'You are on cooldown! Please wait {round(error.retry_after, 2)} seconds')

    @commands.command(name='truthordare', aliases=['tord'], description='Get a truth or dare',
                      usage='truthordare <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def truthordare(self, ctx, rating: str = None, truthordare: str = None):
        """
        Truth or dare command

        :param ctx: The context of where the message was sent
        :param rating: The rating of the question
        :param truthordare: Stores if the question asked was 'truth' or 'dare' to determine the json response for when the button is clicked

        :type ctx: commands.Context
        :type rating: Optional[str]
        :type truthordare: str

        :return: None
        :rtype: None
        """
        if rating and rating.upper() not in ['PG', 'PG13', 'R']:
            await send_error_embed(ctx,
                                   description='Please enter a valid rating! Valid ratings are `PG`, `PG13`, and `R`')
            return

        truthordare = random.choice(['truth', 'dare']) if truthordare is None else truthordare

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/{truthordare}?rating={rating}').json() if rating else requests.get(
            f'https://api.truthordarebot.xyz/v1/{truthordare}').json()  # type: dict

        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Truth or Dare', icon_url=self.bot.user.avatar)

        next_question = Button(label=f'Next {truthordare}', style=discord.ButtonStyle.green)

        view = View(timeout=None)
        view.add_item(next_question)

        async def next_trigger(interaction):
            next_question.disabled = True
            await interaction.response.edit_message(view=view)
            view.stop()
            
            await self.truthordare(ctx, rating, truthordare) if rating else await self.truthordare(ctx,
                                                                                                   truthordare=truthordare)

        await ctx.send(embed=embed, view=view)
        next_question.callback = next_trigger

    @truthordare.error
    async def truthordare_error(self, ctx, error):
        """
        Truth or dare error handler

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await send_error_embed(ctx,
                                   description=f'You are on cooldown! Please wait {round(error.retry_after, 2)} seconds')
        # OMG! You have found the egg! Here's your prize! https://imgur.com/pSB4AnR

    @commands.command(name='wouldyourather', aliases=['wyr'], description='Get a would you rather',
                      usage='wouldyourather <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def wouldyourather(self, ctx, rating: str = None):
        """
        Would you rather command
        
        :param ctx: The context of where the message was sent
        :param rating: The rating of the question

        :type ctx: commands.Context
        :type rating: Optional[str]
        
        :return: None
        :rtype: None
        """
        if rating and rating.upper() not in ['PG', 'PG13', 'R']:
            await send_error_embed(ctx,
                                   description='Please enter a valid rating! Valid ratings are `PG`, `PG13`, and `R`')
            return

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/wyr?rating={rating}').json() if rating else requests.get(
            f'https://api.truthordarebot.xyz/v1/wyr').json()  # type: dict

        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Would You Rather', icon_url=self.bot.user.avatar)

        next_wyr = Button(label='Next would you rather', style=discord.ButtonStyle.green)

        view = View(timeout=None)
        view.add_item(next_wyr)

        async def next_trigger(interaction):
            next_wyr.disabled = True
            await interaction.response.edit_message(view=view)
            view.stop()
            
            await self.wouldyourather(ctx, rating) if rating else await self.wouldyourather(ctx)

        await ctx.send(embed=embed, view=view)
        next_wyr.callback = next_trigger

    @wouldyourather.error
    async def wouldyourather_error(self, ctx, error):
        """
        Would you rather error handler
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await send_error_embed(ctx,
                                   description=f'You are on cooldown! Please wait {round(error.retry_after, 2)} seconds')

    @commands.command(name='neverhaveiever', aliases=['nhie'], description='Get a never have I ever',
                      usage='neverhaveiever <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def neverhaveiever(self, ctx, rating: str = None):
        """
        Never have I ever command

        :param ctx: The context of where the message was sent
        :param rating: The rating of the question

        :type ctx: commands.Context
        :type rating: Optional[str]

        :return: None
        :rtype: None
        """
        if rating and rating.upper() not in ['PG', 'PG13', 'R']:
            await send_error_embed(ctx,
                                   description='Please enter a valid rating! Valid ratings are `PG`, `PG13`, and `R`')
            return

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/nhie?rating={rating}').json() if rating else requests.get(
            f'https://api.truthordarebot.xyz/v1/nhie').json()  # type: dict

        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Never Have I Ever', icon_url=self.bot.user.avatar)

        next_nhie = Button(label='Next never have I ever', style=discord.ButtonStyle.green)

        view = View(timeout=None)
        view.add_item(next_nhie)

        async def next_trigger(interaction):
            next_nhie.disabled = True
            await interaction.response.edit_message(view=view)
            view.stop()
            
            await self.neverhaveiever(ctx, rating) if rating else await self.neverhaveiever(ctx)

        await ctx.send(embed=embed, view=view)
        next_nhie.callback = next_trigger

    @neverhaveiever.error
    async def neverhaveiever_error(self, ctx, error):
        """
        Never have I ever error handler

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await send_error_embed(ctx,
                                   description=f'You are on cooldown! Please wait {round(error.retry_after, 2)} seconds')

    @commands.command(name='paranoia', description='Get a paranoia question', usage='paranoia <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def paranoia(self, ctx, rating: str = None):
        """
        Paranoia command
        
        :param ctx: The context of where the message was sent
        :param rating: The rating of the question

        :type ctx: commands.Context
        :type rating: Optional[str]
        
        :return: None
        :rtype: None
        """
        if rating and rating.upper() not in ['PG', 'PG13', 'R']:
            await send_error_embed(ctx,
                                   description='Please enter a valid rating! Valid ratings are `PG`, `PG13`, and `R`')
            return

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/paranoia?rating={rating}').json() if rating else requests.get(
            f'https://api.truthordarebot.xyz/v1/paranoia').json()
        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Paranoia', icon_url=self.bot.user.avatar)

        next_paranoia = Button(label='Next paranoia', style=discord.ButtonStyle.green)

        view = View(timeout=None)
        view.add_item(next_paranoia)

        async def next_trigger(interaction):
            next_paranoia.disabled = True
            await interaction.response.edit_message(view=view)
            view.stop()
            
            await self.paranoia(ctx, rating) if rating else await self.paranoia(ctx)

        await ctx.send(embed=embed, view=view)
        next_paranoia.callback = next_trigger

    @paranoia.error
    async def paranoia_error(self, ctx, error):
        """
        Error handler for paranoia command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await send_error_embed(ctx,
                                   description=f'You are on cooldown! Please wait {round(error.retry_after, 2)} seconds')

    @commands.command(name='guessthenumber', aliases=['gtn'], description='Guess the number',
                      usage='guessthenumber <limit>')
    async def guessthenumber(self, ctx, limit: int = 100):
        """
        Guess the number command
        
        :param ctx: The context of where the message was sent
        :param limit: The limit of the number
        
        :return: None
        :rtype: None
        """
        await ctx.send(
            f'Hey **{ctx.author.name}**, I\'m thinking of a number between 0 and {limit}.\n\n'

            '**Rules:**\n\n'

            f'- You have 60 seconds to guess a number between the range 0 - {limit}!\n'
            '- If you wish to cancel the game, then enter cancel which will stop the game.\n'
            '- Have Fun!!!\n'
        )

        number = random.randint(0, limit)
        start_time = time.time()
        end_time = start_time + 60

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        while True:
            try:
                guess = await self.bot.wait_for('message', check=check, timeout=60)  # type: discord.Message
            except asyncio.TimeoutError:
                await ctx.send('You took too long to guess the number!')
                break
            else:
                if guess.content.lower() == 'cancel':
                    await ctx.send('Game cancelled!')
                    break

                if not guess.content.isdigit():
                    continue

                if int(guess.content) == number:
                    await ctx.send(f'You guessed the number **{guess.content}**!')
                    break
                elif int(guess.content) < number:
                    await ctx.send(f'Your guess **{guess.content}** is too low!')
                elif int(guess.content) > number:
                    await ctx.send(f'Your guess **{guess.content}** is too high!')
                else:
                    await ctx.send(f'Your guess **{guess.content}** is invalid!')

                if time.time() > end_time:
                    await ctx.send('You took too long to guess the number!')
                    break

    @guessthenumber.error
    async def guessthenumber_error(self, ctx, error):
        """
        Error handler for guess the number command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await send_error_embed(ctx, description=f'Error: `{error}`')

    @commands.command(name='tictactoe', aliases=['ttt'], description='Play Tic Tac Toe', usage='ttt <player>')
    async def tictactoe(self, ctx, player: discord.Member):
        """
        Tic Tac Toe command
        
        :param ctx: The context of where the message was sent
        :param player: The member to play against

        :type ctx: commands.Context
        :type player: discord.Member
        
        :return: None
        :rtype: None
        """
        if player == ctx.author:
            await send_error_embed(ctx, description='You cannot play against yourself!')
            return

        if player.bot:
            await send_error_embed(ctx, description='You cannot play against a bot!')
            return

        turn = random.choice([ctx.author, player])  # type: discord.Member
        await ctx.send(f'It is {turn.mention}\'s turn!', view=view.TicTacToeView(ctx=ctx, initiator=ctx.author, other_player=player, turn=turn, bot=self.bot, timeout=None))

    @tictactoe.error
    async def tictactoe_error(self, ctx, error):
        """
        Error handler for the tictactoe command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await send_error_embed(ctx, description=f'Error: `{error}`')


def setup(bot):
    bot.add_cog(Games(bot))

# Copyright (c) 2022 Sandeep Kanekal
# Contains all game commands
import discord
import random
import requests
import time
import asyncio
import view
from discord.ext import commands
from tools import send_error_embed, inform_owner


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
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
    async def eight_ball(self, ctx: commands.Context, *, question: str):
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
    async def eight_ball_error(self, ctx: commands.Context, error: commands.CommandError):
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
        await send_error_embed(ctx,
                               description='An error occurred while running the 8ball command! The owner has been notified.')
        await inform_owner(self.bot, error)

    @commands.command(aliases=['roll'], description='Rolls a dice', usage='dice')
    @commands.guild_only()
    async def dice(self, ctx: commands.Context):
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
        await msg.edit(f'**You rolled a {random.randint(1, 6)}! :game_die:**',
                       view=view.RollView(ctx=ctx, message_id=msg.id, timeout=None))

    # Coinflip command
    @commands.command(aliases=['cf'], description='Heads or Tails?', usage='coinflip')
    @commands.guild_only()
    async def coinflip(self, ctx: commands.Context):
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
        await msg.edit(f'**You flipped a {random.choice(["Heads", "Tails"])}! :coin:**',
                       view=view.FlipView(ctx=ctx, message_id=msg.id, timeout=None))

    @commands.command(name='truth', description='Get a truth question', usage='truth <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def truth(self, ctx: commands.Context, rating: str = None):
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

        # Limit R rating to NSFW channels only
        if rating and rating.upper() == 'R' and not ctx.channel.is_nsfw():
            await send_error_embed(ctx, description='You cannot use the `R` rating outside NSFW channels.')
            return

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/truth?rating={rating}').json() if rating else requests.get(
            'https://api.truthordarebot.xyz/v1/truth').json()

        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Truth', icon_url=self.bot.user.avatar)

        await ctx.send(embed=embed, view=view.TruthOrDareView(ctx=ctx, timeout=None))

    @truth.error
    async def truth_error(self, ctx: commands.Context, error: commands.CommandError):
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
        else:
            await send_error_embed(ctx,
                                   description='An error occurred while running the truth command! The owner has been notified.')
            await inform_owner(self.bot, error)

    @commands.command(name='dare', description='Get a dare', usage='dare <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def dare(self, ctx: commands.Context, rating: str = None):
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

        # Limit R rating to NSFW channels only
        if rating and rating.upper() == 'R' and not ctx.channel.is_nsfw():
            await send_error_embed(ctx, description='You cannot use the `R` rating outside NSFW channels.')
            return

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/dare?rating={rating}').json() if rating else requests.get(
            'https://api.truthordarebot.xyz/v1/dare').json()

        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Dare', icon_url=self.bot.user.avatar)
        await ctx.send(embed=embed, view=view.TruthOrDareView(ctx=ctx, timeout=None))

    @dare.error
    async def dare_error(self, ctx: commands.Context, error: commands.CommandError):
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
        else:
            await send_error_embed(ctx,
                                   description='An error occurred while running the dare command! The owner has been notified.')
            await inform_owner(self.bot, error)

    @commands.command(name='truthordare', aliases=['tord'], description='Get a truth or dare',
                      usage='truthordare <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def truthordare(self, ctx: commands.Context, rating: str = None, truthordare: str = None):
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

        # Limit R rating to NSFW channels only
        if rating and rating.upper() == 'R' and not ctx.channel.is_nsfw():
            await send_error_embed(ctx, description='You cannot use the `R` rating outside NSFW channels.')
            return

        truthordare = random.choice(['truth', 'dare']) if truthordare is None else truthordare

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/{truthordare}?rating={rating}').json() if rating else requests.get(
            f'https://api.truthordarebot.xyz/v1/{truthordare}').json()  # type: dict

        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Truth or Dare', icon_url=self.bot.user.avatar)
        await ctx.send(embed=embed, view=view.TruthOrDareView(ctx=ctx, timeout=None))

    @truthordare.error
    async def truthordare_error(self, ctx: commands.Context, error: commands.CommandError):
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
        else:
            await send_error_embed(ctx,
                                   description='An error occurred while running the truthordare command! The owner has been notified.')
            await inform_owner(self.bot, error)
        # OMG! You have found the egg! Here's your prize! https://imgur.com/pSB4AnR

    @commands.command(name='wouldyourather', aliases=['wyr'], description='Get a would you rather',
                      usage='wouldyourather <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def wouldyourather(self, ctx: commands.Context, rating: str = None):
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

        # Limit R rating to NSFW channels only
        if rating and rating.upper() == 'R' and not ctx.channel.is_nsfw():
            await send_error_embed(ctx, description='You cannot use the `R` rating outside NSFW channels.')
            return

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/wyr?rating={rating}').json() if rating else requests.get(
            'https://api.truthordarebot.xyz/v1/wyr').json()

        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Would You Rather', icon_url=self.bot.user.avatar)
        await ctx.send(embed=embed, view=view.TruthOrDareView(ctx=ctx, timeout=None))

    @wouldyourather.error
    async def wouldyourather_error(self, ctx: commands.Context, error: commands.CommandError):
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
        else:
            await send_error_embed(ctx,
                                   description='An error occurred while running the wouldyourather command! The owner has been notified.')
            await inform_owner(self.bot, error)

    @commands.command(name='neverhaveiever', aliases=['nhie'], description='Get a never have I ever',
                      usage='neverhaveiever <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def neverhaveiever(self, ctx: commands.Context, rating: str = None):
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

        # Limit R rating to NSFW channels only
        if rating and rating.upper() == 'R' and not ctx.channel.is_nsfw():
            await send_error_embed(ctx, description='You cannot use the `R` rating outside NSFW channels.')
            return

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/nhie?rating={rating}').json() if rating else requests.get(
            'https://api.truthordarebot.xyz/v1/nhie').json()

        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Never Have I Ever', icon_url=self.bot.user.avatar)
        await ctx.send(embed=embed, view=view.TruthOrDareView(ctx=ctx, timeout=None))

    @neverhaveiever.error
    async def neverhaveiever_error(self, ctx: commands.Context, error: commands.CommandError):
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
        else:
            await send_error_embed(ctx,
                                   description='An error occurred while running the neverhaveiever command! The owner has been notified.')
            await inform_owner(self.bot, error)

    @commands.command(name='paranoia', description='Get a paranoia question', usage='paranoia <rating>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def paranoia(self, ctx: commands.Context, rating: str = None):
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

        # Limit R rating to NSFW channels only
        if rating and rating.upper() == 'R' and not ctx.channel.is_nsfw():
            await send_error_embed(ctx, description='You cannot use the `R` rating outside NSFW channels.')
            return

        data = requests.get(
            f'https://api.truthordarebot.xyz/v1/paranoia?rating={rating}').json() if rating else requests.get(
            'https://api.truthordarebot.xyz/v1/paranoia').json()

        embed = discord.Embed(title=f'{data["question"]}', colour=discord.Colour.random())
        embed.set_footer(text=f'Type: {data["type"]} | Rating: {data["rating"].upper()} | ID: {data["id"]}')
        embed.set_author(name='Paranoia', icon_url=self.bot.user.avatar)
        await ctx.send(embed=embed, view=view.TruthOrDareView(ctx=ctx, timeout=None))

    @paranoia.error
    async def paranoia_error(self, ctx: commands.Context, error: commands.CommandError):
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
        else:
            await send_error_embed(ctx,
                                   description='An error occurred while running the paranoia command! The owner has been notified.')
            await inform_owner(self.bot, error)

    @commands.command(name='guessthenumber', aliases=['gtn'], description='Guess the number',
                      usage='guessthenumber <limit>')
    async def guessthenumber(self, ctx: commands.Context, limit: int = 100):
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
            return m.author.id == ctx.author.id and m.channel == ctx.channel

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

                # Inform the user of how near their guess is
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
    async def guessthenumber_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for guess the number command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await send_error_embed(ctx,
                               description='An error occurred while running the guessthenumber command! The owner has been notified.')
        await inform_owner(self.bot, error)

    @commands.command(name='tictactoe', aliases=['ttt'], description='Play Tic Tac Toe', usage='ttt <player>')
    async def tictactoe(self, ctx: commands.Context, player: discord.Member):
        """
        Tic Tac Toe command
        
        :param ctx: The context of where the message was sent
        :param player: The member to play against

        :type ctx: commands.Context
        :type player: discord.Member
        
        :return: None
        :rtype: None
        """
        if player.id == ctx.author.id:
            await send_error_embed(ctx, description='You cannot play against yourself!')
            return

        if player.bot:
            await send_error_embed(ctx, description='You cannot play against a bot!')
            return

        turn = random.choice([ctx.author, player])  # choose a random player to play first
        await ctx.send(f'It is {turn.mention}\'s turn!',
                       view=view.TicTacToeView(ctx=ctx, initiator=ctx.author, other_player=player, turn=turn,
                                               bot=self.bot, timeout=None))

    @tictactoe.error
    async def tictactoe_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the tictactoe command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await send_error_embed(ctx,
                               description='An error occurred while running the tictactoe command! The owner has been notified.')
        await inform_owner(self.bot, error)


def setup(bot: commands.Bot):
    bot.add_cog(Games(bot))

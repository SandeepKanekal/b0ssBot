import random
import discord
import datetime
import requests
import os
import view
from discord.ext import commands
from tools import send_error_embed, get_random_post
from discord.ui import Button, View
from PIL import Image, ImageChops


class Fun(commands.Cog):
    def __init__(self, bot):
        """
        Initialize the cog

        :param bot: The bot
        :type bot: commands.Bot

        :return: None
        :rtype: None
        """
        self.bot = bot

    # Meme command
    @commands.command(aliases=['m'],
                      description='Posts memes from the most famous meme subreddits\nSubreddit can be mentioned\nValid subreddits include: `dankmemes` `memes` `meme` `me_irl` `wholesomememes`',
                      usage='meme <subreddit>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def meme(self, ctx, subreddit: str = None):  # sourcery no-metrics
        """
        Posts memes from the most famous meme subreddits
        Subreddit can be mentioned
        Valid subreddits include: `dankmemes` `memes` `meme` `me_irl` `wholesomememes`

        :param ctx: The context of where the message was sent
        :param subreddit: The subreddit to get a meme from (defaults to a random choice among ['dankmemes', 'memes', 'meme'])

        :type ctx: commands.Context
        :type subreddit: str

        :return: None
        :rtype: None
        """
        if not subreddit: 
            subreddit = random.choice(['dankmemes', 'memes', 'meme'])
        elif subreddit.lower() in ['dankmemes', 'memes', 'meme', 'me_irl', 'wholesomememes']:
            subreddit = subreddit.lower()
        else:
            await send_error_embed(ctx, 'Invalid subreddit')
            return

        await ctx.invoke(self.bot.get_command('redditpost'), subreddit=subreddit)

    @meme.error
    async def meme_error(self, ctx, error):
        """
        Error handler for the meme command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Dankvideo command
    @commands.command(aliases=['dv', 'dankvid'], description='Posts dank videos from the dankest subreddits', usage='dankvideo')
    async def dankvideo(self, ctx):
        """
        Posts a random dank video from the dankest subreddits
        
        :param ctx: command context
        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
        async with ctx.typing():
            submission = await get_random_post(random.choice(['dankvideos', 'cursed_videomemes', 'MemeVideos']))  # Gets a random post from the dankest subreddits

            if submission.over_18 and not ctx.channel.is_nsfw():
                await self.dankvideo.reinvoke(ctx)
                return

        await ctx.send(f'https://reddit.com{submission.permalink}')

    @dankvideo.error
    async def dankvideo_error(self, ctx, error):
        """
        Error handler for the dankvideo command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await send_error_embed(ctx, description=f'Error: `{error}`')
    
    @commands.command(name='invert', description='Invert your or another user\'s avatar', usage='invert <member>')
    async def invert(self, ctx, member: discord.Member = None):
        """
        Inverts the avatar of the user or another user
        
        :param ctx: command context
        :param member: the member to invert the avatar of
        :type ctx: commands.Context
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        async with ctx.typing():
            member = member or ctx.author

            response = requests.get(str(member.display_avatar))

            with open(f'avatar_{member.id}.png', 'wb') as f:
                f.write(response.content)

            image = Image.open(f'avatar_{member.id}.png')
            invert = ImageChops.invert(image.convert('RGB'))
            invert.save(f'{member.id}_inverted.png')
        
        await ctx.send(file=discord.File(f'{member.id}_inverted.png', 'invert.png'))

        os.remove(f'avatar_{member.id}.png')
        os.remove(f'{member.id}_inverted.png')

    @invert.error
    async def invert_error(self, ctx, error):
        """
        Error handler for the invert command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.BadArgument):
            await send_error_embed(ctx, description='Please provide a valid member.')
        else:
            await send_error_embed(ctx, description=f'Error: `{error}`')
    
    @commands.command(name='dadjoke', description='Posts a dad joke', usage='dadjoke')
    async def dadjoke(self, ctx):
        """
        Posts a dad joke
        
        :param ctx: command context
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        async with ctx.typing():
            embed = discord.Embed(description=requests.get('https://icanhazdadjoke.com/', headers={'Accept': 'application/json'}).json()['joke'], colour=discord.Colour.random(), timestamp=datetime.datetime.now())

        await ctx.send(embed=embed, view=view.FunView(ctx=ctx, url='https://icanhazdadjoke.com/', embed=embed, timeout=None))
    
    @commands.command(name='bored', description='Get a random task to do for fun!', usage='bored')
    async def bored(self, ctx):
        """
        Get a random task to do for fun!

        :param ctx: command context
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """ 
        async with ctx.typing():
            response = requests.get('https://www.boredapi.com/api/activity/', verify=False).json()

            embed = discord.Embed(description=f'{response["activity"]}.', timestamp=datetime.datetime.now(), colour=discord.Colour.random()).set_footer(text=f'Type: {response["type"].upper()}')

        await ctx.send(embed=embed, view=view.FunView(ctx=ctx, url='https://www.boredapi.com/api/activity/', embed=embed, timeout=None))
    
    @commands.command(name='egg', description='Gives information about the egghunt', usage='egg')
    async def egg(self, ctx):
        """
        Gives information about the egghunt

        :param ctx: The context of the command

        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
        await ctx.reply(f'Hey there {ctx.author.mention}! The egg is hidden somewhere in the code of the bot. The egg is not visible in the frontend User Interface. Use the /code command to check the code of each and every module, where you can find the egg!')
    
    @commands.command(name='dog', description='Get a random dog picture', usage='dog')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def dog(self, ctx):
        """
        Get a random dog picture
        
        :param ctx: command

        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
        async with ctx.typing():
            response = requests.get('https://dog.ceo/api/breeds/image/random').json()
            embed = discord.Embed(title=':dog: woof!', url=response['message'], colour=discord.Colour.blurple()).set_image(url=response['message'])
            
        await ctx.send(embed=embed, view=view.FunView(ctx=ctx, url='https://dog.ceo/api/breeds/image/random', embed=embed, timeout=None))
    
    @commands.command(name='cat', description='Get a random cat picture', usage='cat')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def cat(self, ctx):
        """
        Get a random cat picture
        
        :param ctx: command

        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
        async with ctx.typing():
            response = requests.get('https://api.thecatapi.com/v1/images/search').json()
            embed = discord.Embed(title=':cat: meow!', url=response[0]['url'], colour=discord.Colour.blurple()).set_image(url=response[0]['url'])
            
        await ctx.send(embed=embed, view=view.FunView(ctx=ctx, url='https://api.thecatapi.com/v1/images/search', embed=embed, timeout=None))
    
    @commands.command(name='egg', description='Gives information about the egghunt', usage='egg')
    async def egg(self, ctx):
        """
        Gives information about the egghunt

        :param ctx: The context of the command

        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
        await ctx.reply(f'Hey there {ctx.author.mention}! The egg is hidden somewhere in the code of the bot. The egg is not visible in the frontend User Interface. Use the /code command to check the code of each and every module, where you can find the egg!')


def setup(bot):
    """
    Function to load cog

    :param bot: The bot object
    :type bot: discord.ext.commands.Bot
    
    :return: None
    :rtype: None
    """
    bot.add_cog(Fun(bot))

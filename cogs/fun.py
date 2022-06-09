import random
import discord
import datetime
import requests
import os
from discord.ext import commands
from tools import send_error_embed, get_posts, get_random_post
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
        index = 0  # type: int

        if subreddit is None:
            subreddit = random.choice(['memes', 'dankmemes', 'meme'])
        elif subreddit.lower() in ['dankmemes', 'memes', 'meme', 'me_irl', 'wholesomememes']:
            subreddit = subreddit.lower()
        else:
            await send_error_embed(ctx, description='Invalid subreddit')
            return

        submissions = await get_posts(subreddit)
        submissions.pop(0)  # Pops the pinned post
        if not ctx.channel.is_nsfw():  # Filters out nsfw posts if the channel is not marked NSFW
            submissions = list(filter(lambda s: not s.over_18, submissions))

        next_meme = Button(style=discord.ButtonStyle.green, emoji='⏭️')  # The button for going to the next meme
        end_interaction = Button(label='End Interaction',
                                 style=discord.ButtonStyle.red)  # The button the end the interaction
        previous_meme = Button(emoji='⏮️', style=discord.ButtonStyle.green)  # The button for going to the previous meme

        view = View(timeout=None)
        view.add_item(previous_meme)
        view.add_item(next_meme)
        view.add_item(end_interaction)
        embed = discord.Embed(title=submissions[0].title, url=f'https://reddit.com{submissions[0].permalink}',
                              colour=discord.Colour.random())

        if submissions[0].is_video:
            embed.set_image(url=submissions[0].thumbnail)
            embed.description = f'[Video link]({submissions[0].url})'
        else:
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

            # Edit the embed
            embed.title = submissions[index].title
            embed.url = f'https://reddit.com{submissions[index].permalink}'

            if submissions[index].is_video:
                embed.set_image(url=submissions[index].thumbnail)
                embed.description = f'[Video link]({submissions[index].url})'
            else:
                embed.set_image(url=submissions[index].url)
                embed.description = ''

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

            # Edit the embed
            index -= 1
            embed.title = submissions[index].title
            embed.url = f'https://reddit.com{submissions[index].permalink}'

            if submissions[index].is_video:
                embed.set_image(url=submissions[index].thumbnail)
                embed.description = f'[Video link]({submissions[index].url})'
            else:
                embed.set_image(url=submissions[index].url)
                embed.description = ''

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

            next_meme.disabled = True
            previous_meme.disabled = True
            end_interaction.disabled = True
            await interaction.response.edit_message(view=view)

        # Callbacks
        next_meme.callback = next_meme_trigger
        end_interaction.callback = end_interaction_trigger
        previous_meme.callback = previous_meme_trigger

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
        
        next_joke = Button(emoji='➡️', style=discord.ButtonStyle.green)
        end_interaction = Button(emoji='❌', style=discord.ButtonStyle.gray)

        view = View(timeout=None)
        view.add_item(next_joke)
        view.add_item(end_interaction)

        await ctx.send(embed=embed, view=view)

        async def next_joke_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            # Callback to button1 triggers this function
            embed.description = requests.get('https://icanhazdadjoke.com/', headers={'Accept': 'application/json'}).json()['joke']
            embed.timestamp = datetime.datetime.now()
            await interaction.response.edit_message(embed=embed)
        
        async def end_interaction_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content=f'This interaction is for {ctx.author.mention}',
                                                        ephemeral=True)
                return

            next_joke.disabled = True
            end_interaction.disabled = True
            await interaction.response.edit_message(view=view)

        next_joke.callback = next_joke_trigger
        end_interaction.callback = end_interaction_trigger


def setup(bot):
    """
    Function to load cog

    :param bot: The bot object
    :type bot: discord.ext.commands.Bot
    
    :return: None
    :rtype: None
    """
    bot.add_cog(Fun(bot))

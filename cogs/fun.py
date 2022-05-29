import random
import discord
import datetime
from discord.ext import commands
from tools import send_error_embed, get_posts, get_random_post
from discord.ui import Button, View


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Meme command
    @commands.command(aliases=['m'],
                      description='Posts memes from the most famous meme subreddits\nSubreddit can be mentioned\nValid subreddits include: `dankmemes` `memes` `meme` `me_irl` `wholesomememes`',
                      usage='meme <subreddit>')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def meme(self, ctx, subreddit: str = None):  # sourcery no-metrics
        index = 0

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

        view = View()
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
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Dankvideo command
    @commands.command(aliases=['dv', 'dankvid'], description='Posts dank videos from r/dankvideos', usage='dankvideo')
    async def dankvideo(self, ctx):
        submission = await get_random_post(random.choice(['dankvideos', 'cursed_videomemes', 'MemeVideos']))

        if submission.over_18 and not ctx.channel.is_nsfw():
            await send_error_embed(ctx, description='This post is NSFW. Please use this command in an NSFW channel.')
            return

        await ctx.send(f'https://reddit.com{submission.permalink}')

    @dankvideo.error
    async def dankvideo_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')


def setup(bot):
    bot.add_cog(Fun(bot))

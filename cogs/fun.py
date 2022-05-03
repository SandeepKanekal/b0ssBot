import random
import discord
import datetime
from discord.ext import commands
from tools import send_error_embed, get_post, get_random_post
from discord.ui import Button, View


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 8ball for fun
    @commands.command(name='8ball', aliases=['8b'], description='Ask a question, and get a reply!', usage='8ball <question>')
    async def eight_ball(self, ctx, *, question: str):

        if question.lower().startswith('what') or question.lower().startswith('how') or question.lower().startswith(
                'why') or question.lower().startswith('who'):
            await send_error_embed(ctx, description='Please ask a question that can be answered with `yes` or `no`')
            return

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
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please ask a question!\n\nProper Usage: `{self.bot.get_command("8ball").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    @commands.command(aliases=['roll'], description='Rolls a dice', usage='dice')
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
            
            roll.disabled = True
            end_interaction.disabled = True
            await interaction.response.edit_message(view=view)

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
    @commands.command(aliases=['m'],
                      description='Posts memes from the most famous meme subreddits\nSubreddit can be mentioned\nValid subreddits include: `dankmemes` `memes` `meme` `me_irl` `wholesomememes`',
                      usage='meme <subreddit>')
    async def meme(self, ctx, subreddit: str = None):
        index = 0

        if subreddit is None:
            subreddit = random.choice(['memes', 'dankmemes', 'meme'])
        elif subreddit.lower() in ['dankmemes', 'memes', 'meme', 'me_irl', 'wholesomememes']:
            subreddit = subreddit.lower()
        else:
            await send_error_embed(ctx, description='Invalid subreddit')
            return

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
        submission = await get_random_post(random.choice(['dankvideos', 'cursed_videomemes']))

        if submission.over_18 and not ctx.channel.is_nsfw():
            await send_error_embed(ctx, description='This post is NSFW. Please use this command in an NSFW channel.')
            return

        await ctx.send(f'https://reddit.com{submission.permalink}')

    @dankvideo.error
    async def dankvideo_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Coinflip command
    @commands.command(aliases=['cf'], description='Heads or Tails?', usage='coinflip')
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

            flip.disabled = True
            end_interaction.disabled = True
            await interaction.response.edit_message(view=view)

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


def setup(bot):
    bot.add_cog(Fun(bot))

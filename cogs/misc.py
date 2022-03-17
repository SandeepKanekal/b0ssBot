# All misc commands stored here
import datetime
import json
import urllib.request
import discord
import pafy
import requests
import re
import os
import wikipedia
from discord.ext import commands
from discord.ui import Button, View


# Gets quote from https://zenquotes.io api
def get_quote():
    response = requests.get('https://zenquotes.io/api/random')
    return json.loads(response.text)


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description):
    # Response embed
    embed = discord.Embed(description=description, colour=discord.Colour.red())
    await ctx.send(embed=embed)


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Quote command
    @commands.command(aliases=['qu'], description='Replies with an inspirational quote')
    async def quote(self, ctx):
        quote = get_quote()
        embed = discord.Embed(colour=discord.Colour.orange())
        embed.add_field(name=quote[0]['q'], value=quote[0]['a'], inline=True)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=str(ctx.author.avatar))
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    # Spam command
    @commands.command(aliases=['s'], description='Spams text or users')
    async def spam(self, ctx, *, message):
        for _ in range(5):
            await ctx.send(message)

    @spam.error
    async def spam_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Av command
    @commands.command(aliases=['av', 'pfp'], description='Shows the specified user\'s avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        if member is not None:  # A member is mentioned
            # Getting the urls
            url = str(member.avatar)
        else:
            member = ctx.message.author  # Member is the author of the message sent
            # Getting the urls
            url = member.avatar
        png_url = str(url).replace('webp', 'png')
        jpg_url = str(url).replace('webp', 'jpg')
        # Response embed
        embed = discord.Embed(colour=member.colour)
        embed.set_author(name=str(member), icon_url=url)
        embed.set_image(url=url)
        embed.add_field(name='Download this image', value=f'[webp]({url}) | [png]({png_url}) | [jpg]({jpg_url})')
        await ctx.reply(embed=embed)

    # Servericon command
    @commands.command(aliases=['serverpfp', 'serverav', 'serveravatar'], description='Shows the server\'s icon')
    async def servericon(self, ctx):
        # Getting the urls
        url = str(ctx.guild.icon)
        png_url = str(url).replace('webp', 'png')
        jpg_url = str(url).replace('webp', 'jpg')
        # Response embed
        embed = discord.Embed(colour=discord.Colour.random())
        embed.set_author(name=ctx.guild.name, icon_url=url)
        embed.set_image(url=url)
        embed.add_field(name='Download this image', value=f'[webp]({url}) | [png]({png_url}) | [jpg]({jpg_url})')
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=str(ctx.author.avatar))
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    # Megaspam command
    @commands.command(aliases=['ms'], description='Spams a message 25 times')
    async def megaspam(self, ctx, *, message):
        await ctx.message.delete()
        for _ in range(25):
            await ctx.send(message)

    @megaspam.error
    async def megaspam_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Search command
    @commands.command(aliases=['yt', 'youtube', 'ytsearch'],
                      description='Searches YouTube and responds with the top result')
    async def search(self, ctx, *, query):
        original_query = query
        query = query.replace(' ', '+')  # Replacing white spaces with +
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + query)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        try:
            video = pafy.new("https://www.youtube.com/watch?v=" + video_ids[0])  # Getting video details
        except OSError as e:
            embed = discord.Embed(description=f'Could not get video. {e}', colour=discord.Colour.red())
            await ctx.send(embed=embed)
            return

        # Gets the next video
        async def next_video_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return

            embed.clear_fields()
            try:
                video_ids.pop(0)
            except IndexError:
                emb = discord.Embed(description='No more videos available', colour=discord.Colour.red())
                await interaction.response.edit_message(embed=emb)

            vid = pafy.new(f'https://www.youtube.com/watch?v={video_ids[0]}')
            embed.add_field(name='Search Query:',
                            value=f'[{original_query.upper()}](https://www.youtube.com/results?search_query={query})')
            embed.add_field(name='Result:', value=f'[{vid.title}](https://www.youtube.com/watch?v={video_ids[0]})')
            if vid.author == vid.username:
                embed.add_field(name='Video Author:', value=f'[{vid.author}](https://youtube.com/c/{vid.author})')
            else:
                embed.add_field(name='Video Author:',
                                value=f'[{vid.author}](https://youtube.com/channel/{vid.username})')
            embed.set_image(url=vid.bigthumbhd)
            embed.set_footer(text=f'Duration: {vid.duration}, 🎥: {vid.viewcount}, 👍: {vid.likes}')
            watch_video.url = f'https://www.youtube.com/watch?v={video_ids[0]}'
            view.remove_item(watch_video)
            view.add_item(watch_video)
            await interaction.response.edit_message(embed=embed, view=view)

        # Ends the interaction
        async def end_interaction_trigger(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f'This interaction is for {ctx.author.mention}', ephemeral=True)
                return
            view.remove_item(next_video)
            view.remove_item(end_interaction)
            await interaction.response.edit_message(view=view)

        # Response embed
        embed = discord.Embed(colour=discord.Colour.red())
        embed.add_field(name='Search Query:',
                        value=f'[{original_query.upper()}](https://www.youtube.com/results?search_query={query})')
        embed.add_field(name=f'Result:', value=f'[{video.title}](https://www.youtube.com/watch?v={video_ids[0]})')
        if video.author == video.username:
            embed.add_field(name='Video Author:', value=f'[{video.author}](https://youtube.com/c/{video.author})')
        else:
            embed.add_field(name='Video Author:',
                            value=f'[{video.author}](https://youtube.com/channel/{video.username})')
        embed.set_image(url=video.bigthumbhd)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(text=f'Duration: {video.duration}, 🎥: {video.viewcount}, 👍: {video.likes}')
        next_video = Button(label='Next Video ⏭️', style=discord.ButtonStyle.green)
        end_interaction = Button(label='End Interaction', style=discord.ButtonStyle.red)
        watch_video = Button(label='Watch Video', url=f'https://www.youtube.com/watch?v={video_ids[0]}')
        view = View()
        view.add_item(next_video)
        view.add_item(end_interaction)
        view.add_item(watch_video)
        await ctx.send(embed=embed, view=view)
        next_video.callback = next_video_trigger
        end_interaction.callback = end_interaction_trigger

    @search.error
    async def search_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Code command
    @commands.command(name='code', description='Shows the code of the module')
    async def code(self, ctx, module):
        module = module.lower()
        try:
            with open(f'cogs/{module}.py') as code_file:  # Open module
                code = code_file.read()
                with open(f'Code for {module}.txt', 'w+') as text_file:  # Write the file to be sent
                    text_file.write(code)

            await ctx.send(file=discord.File(f'Code for {module}.txt'))
            os.remove(f'Code for {module}.txt')  # Remove file to avoid problems in version control

        except FileNotFoundError:
            await send_error_embed(ctx, description=f'Module {module} not found')

    @code.error
    async def code_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Wikipedia command
    @commands.command(aliases=['wiki'], description='Gets a summary of the query from wikipedia')
    async def wikipedia(self, ctx, *, query):
        # Gets the data from wikipedia
        try:
            summary = wikipedia.summary(query, sentences=5)
            thumbnail = wikipedia.page(query).images[0]
            url = wikipedia.page(query).url
            # Response embed
            summary += f'[ Read More...]({url})'
            embed = discord.Embed(title=wikipedia.page(query).title, url=url, description=summary,
                                  colour=discord.Colour.random())
            embed.set_thumbnail(url=thumbnail)
            await ctx.send(embed=embed)

        except wikipedia.exceptions.WikipediaException as e:
            await send_error_embed(ctx, description=e)

    @wikipedia.error
    async def wikipedia_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')


# Setup
def setup(bot):
    bot.add_cog(Misc(bot))

# All misc commands stored here
import datetime
import json
import urllib.request
import discord
import pafy
import requests
import re
import os
from discord.ext import commands
from discord.ui import Button, View

today = datetime.date.today()


# Gets quote from https://zenquotes.io api
def get_quote():
    response = requests.get('https://zenquotes.io/api/random')
    json_data = json.loads(response.text)
    return json_data


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
        await ctx.send(embed=embed)

    # Spam command
    @commands.command(aliases=['s'], description='Spams text or users')
    async def spam(self, ctx, *, message):
        for _ in range(5):
            await ctx.send(message)

    # Av command
    @commands.command(aliases=['av', 'pfp'], description='Shows the specified user\'s avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        if member is not None:
            url = str(member.avatar)
            png_url = str(url).replace('webp', 'png')
            jpg_url = str(url).replace('webp', 'jpg')
            embed = discord.Embed(colour=member.colour)
            embed.set_author(name=str(member), icon_url=url)
            embed.set_image(url=url)
            embed.add_field(name='Download this image', value=f'[webp]({url}) | [png]({png_url}) | [jpg]({jpg_url})')
            await ctx.reply(embed=embed)
        else:
            member = ctx.message.author
            url = member.avatar
            png_url = str(url).replace('webp', 'png')
            jpg_url = str(url).replace('webp', 'jpg')
            embed = discord.Embed(colour=member.colour)
            embed.set_author(name=str(member), icon_url=url)
            embed.set_image(url=url)
            embed.add_field(name='Download this image', value=f'[webp]({url}) | [png]({png_url}) | [jpg]({jpg_url})')
            await ctx.reply(embed=embed)

    @commands.command(aliases=['serverpfp', 'serverav', 'serveravatar'], description='Shows the server\'s icon')
    async def servericon(self, ctx):
        url = str(ctx.guild.icon)
        png_url = str(url).replace('webp', 'png')
        jpg_url = str(url).replace('webp', 'jpg')
        embed = discord.Embed(colour=discord.Colour.random())
        embed.set_author(name=ctx.guild.name, icon_url=url)
        embed.set_image(url=url)
        embed.add_field(name='Download this image', value=f'[webp]({url}) | [png]({png_url}) | [jpg]({jpg_url})')
        embed.set_footer(text=f'Requested by {ctx.author} • {today.strftime("%B %d, %Y")}')
        await ctx.send(embed=embed)

    @commands.command(aliases=['ms'], description='Spams a message 25 times')
    async def megaspam(self, ctx, *, message):
        await ctx.message.delete()
        for _ in range(25):
            await ctx.send(message)

    @commands.command(name='poll', description='Make a poll!')
    async def poll(self, ctx, channel: discord.TextChannel = None, *, question):
        embed = discord.Embed(colour=discord.Colour.random())
        embed.add_field(name='Poll', value=f'**{question}**', inline=False)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(text=f'Poll made by {ctx.author} • {today.strftime("%B %d, %Y")}')
        embed.set_thumbnail(url=ctx.guild.icon_url)
        msg = await channel.send(embed=embed)
        await msg.add_reaction('👍')
        await msg.add_reaction('👎')

    @commands.command(aliases=['yt', 'youtube', 'ytsearch'], description='Searches YouTube and responds with the top result')
    async def search(self, ctx, *, query):
        original_query = query
        query = query.replace(' ', '+')
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + query)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        video = pafy.new("https://www.youtube.com/watch?v=" + video_ids[0])
        embed = discord.Embed(colour=discord.Colour.red())
        embed.add_field(name='Search Query:',
                        value=f'[{original_query.upper()}](https://www.youtube.com/results?search_query={query})')
        embed.add_field(name='Top Result:', value=f'[{video.title}](https://www.youtube.com/watch?v={video_ids[0]})')
        if video.author == video.username:
            embed.add_field(name='Video Author:', value=f'[{video.author}](https://youtube.com/c/{video.author})')
        else:
            embed.add_field(name='Video Author:',
                            value=f'[{video.author}](https://youtube.com/channel/{video.username})')
        embed.set_image(url=video.bigthumbhd)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(text=f'Duration: {video.duration}, 🎥: {video.viewcount}, 👍: {video.likes}')
        button = Button(label='Watch Video', url=f'https://www.youtube.com/watch?v={video_ids[0]}')
        view = View()
        view.add_item(button)
        await ctx.send(embed=embed, view=view)

    @commands.command(name='code', description='Shows the code of the module')
    async def code(self, ctx, module):
        module = module.lower()
        try:
            with open(f'cogs/{module}.py') as code_file:
                code = code_file.read()
                with open(f'Code for {module}.txt', 'w+') as text_file:
                    text_file.write(code)
            await ctx.send(file=discord.File(f'Code for {module}.txt'))
            os.remove(f'Code for {module}.txt')
        except FileNotFoundError:
            embed = discord.Embed(title=f'Module {module} not found', colour=discord.Colour.random())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)


# Setup
def setup(bot):
    bot.add_cog(Misc(bot))

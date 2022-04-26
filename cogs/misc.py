# All misc commands stored here
import datetime
import discord
import requests
import os
from tools import send_error_embed
from discord.ext import commands


# Gets quote from https://zenquotes.io api
def get_quote() -> list:
    return requests.get('https://zenquotes.io/api/random').json()


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Quote command
    @commands.command(aliases=['qu'], description='Replies with an inspirational quote', usage='quote')
    async def quote(self, ctx):
        quote = get_quote()

        if quote[0]['a'] == 'zenquotes.io':
            await send_error_embed(ctx, description='Please wait for a few seconds before using this command again')
            return

        embed = discord.Embed(
            description=f'**{quote[0]["q"]}**',
            colour=discord.Colour.blue()
        )
        embed.set_author(name=quote[0]['a'])
        await ctx.send(embed=embed)

    @quote.error
    async def quote_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Spam command
    @commands.command(aliases=['s'], description='Spams text or users', usage='spam <message>')
    async def spam(self, ctx, *, message):
        for _ in range(5):
            await ctx.send(message)

    @spam.error
    async def spam_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify a message to spam\n\nProper Usage: `{self.bot.get_command("spam").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Av command
    @commands.command(aliases=['av', 'pfp'], description='Shows the specified user\'s avatar', usage='avatar <user>')
    async def avatar(self, ctx, *, member: discord.Member = None):
        if member is None:
            member = ctx.author
        # Getting the urls
        png_url = str(member.avatar) if member.avatar else str(member.default_avatar)
        webp_url = png_url.replace('png', 'webp')
        jpg_url = png_url.replace('png', 'jpg')
        # Response embed
        embed = discord.Embed(colour=member.colour)
        embed.set_author(name=str(member), icon_url=png_url)
        embed.set_image(url=png_url)
        embed.add_field(name='Download this image', value=f'[webp]({webp_url}) | [png]({png_url}) | [jpg]({jpg_url})')
        await ctx.reply(embed=embed)

    @avatar.error
    async def avatar_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify a valid user\n\nProper Usage: `{self.bot.get_command("avatar").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Servericon command
    @commands.command(aliases=['serverpfp', 'serverav', 'serveravatar'], description='Shows the server\'s icon',
                      usage='servericon')
    async def servericon(self, ctx):
        if ctx.guild.icon is None:
            await send_error_embed(ctx, description='This server has no icon')
            return
        # Getting the urls
        png_url = str(ctx.guild.icon)
        webp_url = png_url.replace('png', 'webp')
        jpg_url = png_url.replace('png', 'jpg')
        # Response embed
        embed = discord.Embed(colour=discord.Colour.random())
        embed.set_author(name=ctx.guild.name, icon_url=png_url)
        embed.set_image(url=png_url)
        embed.add_field(name='Download this image', value=f'[webp]({webp_url}) | [png]({png_url}) | [jpg]({jpg_url})')
        embed.set_footer(text=f'Requested by {ctx.author}',
                         icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(ctx.author.default_avatar))
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    @servericon.error
    async def servericon_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Megaspam command
    @commands.command(aliases=['ms'], description='Spams a message 25 times', usage='megaspam <message>')
    @commands.has_permissions(manage_messages=True)
    async def megaspam(self, ctx, *, message):
        await ctx.message.delete()
        for _ in range(25):
            await ctx.send(message)

    @megaspam.error
    async def megaspam_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify a message\n\nProper Usage: `{self.bot.get_command("megaspam").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Code command
    @commands.command(name='code',
                      description='Shows the code of the module\nModules of the bot: Events, Fun, Help, Info, Internet, MISC, Moderation, Music, Util',
                      usage='code <module>')
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
            await send_error_embed(ctx,
                                   description=f'Module {module} not found\nModules of the bot: Events, Fun, Help, Info, Internet, MISC, Moderation, Music, Util')

    @code.error
    async def code_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify a module\n\nProper Usage: `{self.bot.get_command("code").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')


# Setup
def setup(bot):
    bot.add_cog(Misc(bot))

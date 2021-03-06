# Copyright (c) 2022 Sandeep Kanekal
# All misc commands stored here
import datetime
import discord
from tools import send_error_embed
from discord.ext import commands


class Misc(commands.Cog):
    def __init__(self, bot):
        """
        Initialize the cog

        :param bot: The bot
        :type bot: commands.Bot

        :return: None
        :rtype: None
        """
        self.bot = bot  # type: commands.Bot

    # Spam command
    @commands.command(aliases=['s'], description='Spams text', usage='spam <message>')
    async def spam(self, ctx, *, text: str):
        """
        Spams text

        :param ctx: The context of where the message was sent
        :param text: The text to spam

        :type ctx: commands.Context
        :type text: str

        :return: None
        :rtype: None
        """
        if ctx.message.mentions:
            await send_error_embed(ctx, description='You cannot mention users in spam!')
            return
        for _ in range(5):
            await ctx.send(text)

    @spam.error
    async def spam_error(self, ctx, error):
        """
        Error handler for the spam command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify a message to spam\n\nProper Usage: `{self.bot.get_command("spam").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Av command
    @commands.command(aliases=['av', 'pfp'], description='Shows the specified user\'s avatar', usage='avatar <user>')
    async def avatar(self, ctx, *, member: discord.Member = None):
        """
        Shows the specified user's avatar. If no user is specified, shows the author's avatar

        :param ctx: The context of where the message was sent
        :param member: The member to show the avatar of

        :type ctx: commands.Context
        :type member: discord.Member

        :return: None
        :rtype: None
        """
        member = member or ctx.author  # type: discord.Member
        # Response embed
        embed = discord.Embed(colour=member.colour)
        embed.set_author(name=member.name, icon_url=member.display_avatar)
        embed.set_image(url=member.display_avatar)
        embed.add_field(name='Download this image', value=f'[Click Here]({member.display_avatar})')
        await ctx.reply(embed=embed)

    @avatar.error
    async def avatar_error(self, ctx, error):
        """
        Error handler for the avatar command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.BadArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify a valid user\n\nProper Usage: `{self.bot.get_command("avatar").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Servericon command
    @commands.command(aliases=['serverpfp', 'serverav', 'serveravatar'], description='Shows the server\'s icon',
                      usage='servericon')
    async def servericon(self, ctx):
        """
        Shows the server's icon

        :param ctx: The context of where the message was sent

        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
        if ctx.guild.icon is None:
            await send_error_embed(ctx, description='This server has no icon')
            return
        # Response embed
        embed = discord.Embed(colour=discord.Colour.random(), timestamp=datetime.datetime.now())
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        embed.set_image(url=ctx.guild.icon)
        embed.add_field(name='Download this image', value=f'[Click Here]({ctx.guild.icon})')
        embed.set_footer(text=f'Requested by {ctx.author}',
                         icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(ctx.author.default_avatar))
        await ctx.send(embed=embed)

    # Megaspam command
    @commands.command(aliases=['ms'], description='Spams a message 25 times', usage='megaspam <message>')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def megaspam(self, ctx, *, message):
        """
        Spams a message 25 times

        :param ctx: The context of where the message was sent
        :param message: The message to spam

        :type ctx: commands.Context
        :type message: str

        :return: None
        :rtype: None
        """
        if ctx.message.mentions:
            await send_error_embed(ctx, description='You cannot mention users in megaspam')
            return

        await ctx.message.delete()
        await ctx.send('\n'.join(message for _ in range(25)))

    @megaspam.error
    async def megaspam_error(self, ctx, error):
        """
        Error handler for the megaspam command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.CommandOnCooldown):
            await send_error_embed(ctx,
                                   description=f'You are on cooldown. Try again in {error.retry_after:.2f} seconds')
        elif isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Please specify a message to spam\n\nProper Usage: `{self.bot.get_command("megaspam").usage}`')
        elif isinstance(error, discord.HTTPException):
            await send_error_embed(ctx, description='Your message is too long!')  
        else:
            await send_error_embed(ctx, description=f'Error: `{error}`')


# Setup
def setup(bot):
    """
    Loads the Cog.

    :param bot: The bot to load the Cog into

    :type bot: commands.Bot

    :return: None
    :rtype: None
    """
    bot.add_cog(Misc(bot))

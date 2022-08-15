# Copyright (c) 2022 Sandeep Kanekal
# All misc commands stored here
import datetime
import discord
from tools import send_error_embed, inform_owner
from discord.ext import commands
from ui_components import FeatureView


class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
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
    async def spam(self, ctx: commands.Context, *, text: str):
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
    async def spam_error(self, ctx: commands.Context, error: commands.CommandError):
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
        await send_error_embed(ctx,
                               description='An error has occurred while running the spam command! The owner has been notified.')
        await inform_owner(self.bot, error)

    # Av command
    @commands.command(aliases=['av', 'pfp'], description='Shows the specified user\'s avatar', usage='avatar <user>')
    async def avatar(self, ctx: commands.Context, *, member: discord.Member = None):
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
    async def avatar_error(self, ctx: commands.Context, error: commands.CommandError):
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
        await send_error_embed(ctx,
                               description='An error has occurred while running the avatar command! The owner has been notified.')
        await inform_owner(self.bot, error)

    # Servericon command
    @commands.command(aliases=['serverpfp', 'serverav', 'serveravatar'], description='Shows the server\'s icon',
                      usage='servericon')
    async def servericon(self, ctx: commands.Context):
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
    async def megaspam(self, ctx: commands.Context, *, message):
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
    async def megaspam_error(self, ctx: commands.Context, error: commands.CommandError):
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
        elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.HTTPException):
            await send_error_embed(ctx, description='Your message is too long!')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the megaspam command! The owner has been notified.')
            await inform_owner(self.bot, error)

    @commands.command(name='featuresuggest', aliases=['feature'], description='Suggest the owner of the bot, a feature',
                      usage='featuresuggest <feature>')
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def featuresuggest(self, ctx: commands.Context, *, feature: str):
        """
        Suggest a feature to the owner of the bot

        :param ctx: The context of where the message was sent
        :param feature: The feature to suggest

        :type ctx: commands.Context
        :type feature: str

        :return: None
        :rtype: None
        """
        # Respond to the author
        await ctx.message.delete()
        await ctx.send('The feature has been suggested!', delete_after=3)

        # Suggestion embed
        embed = discord.Embed(
            title='New feature suggestion!',
            description=feature,
            colour=discord.Colour.blurple(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.display_avatar)

        # Send suggestion to owner
        await self.bot.get_user(800018344702640180).send(embed=embed, view=FeatureView(ctx.author, timeout=None))

    @featuresuggest.error
    async def featuresuggest_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the featuresuggest command

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
                                   description=f'Please specify a feature to suggest\n\nProper Usage: `{self.bot.get_command("featuresuggest").usage}`')
        else:
            await send_error_embed(ctx,
                                   description='An error has occurred while running the featuresuggest command! The owner has been notified.')
            await inform_owner(self.bot, error)


# Setup
def setup(bot: commands.Bot):
    """
    Loads the Cog.

    :param bot: The bot to load the Cog into

    :type bot: commands.Bot

    :return: None
    :rtype: None
    """
    bot.add_cog(Misc(bot))

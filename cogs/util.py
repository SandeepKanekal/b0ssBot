# Copyright (c) 2022 Sandeep Kanekal
# All Util commands stored here
import asyncio
import contextlib
import discord
import datetime
from tools import send_error_embed, convert_to_unix_time, inform_owner
from sql_tools import SQL
from discord.ext import commands


class Util(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # A listener which defines what must be done when a message is deleted
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """
        Event listener which is called when a message is deleted.

        :param message: The message that was deleted

        :type message: discord.Message

        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        # Replace single quotes with double quotes
        content = message.content.replace("'", "''")

        if not isinstance(message.author, discord.Member):
            return

        # Make a list of values
        if message.attachments:
            attachment_str = ', '.join(f"'{attachment.url}'" for attachment in message.attachments)
            values = [f'\'{message.author.id}\'', f'\'{content}\'', f'\'{message.channel.id}\'',
                      f'\'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")}\'', f"'{message.guild.id}'",
                      f"ARRAY[{attachment_str}]"]

        else:
            values = [f'\'{message.author.id}\'', f'\'{content}\'', f'\'{message.channel.id}\'',
                      f'\'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")}\'', f"'{message.guild.id}'",
                      "ARRAY['None']"]
            attachment_str = "ARRAY['None']"

        # Update databse
        if sql.select(elements=['*'], table='snipes',
                      where=f'guild_id = \'{message.guild.id}\' AND channel_id = \'{message.channel.id}\''):
            sql.update(table='snipes', column='message', value=f'\'{content}\'',
                       where=f"guild_id = '{message.guild.id}' AND channel_id = '{message.channel.id}'")
            sql.update(table='snipes', column='author_id', value=f'\'{message.author.id}\'',
                       where=f"guild_id = '{message.guild.id}' AND channel_id = '{message.channel.id}'")
            sql.update(table='snipes', column='time',
                       value=f'\'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")}\'',
                       where=f"guild_id = '{message.guild.id}' AND channel_id = '{message.channel.id}'")
            if message.attachments:
                sql.update(table='snipes', column='attachments', value=f"ARRAY[{attachment_str}]",
                           where=f"guild_id = '{message.guild.id}' AND channel_id = '{message.channel.id}'")
            else:
                sql.update(table='snipes', column='attachments', value="ARRAY['None']",
                           where=f"guild_id = '{message.guild.id}' AND channel_id = '{message.channel.id}'")
        
        # Insert into database
        else:
            sql.insert(table='snipes',
                       columns=['author_id', 'message', 'channel_id', 'time', 'guild_id', 'attachments'],
                       values=values)

    # Snipe command
    @commands.command(name='snipe', description='Snipes the most recently deleted message', usage='snipe')
    @commands.has_permissions(manage_messages=True)
    async def snipe(self, ctx: commands.Context):
        """
        Snipes the most recently deleted message in the channel.

        :param ctx: The context of where the command was used

        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        # Get the latest message
        if message := sql.select(
                elements=['author_id', 'message', 'channel_id', 'time', 'attachments'],
                table='snipes',
                where=f'guild_id = \'{ctx.guild.id}\' AND channel_id = \'{ctx.channel.id}\''
        ):
            # Get the time of deletion and convert to unix time
            del_time = message[0][3]
            del_time = convert_to_unix_time(del_time)
            channel = discord.utils.get(ctx.guild.channels, id=int(message[0][2]))
            member = discord.utils.get(ctx.guild.members, id=int(message[0][0]))
            content = message[0][1].replace("''", "'")

            # Get the prefix
            command_prefix = sql.select(elements=["prefix"], table="prefixes", where=f"guild_id = '{ctx.guild.id}'")[0][
                0]

            # Response embed
            embed = discord.Embed(
                title='Sniped a message!',
                description=f'Author: {member.mention if isinstance(member, discord.Member) else member}\nDeleted message: {content}\nChannel: {channel.mention}\nTime: {del_time}',
                colour=discord.Colour.green()
            ).set_footer(
                text=f'Enable modlogs for more information. Type {command_prefix}help modlogs for more information')
            embed.set_thumbnail(url=ctx.guild.icon or discord.Embed.Empty)
            embed.add_field(name='Attachments', value='\n\n'.join(message[0][4]))

            await ctx.send(embed=embed)

        else:
            await send_error_embed(ctx, 'There are no messages to snipe.')

    @snipe.error
    async def snipe_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the snipe command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingPermissions):
            await send_error_embed(ctx, 'You do not have the required permissions to use this command.')
        else:
            await send_error_embed(ctx, 'An error occurred while running the snipe command! The owner has been informed.')
            await inform_owner(self.bot, error)

    # AFK command
    @commands.command(name='afk', description='Marks the user as AFK', usage='afk <reason>')
    async def afk(self, ctx: commands.Context, *, reason: str = 'No reason'):
        """
        Marks the user as AFK.
        
        :param ctx: The context of where the command was used
        :param reason: The reason for being AFK

        :type ctx: commands.Context
        :type reason: str
        
        :return: None
        :rtype: None
        """
        member = ctx.author
        reason = reason.replace("'", "''")
        member_details = member.name.replace("'", "''") + '#' + member.discriminator

        sql = SQL('b0ssbot')

        with contextlib.suppress(discord.Forbidden):
            await member.edit(nick=f'[AFK] {member.display_name}')  # Changing the nickname

        # Adds member details to the database
        sql.insert(table='afks', columns=['member', 'member_id', 'guild_id', 'reason'],
                   values=[f'\'{member_details}\'', f'\'{str(member.id)}\'', f'\'{str(ctx.guild.id)}\'',
                           f'\'{reason}\''])

        # Create embed
        embed = discord.Embed(title='AFK', description=f'{member.mention} has gone AFK', colour=member.colour, timestamp=datetime.datetime.now())
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.add_field(name='AFK note', value=reason.replace("''", "'"))

        await ctx.send(embed=embed)

    @afk.error
    async def afk_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the afk command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await send_error_embed(ctx, 'An error occurred while running the afk command! The owner has been informed.')
        await inform_owner(self.bot, error)

    # Ping command
    @commands.command(name="ping", description='Replies with the latency of the bot', usage='ping')
    async def ping(self, ctx: commands.Context):
        """
        Replies with the latency of the bot.
        
        :param ctx: The context of where the command was used

        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        await ctx.reply(
            embed=discord.Embed(
                description=f'**Pong!!** Bot latency is {round(self.bot.latency * 1000)}ms', 
                colour=discord.Colour.yellow()
            )
        )

    # Clear command
    @commands.command(aliases=['purge'],
                      description='Purges the amount of messages specified by the user\nPinned messages are not cleared',
                      usage='clear <limit>')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, limit: int):
        """
        Purges the amount of messages specified by the user.
        
        :param ctx: The context of where the command was used
        :param limit: The amount of messages to purge
        
        :type ctx: commands.Context
        :type limit: int

        :return: None
        :rtype: None
        """
        # Deltet command and purge unpinned messages
        await ctx.message.delete()
        await ctx.channel.purge(limit=limit, check=lambda m: not m.pinned)

        # Send confirmation
        msg = await ctx.send(f'Cleared {limit} messages')
        await asyncio.sleep(5)
        with contextlib.suppress(discord.NotFound):
            await msg.delete()

    # Permission errors in the clear command is handled here
    @clear.error
    async def clear_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the clear command

        :param ctx: The context of where the command was used
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Provide a limit\n\nProper Usage: `{self.bot.get_command("clear").usage}`')
        elif isinstance(error, commands.BadArgument):
            await send_error_embed(ctx,
                                   description=f'Provide a valid number\n\nProper Usage: `{self.bot.get_command("clear").usage}`')
        elif isinstance(error, commands.MissingPermissions):
            await send_error_embed(ctx, 'You do not have the required permissions to use this command.')
        else:
            await send_error_embed(ctx, description='An error occurred while running the clear command! The owner has been informed.')
            await inform_owner(self.bot, error)

    # Poll command
    @commands.command(name='poll', description='Make a poll!', usage='poll <question>')
    async def poll(self, ctx: commands.Context, *, question: str):
        """
        Makes a poll.

        :param ctx: The context of where the command was used
        :param question: The question for the poll

        :type ctx: commands.Context
        :type question: str

        :return: None
        :rtype: None
        """
        msg = await ctx.send(embed=discord.Embed(title='Poll', description=question, colour=discord.Colour.random()))
        # Adding reactions
        await msg.add_reaction('👍')
        await msg.add_reaction('👎')

    @poll.error
    async def poll_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the poll command

        :param ctx: The context of where the command was used
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Provide a question\n\nProper Usage: `{self.bot.get_command("poll").usage}`')

        else:
            await send_error_embed(ctx, 'An error occurred while running the poll command! The owner has been informed.')
            await inform_owner(self.bot, error)

    # Refer command
    @commands.command(name='refer', description='Refers to a message, message ID or link required as a parameter',
                      usage='refer <message_id or message_link>')
    async def refer(self, ctx: commands.Context, message_reference: str):
        """
        Refers to a message, message ID or link required as a parameter.

        :param ctx: The context of where the command was used
        :param message_reference: The message ID or link to refer to

        :type ctx: commands.Context
        :type message_reference: str

        :return: None
        :rtype: None
        """
        # Get the message ID
        message_id = message_reference
        if message_reference.startswith('https://discord.com/channels/'):  # Message ID
            message_id = message_reference.split('/')[6]

        # Get the message and respond appropriately
        try:
            message = await ctx.fetch_message(message_id)
        except discord.NotFound:
            await send_error_embed(ctx, description='Message not found')
        else:
            embed = discord.Embed(colour=message.author.colour, timestamp=datetime.datetime.now())
            embed.set_author(name=message.author, icon_url=message.author.display_avatar, url=message.jump_url)
            embed.add_field(name=message.content or "Message does not contain content",
                            value=f'\n[Jump to message]({message.jump_url})')
            embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.display_avatar)
            await ctx.send(embed=embed)

            if message.embeds:
                await ctx.send('Message contains embeds', embeds=message.embeds)

    @refer.error
    async def refer_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the refer command

        :param ctx: The context of where the command was used
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Provide a message reference\n\nProper Usage: `{self.bot.get_command("refer").usage}`')
        elif isinstance(error, commands.CommandInvokeError) and isinstance(error.__cause__, discord.HTTPException):
            await send_error_embed(ctx, description='Provided argument is not a message ID or link')
        else:
            await send_error_embed(ctx, 'An error occurred while running the refer command! The owner has been informed.')
            await inform_owner(self.bot, error)

    @commands.command(name='prefix', desrciption='Change the prefix of the bot for the guild',
                      usage='prefix <new_prefix>')
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx: commands.Context, new_prefix):
        """
        Changes the prefix of the bot for the guild.

        :param ctx: The context of where the command was used
        :param new_prefix: The new prefix for the guild

        :type ctx: commands.Context
        :type new_prefix: str

        :return: None
        :rtype: None
        """
        if len(new_prefix) > 2:
            await ctx.send('Prefix must be 2 characters or less')
            return

        # Update database
        sql = SQL('b0ssbot')
        sql.update(table='prefixes', column='prefix', value=f'\'{new_prefix}\'', where=f'guild_id=\'{ctx.guild.id}\'')

        # Respond
        embed = discord.Embed(
            description=f'Prefix changed to **{new_prefix}**',
            colour=discord.Colour.green()
        ).set_thumbnail(url=ctx.guild.icon or discord.Embed.Empty)
        await ctx.reply(embed=embed)

    @prefix.error
    async def prefix_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the prefix command

        :param ctx: The context of where the command was used
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Provide a prefix\n\nProper Usage: `{self.bot.get_command("prefix").usage}`')
        else:
            await send_error_embed(ctx, description='An error occurred while running the prefix command! The owner has been informed.')
            await inform_owner(self.bot, error)

    @commands.command(name='serverclear', aliases=['sc'], description='Clear all messages in the server containing the specific content.', usage='serverclear <content>')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 1800, commands.BucketType.guild)
    async def serverclear(self, ctx: commands.Context, *, content: str):
        """
        Clear all messages in the server containing the specific content.

        :param ctx: The context of where the command was used
        :param content: The content to search for in the messages to delete

        :type ctx: commands.Context
        :type content: str

        :return: None
        :rtype: None
        """
        # Inform the user that this will take a while
        msg = await ctx.reply('This may take a while... Pinned messages will not be cleared.')
        information = await ctx.send('Initializing...')

        # Delete command message
        await ctx.message.delete()

        for channel in ctx.guild.text_channels:
            await information.edit(f'Clearing in {channel.mention}')
            
            # Get the messages to delete
            messages = list(filter(lambda m: content in m.content and not m.pinned, await channel.history(limit=None).flatten()))

            # Delete the messages
            for message in messages:
                await message.delete()
        
        await information.edit('Done!', delete_after=5)
        await msg.delete()

    
    @serverclear.error
    async def serverclear_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the serverclear command

        :param ctx: The context of where the command was used
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   description=f'Provide a content to search for\n\nProper Usage: `{self.bot.get_command("serverclear").usage}`')
        elif isinstance(error, commands.CommandOnCooldown):
            await send_error_embed(ctx, description=f'This command is on cooldown! Try again in {error.retry_after:.2f} seconds.')
        elif isinstance(error, commands.MissingPermissions):
            await send_error_embed(ctx, description=f'Error: `{error}`')
        else:
            await send_error_embed(ctx, description='An error occurred while running the serverclear command! The owner has been informed.')
            await inform_owner(self.bot, error)


def setup(bot: commands.Bot):
    """
    Adds the util cog to the bot

    :param bot: The bot

    :type bot: commands.Bot

    :return: None
    :rtype: None
    """
    bot.add_cog(Util(bot))

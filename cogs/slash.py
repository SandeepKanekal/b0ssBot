# Copyright (c) 2022 Sandeep Kanekal
import contextlib
import discord
import datetime
import requests
import os
import asyncio
from discord.ext import commands
from discord.commands import Option, SlashCommandGroup
from tools import convert_to_unix_time, inform_owner
from sql_tools import SQL
from googleapiclient.discovery import build
from PIL import Image, ImageChops, UnidentifiedImageError
from ui_components import EmbedView


class Slash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """
        Initialize the cog
        
        :param bot: The bot object
        :type bot: commands.Bot
        
        :return: None
        :rtype: None
        """
        self.bot = bot  # type: commands.Bot

    @commands.slash_command(name='prefix', description='Change the prefix of the bot for the server',
                            usage='prefix <new_prefix>')
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx: discord.ApplicationContext,
                     new_prefix: Option(str, descrciption='The new prefix', required=True)):
        """
        Change the prefix of the bot for the server.
        
        :param ctx: The context of the message
        :param new_prefix: The new prefix

        :type ctx: discord.ApplicationContext
        :type new_prefix: str

        :return: None
        :rtype: None
        """
        if len(new_prefix) > 2:
            await ctx.respond('Prefix must be 2 characters or less')
            return

        sql = SQL('b0ssbot')  # type: SQL
        sql.update(table='prefixes', column='prefix', value=f'\'{new_prefix}\'', where=f'guild_id=\'{ctx.guild.id}\'')
        await ctx.respond(f'Prefix changed to **{new_prefix}**')

    @prefix.error
    async def prefix_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the prefix command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError

        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to change the prefix')
        else:
            await ctx.respond('An error has occurred while running the prefix command! The owner has been notified.',
                              ephemeral=True)
            await inform_owner(self.bot, error)

    @commands.slash_command(name='userinfo',
                            description='Shows the mentioned user\'s information. Leave it blank to get your information',
                            usage='userinfo <member>')
    async def userinfo(self, ctx: discord.ApplicationContext,
                       member: Option(discord.Member, description='The user to get info on', required=False,
                                      default=None)):
        """
        Shows the mentioned user's information. Leave it blank to get your information.
        
        :param ctx: The context of the message
        :param member: The user to get info on
        
        :type ctx: discord.ApplicationContext
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        member = member or ctx.author  # type: discord.Member

        # Getting the dates
        joined_at = member.joined_at.strftime('%Y-%m-%d %H:%M:%S:%f')  # type: str
        registered_at = member.created_at.strftime('%Y-%m-%d %H:%M:%S:%f')  # type: str

        # Converting to unix timestamps
        joined_at = convert_to_unix_time(joined_at)  # type: str
        registered_at = convert_to_unix_time(registered_at)  # type: str

        # Create embed
        embed = discord.Embed(colour=member.colour, timestamp=datetime.datetime.now())

        # Set details
        embed.set_footer(text=f'ID: {member.id}')
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name=str(member), icon_url=member.display_avatar)

        # Add fields
        embed.add_field(name='Display Name', value=member.mention, inline=True)
        embed.add_field(name='Top Role', value=member.top_role.mention, inline=True)

        if len(member.roles) > 1:
            role_string = ' '.join([r.mention for r in member.roles][1:])
            embed.add_field(name=f'Roles[{len(member.roles) - 1}]', value=role_string, inline=False)
        else:
            embed.add_field(name='Roles[1]', value=member.top_role.mention, inline=False)

        embed.add_field(name='Permissions',
                        value=', '.join([p[0].replace('_', ' ').title() for p in member.guild_permissions if p[1]]),
                        inline=False)
        embed.add_field(name='Joined', value=joined_at, inline=True)
        embed.add_field(name='Registered', value=registered_at, inline=True)

        await ctx.respond(embed=embed)

    @userinfo.error
    async def userinfo_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the userinfo command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        await ctx.respond('An error has occurred while running the userinfo command! The owner has been notified.',
                          ephemeral=True)
        await inform_owner(self.bot, error)

    @commands.slash_command(name='avatar', description='Shows the specified user\'s avatar', usage='avatar <user>')
    async def avatar(self, ctx: discord.ApplicationContext,
                     member: Option(discord.Member, description='User to get the avatar of', required=False,
                                    default=None)):
        """
        Shows the specified user's avatar.
        
        :param ctx: The context of the message
        :param member: The user to get the avatar of
        
        :type ctx: discord.ApplicationContext
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
        await ctx.respond(embed=embed)

    @avatar.error
    async def avatar_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the avatar command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        await ctx.respond('An error has occurred while running the avatar command! The owner has been notified.',
                          ephemeral=True)
        await inform_owner(self.bot, error)

    youtubenotification = SlashCommandGroup(name='youtubenotification',
                                            description='Configure YouTube notifications for the server')

    @youtubenotification.command(name='add', description='Add a YouTube channel to the server')
    @commands.has_permissions(manage_guild=True)
    async def youtubenotification_add(self, ctx: discord.ApplicationContext, text_channel: Option(discord.TextChannel,
                                                                                                  description='The text channel to send notifications to',
                                                                                                  required=True),
                                      youtube_channel: Option(str, description='The URL of the YouTube channel',
                                                              required=True), ping_role: Option(discord.Role,
                                                                                                description='The role to ping when a video is uploaded',
                                                                                                required=False,
                                                                                                default=None)):
        """
        Add a YouTube channel to the server
        
        :param ctx: The context of the command
        :param text_channel: The text channel to send notifications to
        :param youtube_channel: The URL of the YouTube channel
        :param ping_role: The role to ping when a video is uploaded

        :type ctx: discord.ApplicationContext
        :type text_channel: discord.TextChannel
        :type youtube_channel: str
        :type ping_role: discord.Role

        :return: None
        :rtype: None
        """
        await ctx.interaction.response.defer()

        sql = SQL('b0ssbot')
        youtube = build('youtube', 'v3', developerKey=os.getenv('youtube_api_key'))

        # Get the channel ID
        youtube_channel_id = requests.get(
            f"https://www.googleapis.com/youtube/v3/search?part=id&q={youtube_channel.split('/c/')[1]}&type=channel&key={os.getenv('youtube_api_key')}").json()[
            'items'][0]['id']['channelId'] if '/c/' in youtube_channel else youtube_channel.split('/channel/')[1]

        # Check if the channel has already been added
        if sql.select(elements=['*'], table='youtube',
                      where=f"guild_id='{ctx.guild.id}' and channel_id = '{youtube_channel_id}'"):
            await ctx.respond('Channel already added', ephemeral=True)
            return

        # Get details of the channel and latest video
        channel = youtube.channels().list(id=youtube_channel_id, part='snippet, contentDetails').execute()
        latest_video_id = youtube.playlistItems().list(
            playlistId=channel['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
            part='contentDetails').execute()['items'][0]['contentDetails']['videoId']
        channel_name = channel['items'][0]['snippet']['title'].replace("'", "''")

        # Insert into database
        sql.insert(table='youtube',
                   columns=['guild_id', 'text_channel_id', 'channel_id', 'channel_name', 'latest_video_id',
                            'ping_role'],
                   values=[f"'{ctx.guild.id}'", f"'{text_channel.id}'", f"'{channel['items'][0]['id']}'",
                           f"'{channel_name}'", f"'{latest_video_id}'",
                           f"'{ping_role.id}'" if ping_role else "'None'"])

        # Respond to the user
        await ctx.respond(
            f'NOTE: This command requires **Send Webhooks** to be enabled in {text_channel.mention}',
            embed=discord.Embed(
                colour=0xFF0000,
                description=f'YouTube notifications for the channel **[{channel["items"][0]["snippet"]["title"]}](https://youtube.com/channel/{channel["items"][0]["id"]})** will now be sent to {text_channel.mention}').set_thumbnail(
                url=channel["items"][0]["snippet"]["thumbnails"]["high"]["url"])
        )

    @youtubenotification_add.error
    async def youtubenotification_add_error(self, ctx: discord.ApplicationContext,
                                            error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the youtube add command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the youtube add command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @youtubenotification.command(name='remove', description='Remove a YouTube channel from the server')
    @commands.has_permissions(manage_guild=True)
    async def youtubenotification_remove(self, ctx: discord.ApplicationContext,
                                         youtube_channel: Option(str, description='The URL of the YouTube channel',
                                                                 required=True)):
        """
        Remove a YouTube channel from the server
        
        :param ctx: The context of the command
        :param youtube_channel: The URL of the YouTube channel
        
        :type ctx: discord.ApplicationContext
        :type youtube_channel: str
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')
        youtube = build('youtube', 'v3', developerKey=os.getenv('youtube_api_key'))

        # Get the channel ID
        youtube_channel_id = requests.get(
            f"https://www.googleapis.com/youtube/v3/search?part=id&q={youtube_channel.split('/c/')[1]}&type=channel&key={os.getenv('youtube_api_key')}").json()[
            'items'][0]['id']['channelId'] if '/c/' in youtube_channel else youtube_channel.split('/channel/')[1]
        channel = youtube.channels().list(id=youtube_channel_id, part='snippet, contentDetails').execute()

        # Check if the channel has been added
        if not sql.select(elements=['*'], table='youtube',
                          where=f"guild_id='{ctx.guild.id}' and channel_id = '{youtube_channel_id}'"):
            await ctx.respond('Channel not added', ephemeral=True)
            return

        # Get the text channel ID
        text_channel_id = int(sql.select(elements=['text_channel_id'], table='youtube',
                                         where=f'guild_id = \'{ctx.guild.id}\' AND channel_id = \'{youtube_channel_id}\'')[
                                  0][0])

        # Remove from database
        sql.delete(table='youtube',
                   where=f'guild_id = \'{ctx.guild.id}\' AND channel_id = \'{channel["items"][0]["id"]}\'')

        text_channel = discord.utils.get(ctx.guild.text_channels, id=text_channel_id)

        # Respond to the user
        await ctx.respond(embed=discord.Embed(
            colour=0xFF0000,
            description=f'YouTube notifications for the channel **[{channel["items"][0]["snippet"]["title"]}](https://youtube.com/channel{channel["items"][0]["id"]})** will no longer be sent to {text_channel.mention}').set_thumbnail(
            url=channel["items"][0]["snippet"]["thumbnails"]["high"]["url"]))

    @youtubenotification_remove.error
    async def youtubenotification_remove_error(self, ctx: discord.ApplicationContext,
                                               error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the youtube remove command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the youtube remove command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @youtubenotification.command(name='list', description='List all YouTube channels added to the server')
    async def youtubenotification_list(self, ctx: discord.ApplicationContext):
        """
        List all YouTube channels added to the server
        
        :param ctx: The context of the command
        
        :type ctx: discord.ApplicationContext
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')
        channels = sql.select(elements=['channel_name', 'channel_id', 'text_channel_id'], table='youtube',
                              where=f'guild_id = \'{ctx.guild.id}\'')

        # Check if there are any channels set up
        if not channels:
            await ctx.respond('No channels are currently set up for notifications', ephemeral=True)
            return

        # Create embed
        embed = discord.Embed(
            description='',
            colour=0xFF0000
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon or discord.Embed.Empty)
        embed.set_thumbnail(
            url='https://yt3.ggpht.com/584JjRp5QMuKbyduM_2k5RlXFqHJtQ0qLIPZpwbUjMJmgzZngHcam5JMuZQxyzGMV5ljwJRl0Q=s176-c-k-c0x00ffffff-no-rj')

        # Update the description with the channels
        for index, channel in enumerate(channels):
            text_channel = discord.utils.get(ctx.guild.text_channels, id=int(channel[2]))
            embed.description += f'{index + 1}. **[{channel[0]}](https://youtube.com/channel/{channel[1]})** in {text_channel.mention}\n'

        await ctx.respond(embed=embed)

    @youtubenotification_list.error
    async def youtubenotification_list_error(self, ctx: discord.ApplicationContext,
                                             error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the youtube list command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        await ctx.respond('An error has occurred while running the youtube list command! The owner has been notified.',
                          ephemeral=True)
        await inform_owner(self.bot, error)

    @youtubenotification.command(name='clear', description='Clear all YouTube channels added to the server')
    @commands.has_permissions(manage_guild=True)
    async def youtubenotification_clear(self, ctx: discord.ApplicationContext):
        """
        Clear all YouTube channels added to the server
        
        :param ctx: The context of the command
        
        :type ctx: discord.ApplicationContext
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        # Check if there are any channels set up
        if not sql.select(elements=['*'], table='youtube', where=f'guild_id = \'{ctx.guild.id}\''):
            await ctx.respond('No channels are currently set up for notifications', ephemeral=True)
            return

        # Remove from database
        sql.delete(table='youtube', where=f'guild_id = \'{ctx.guild.id}\'')

        await ctx.respond('All channels removed')

    @youtubenotification_clear.error
    async def youtubenotification_clear_error(self, ctx: discord.ApplicationContext,
                                              error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the youtube clear command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the youtube clear command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @youtubenotification.command(name='update', description='Update YouTube notification configurations')
    @commands.has_permissions(manage_guild=True)
    async def youtubenotification_update(self, ctx: discord.ApplicationContext,
                                         youtube_channel: Option(str, description='The URL of the YouTube channel',
                                                                 required=True),
                                         text_channel: Option(discord.TextChannel,
                                                              description='The channel to the send notifications to',
                                                              required=False, default=None),
                                         ping_role: Option(discord.Role,
                                                           description='The role to ping when a video is uploaded',
                                                           required=False, default=None)):
        """
        Update YouTube notification configurations
        
        :param ctx: The context of the command
        :param youtube_channel: The URL of the YouTube channel
        :param text_channel: The channel to send the notifications to
        :param ping_role: The role to ping when a video is uploaded
        
        :type ctx: discord.ApplicationContext
        :type youtube_channel: str
        :type text_channel: discord.TextChannel
        :type ping_role: discord.Role
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        # Get the channel ID
        youtube_channel_id = requests.get(
            f"https://www.googleapis.com/youtube/v3/search?part=id&q={youtube_channel.split('/c/')[1]}&type=channel&key={os.getenv('youtube_api_key')}").json()[
            'items'][0]['id']['channelId'] if '/c/' in youtube_channel else youtube_channel.split('/channel/')[1]

        # Check if the channel has been added
        if not sql.select(elements=['*'], table='youtube',
                          where=f"guild_id='{ctx.guild.id}' and channel_id = '{youtube_channel_id}'"):
            await ctx.respond('Error: YouTube channel not configured', ephemeral=True)
            return

        # Update the text channel
        if text_channel and int(sql.select(elements=['text_channel_id'], table='youtube',
                                           where=f'guild_id = \'{ctx.guild.id}\' AND channel_id = \'{youtube_channel_id}\'')[
                                    0][0]) != text_channel.id:
            sql.update(table='youtube', column='text_channel_id', value=f"'{text_channel.id}'",
                       where=f"guild_id='{ctx.guild.id}' and channel_id = '{youtube_channel_id}'")

        # Update the ping role
        elif ping_role and (sql.select(elements=['ping_role'], table='youtube',
                                       where=f'guild_id = \'{ctx.guild.id}\' AND channel_id = \'{youtube_channel_id}\'')[
                                0][0] != 'None' or str(ping_role.id)):
            sql.update(table='youtube', column='ping_role', value=f"'{ping_role.id}'",
                       where=f"guild_id='{ctx.guild.id}' and channel_id = '{youtube_channel_id}'")

        else:
            await ctx.respond('No changes made', ephemeral=True)
            return

        await ctx.respond(embed=discord.Embed(
            colour=0xFF0000,
            description='Updates saved!',
            timestamp=datetime.datetime.now()
        ))

    @youtubenotification_update.error
    async def youtubenotification_update_error(self, ctx: discord.ApplicationContext,
                                               error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the youtube update command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the youtube update command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    warn = SlashCommandGroup(name='warn', description='Warn a user')

    @warn.command(name='add', description='Warn a user')
    @commands.has_permissions(moderate_members=True)
    async def warn_add(self, ctx: discord.ApplicationContext,
                       member: Option(discord.Member, description='The member to warn', required=True),
                       reason: Option(str, desription='The reason for the warn', required=False, default='No reason')):
        """
        Warn a user
        
        :param ctx: The context of the command
        :param member: The member to warn
        :param reason: The reason for warning the user
        
        :type ctx: discord.ApplicationContext
        :type member: discord.Member
        :type reason: str
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        if member.id == ctx.author.id:
            await ctx.respond('You can\'t warn yourself')
            return

        if warns := sql.select(
                elements=['warns', 'reason'],
                table='warns',
                where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'",
        ):
            reason_arr = warns[0][1]
            reason_arr.append(reason)
            reason_str = ''.join(f'\'{r}\', ' for r in reason_arr)
            reason_str = reason_str[:-2]
            sql.update(table='warns', column='warns', value=warns[0][0] + 1,
                       where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
            sql.update(table='warns', column='reason', value=f"ARRAY[{reason_str}]",
                       where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")

        else:
            sql.insert(table='warns', columns=['member_id', 'warns', 'guild_id', 'reason'],
                       values=[f"'{member.id}'", "1", f"'{ctx.guild.id}'", f"ARRAY['{reason}']"])
        embed = discord.Embed(
            description=f'{member} has been warned for {reason}',
            colour=discord.Colour.red()
        ).set_author(name=member.name, icon_url=str(member.avatar) if member.avatar else str(member.default_avatar))
        await ctx.respond(embed=embed)

    @warn_add.error
    async def warn_add_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the warn_add command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond('An error has occurred while running the warn add command! The owner has been notified.',
                              ephemeral=True)
            await inform_owner(self.bot, error)

    @warn.command(name='remove', description='Removes the member\'s oldest warn')
    @commands.has_permissions(moderate_members=True)
    async def warn_remove(self, ctx: discord.ApplicationContext,
                          member: Option(discord.Member, description='The member to remove a warn from',
                                         required=True)):
        """
        Removes the member\'s oldest warn
        
        :param ctx: The context of the command
        :param member: The member to remove warns from
        
        :type ctx: discord.ApplicationContext
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        if warns := sql.select(
                elements=['warns', 'reason'],
                table='warns',
                where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'",
        ):
            if warns[0][0] == 1:
                sql.delete(table='warns', where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
            else:
                reason_arr = warns[0][1]
                reason_arr.pop(0)
                reason_str = ''.join(f'\'{r}\', ' for r in reason_arr)
                reason_str = reason_str[:-2]
                sql.update(table='warns', column='warns', value=warns[0][0] - 1,
                           where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
                sql.update(table='warns', column='reason', value=f"ARRAY[{reason_str}]",
                           where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
        else:
            await ctx.respond(f'{member.mention} has no warns', ephemeral=True)
            return

        await ctx.respond(f'{member}\'s oldest warn has been removed')

    @warn_remove.error
    async def warn_remove_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the warn remove command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the warn remove command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @warn.command(name='list', description='Lists the member\'s warns')
    @commands.has_permissions(moderate_members=True)
    async def warn_list(self, ctx: discord.ApplicationContext,
                        member: Option(discord.Member, description='The member to list warns for', required=True)):
        """
        Lists the member\'s warns
        
        :param ctx: The context of the command
        :param member: The member to list warns for
        
        :type ctx: discord.ApplicationContext
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        if warns := sql.select(
                elements=['warns', 'reason'],
                table='warns',
                where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'",
        ):
            embed = discord.Embed(
                title=f'{member} has {warns[0][0]} {("warn" if warns[0][0] == 1 else "warns")}',
                description=f'Reason for latest warn: **{warns[0][1][warns[0][0] - 1]}**',
                colour=discord.Colour.red()
            ).set_author(name=member.name, icon_url=member.avatar or discord.Embed.Empty)

            await ctx.respond(embed=embed)
        else:
            await ctx.respond(f'{member.mention} has no warns', ephemeral=True)
            return

    @warn_list.error
    async def warn_list_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the warn list command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond('An error has occurred while running the warn list command! The owner has been notified.',
                              ephemeral=True)
            await inform_owner(self.bot, error)

    @warn.command(name='clear', description='Clears the member\'s warns')
    @commands.has_permissions(moderate_members=True)
    async def warn_clear(self, ctx: discord.ApplicationContext,
                         member: Option(discord.Member, description='The member to clear warns for', required=True)):
        """
        Clears the member\'s warns
        
        :param ctx: The context of the command
        :param member: The member to clear warns for
        
        :type ctx: discord.ApplicationContext
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        if sql.select(
                elements=['warns', 'reason'],
                table='warns',
                where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'",
        ):
            sql.delete(table='warns', where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
        else:
            await ctx.respond(f'{member.mention} has no warns', ephemeral=True)
            return

        await ctx.respond(f'{member}\'s warns have been cleared')

    @warn_clear.error
    async def warn_clear_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the warn clear command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the warn clear command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    messageresponse = SlashCommandGroup('messageresponse', 'Configure chat responses')

    @messageresponse.command(name='add', description='Adds a chat response')
    @commands.has_permissions(manage_messages=True)
    async def messageresponse_add(self, ctx: discord.ApplicationContext,
                                  message: Option(str, desription='The message to trigger the response to',
                                                  required=True),
                                  response: Option(str, description='The response for the message', required=True)):
        """
        Adds a chat a response

        :param ctx: The context of the command
        :param message: The message to trigger the response to
        :param response: The response for the message
        
        :type ctx: discord.ApplicationContext
        :type message: str
        :type response: str
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')
        original_message = message

        message = message.replace("'", "''").lower()
        response = response.replace("'", "''")

        if sql.select(elements=['message', 'response'], table='message_responses',
                      where=f"guild_id = '{ctx.guild.id}' AND message = '{message}'"):
            await ctx.respond(f'A response for `{original_message}` already exists', ephemeral=True)
            return

        else:
            sql.insert(table='message_responses', columns=['guild_id', 'message', 'response'],
                       values=[f"'{ctx.guild.id}'", f"'{message}'", f"'{response}'"])

        await ctx.respond(f'Response for `{original_message}` added')

    @messageresponse_add.error
    async def messageresponse_add_error(self, ctx: discord.ApplicationContext,
                                        error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the messageresponse add command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the messageresponse add command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @messageresponse.command(name='remove', description='Removes a chat response')
    @commands.has_permissions(manage_messages=True)
    async def messageresponse_remove(self, ctx: discord.ApplicationContext,
                                     message: Option(str, description='The message to remove the response for',
                                                     required=True)):
        """
        Removes a chat response
        
        :param ctx: The context of the command
        :param message: The message to remove the response for
        
        :type ctx: discord.ApplicationContext
        :type message: str
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')
        original_message = message

        message = message.replace("'", "''").lower()

        if sql.select(elements=['message', 'response'], table='message_responses',
                      where=f"guild_id = '{ctx.guild.id}' AND message = '{message}'"):
            sql.delete(table='message_responses', where=f"guild_id = '{ctx.guild.id}' AND message = '{message}'")
        else:
            await ctx.respond(f'No response for `{original_message}` exists', ephemeral=True)
            return

        await ctx.respond(f'Response for `{original_message}` removed')

    @messageresponse_remove.error
    async def messageresponse_remove_error(self, ctx: discord.ApplicationContext,
                                           error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the messageresponse remove command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the messageresponse remove command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @messageresponse.command(name='list', description='Lists all chat responses')
    async def messageresponse_list(self, ctx: discord.ApplicationContext):
        """
        Lists all chat responses
        
        :param ctx: The context of the command
        
        :type ctx: discord.ApplicationContext
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        if not sql.select(elements=['message', 'response'], table='message_responses',
                          where=f"guild_id = '{ctx.guild.id}'"):
            await ctx.respond('No responses found', ephemeral=True)
            return

        await ctx.interaction.response.defer()

        embed = discord.Embed(title=f'Message Responses for the server {ctx.guild.name}', colour=discord.Colour.green())
        responses = sql.select(elements=['message', 'response'], table='message_responses',
                               where=f"guild_id = '{ctx.guild.id}'")
        for response in responses:
            embed.add_field(name=f'Message: {response[0]}', value=f'Response: {response[1]}', inline=False)

        try:
            await ctx.respond(embed=embed)
        except discord.HTTPException:
            with open(f'responses_{ctx.guild.id}.txt', 'w') as f:
                for response in responses:
                    f.write(f'Message: {response[0]}\nResponse: {response[1]}\n\n')
            await ctx.respond(file=discord.File(f'responses_{ctx.guild.id}.txt', filename='responses.txt'))
            os.remove(f'responses_{ctx.guild.id}.txt')

    @messageresponse_list.error
    async def messageresponse_list_error(self, ctx: discord.ApplicationContext,
                                         error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the messageresponse list command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        await ctx.respond(
            'An error has occurred while running the messageresponse list command! The owner has been notified.',
            ephemeral=True)
        await inform_owner(self.bot, error)

    @messageresponse.command(name='clear', description='Clears all chat responses')
    @commands.has_permissions(manage_messages=True)
    async def messageresponse_clear(self, ctx: discord.ApplicationContext):
        """
        Clears all chat responses
        
        :param ctx: The context of the command
        
        :type ctx: discord.ApplicationContext
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')
        sql.delete(table='message_responses', where=f"guild_id = '{ctx.guild.id}'")
        await ctx.respond('All responses cleared')

    @messageresponse_clear.error
    async def messageresponse_clear_error(self, ctx: discord.ApplicationContext,
                                          error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the messageresponse clear command
        
        :param ctx: The context of the message
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the messageresponse clear command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @commands.slash_command(name='mute', description='Mutes the user specified', usage='mute <user> <duration>')
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx: discord.ApplicationContext,
                   member: Option(discord.Member, description='The member to be muted', required=True),
                   duration: Option(int,
                                    description='The duration of the mute in minutes. Leave blank for permanent mute',
                                    required=False,
                                    default=None),
                   reason: Option(str, description='The reason for the mute', required=False,
                                  default='No reason provided')):
        """
        Mutes the user specified
        
        :param ctx: The context of where the command was used
        :param member: The member to be muted
        :param duration: The duration of the mute in minutes. Leave blank for permanent mute
        :param reason: The reason for the mute
        
        :type ctx: discord.ApplicationContext
        :type member: discord.Member
        :type duration: int
        :type reason: str
        
        :return: None
        :rtype: None
        """
        # Checks before execution
        if member.id == ctx.author.id:
            await ctx.respond('You cannot mute yourself', ephemeral=True)
            return

        if member.id == self.bot.user.id:
            await ctx.respond('I cannot mute myself', ephemeral=True)
            return

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.respond('You cannot mute a member with the same or higher permissions', ephemeral=True)
            return

        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')  # Get the muted role
        if not muted_role:
            await ctx.interaction.response.defer()
            muted_role = await ctx.guild.create_role(name='Muted')  # Create a muted role if not present
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False,
                                              send_messages=False)  # Set permissions of the muted role

        # Mute the user
        try:
            await member.add_roles(muted_role, reason=reason)  # Add muted role
            await ctx.respond(
                embed=discord.Embed(
                    description=f'{member} has been muted for {reason}. Duration: {duration or "Permanent"}.',
                    colour=discord.Colour.red()))

            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                await member.send(
                    f'You were muted in {ctx.guild.name} for {reason}. Duration: {duration or "Permanent"}.')

            # Wait and unmute if duration is specified
            if duration:
                await asyncio.sleep(duration * 60)

                if muted_role in member.roles:
                    await member.remove_roles(muted_role, reason=reason)

                    await ctx.respond(
                        embed=discord.Embed(description=f'{member} has been unmuted',
                                            colour=discord.Colour.green()))

                    with contextlib.suppress(discord.HTTPException):
                        await member.send(f'You have been unmuted in {ctx.guild.name}')

        except discord.Forbidden:  # Permission error
            await ctx.respond('I do not have enough permissions to perform this action', ephemeral=True)

    @mute.error
    async def mute_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the mute command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond('An error has occurred while running the mute command! The owner has been notified.',
                              ephemeral=True)
            await inform_owner(self.bot, error)

    @commands.slash_command(name='unmute', description='Unmutes the user specified', usage='unmute <user>')
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx: discord.ApplicationContext,
                     member: Option(discord.Member, description='The member to be unmuted', required=True)):
        """
        Unmutes the user specified
        
        :param ctx: The context of where the command was used
        :param member: The member to be unmuted
        
        :type ctx: discord.ApplicationContext
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        # Checks before execution
        if member.id == ctx.author.id:
            await ctx.respond('You cannot unmute yourself', ephemeral=True)
            return

        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')  # Get the muted role
        if not muted_role:
            await ctx.respond('There is no muted role', ephemeral=True)
            return

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.respond('You cannot unmute a member with the same or higher permissions', ephemeral=True)
            return

        # Unmute the user
        try:
            await member.remove_roles(muted_role, reason='Unmuted')  # Remove muted role
            await ctx.respond(
                embed=discord.Embed(description=f'{member} has been unmuted', colour=discord.Colour.green()))
        except discord.Forbidden:  # Permission error
            await ctx.respond('I do not have enough permissions to perform this action', ephemeral=True)

    @unmute.error
    async def unmute_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the unmute command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond('An error has occurred while running the unmute command! The owner has been notified.',
                              ephemeral=True)
            await inform_owner(self.bot, error)

    timeout = SlashCommandGroup('timeout', 'Manage timeouts for users')

    @timeout.command(name='add', description='Timeout a user')
    @commands.has_permissions(moderate_members=True)
    async def timeout_add(self, ctx: discord.ApplicationContext,
                          member: Option(discord.Member, description='The member to be timed out', required=True),
                          minutes: Option(int, description='The duration of the timeout in minutes', required=True),
                          reason: Option(str, description='The reason for the timeout', required=False,
                                         default='No reason')):
        """
        Timeouts the user specified
        
        :param ctx: The context of where the command was used
        :param member: The member to be timed out
        :param minutes: The duration of the timeout in minutes
        :param reason: The reason for the timeout
        
        :type ctx: discord.ApplicationContext
        :type member: discord.Member
        :type minutes: int
        :type reason: str
        
        :return: None
        :rtype: None
        """
        # Checks before execution
        if member.timed_out:
            await ctx.respond(f'{member} is already timed out', ephemeral=True)
            return

        if not minutes:
            await ctx.respond('Mention a value in minutes above 0', ephemeral=True)
            return

        if member.guild_permissions >= ctx.author.guild_permissions:
            await ctx.respond('You cannot timeout this user', ephemeral=True)
            return

        # Timeout the user
        try:
            duration = datetime.timedelta(minutes=minutes)
            await member.timeout_for(duration=duration, reason=reason)

            embed = discord.Embed(
                description=f'{member.mention} has been timed out for {minutes} {"minute" if minutes == 1 else "minutes"}. Reason: {reason}',
                colour=discord.Colour.green()
            )
            await ctx.respond(embed=embed)

            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                await member.send(
                    f'You were timed out in {ctx.guild.name} for {minutes} {"minute" if minutes == 1 else "minutes"}. Reason: {reason}')

        except discord.Forbidden:  # Permission error
            await ctx.respond('I do not have enough permissions to perform this action', ephemeral=True)

    @timeout_add.error
    async def timeout_add_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the timeout add command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the timeout add command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @timeout.command(name='remove', description='Remove a timeout from a user')
    @commands.has_permissions(moderate_members=True)
    async def timeout_remove(self, ctx: discord.ApplicationContext,
                             member: Option(discord.Member, description='The member to be timed out', required=True)):
        """
        Removes a timeout from the user specified
        
        :param ctx: The context of where the command was used
        :param member: The member to be timed out
        
        :type ctx: discord.ApplicationContext
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        # Checks before execution
        if not member.timed_out:
            await ctx.respond(f'{member} is not timed out', ephemeral=True)
            return

        if member.guild_permissions >= ctx.author.guild_permissions:
            await ctx.respond('You cannot remove this user\'s timeout', ephemeral=True)
            return

        # Remove the timeout
        try:
            await member.remove_timeout()
            await ctx.respond(f'{member} has been removed from timeout',
                              colour=discord.Colour.green())
            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                await member.send(
                    f'You were removed from timeout in {ctx.guild.name}.')

        except discord.Forbidden:  # Permission error
            await ctx.respond('I do not have enough permissions to perform this action', ephemeral=True)

    @timeout_remove.error
    async def timeout_remove_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the timeout remove command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have the required permissions to use this command!', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the timeout remove command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    # Code command
    @commands.slash_command(name='code',
                            description='Code for the modules of the bot', usage='code <module>')
    async def code(self, ctx: discord.ApplicationContext,
                   module: Option(str, description='The module to get the code for', required=True,
                                  choices=['context', 'events', 'fun', 'help', 'info', 'internet', 'misc', 'music',
                                           'moderation',
                                           'util', 'owner', 'slash', 'games', 'main', 'keep_alive', 'sql_tools',
                                           'tools', 'ui_components'])
                   ):
        """
        Gets the code for the specified module
        
        :param ctx: The context of where the command was used
        :param module: The module to get the code for
        
        :type ctx: discord.ApplicationContext
        :type module: str
        
        :return: None
        :rtype: None
        """
        try:
            await ctx.respond('https://github.com/SandeepKanekal/b0ssBot -> Source Code',
                              file=discord.File(f'{module}.py', filename=f'{module}.py'))
        except FileNotFoundError:
            await ctx.respond('https://github.com/SandeepKanekal/b0ssBot -> Source Code',
                              file=discord.File(f'cogs/{module}.py', filename=f'{module}.py'))

    @code.error
    async def code_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the code command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        await ctx.respond('An error has occurred while running the code command! The owner has been notified.',
                          ephemeral=True)
        await inform_owner(self.bot, error)

    @commands.slash_command(name='roleinfo', aliases=['role', 'ri'], description='Shows the information of a role',
                            usage='roleinfo <role>')
    async def roleinfo(self, ctx: discord.ApplicationContext,
                       role: Option(discord.Role, desription='The role to get the information of', required=True)):
        """
        Shows the information of a role
        
        :param ctx: The context of where the message was sent
        
        :type ctx: discord.ApplicationContext
        
        :param role: The role to get the information of
        
        :type role: discord.Role
        
        :return: None
        :rtype: None
        """
        # Getting the creation date of the role relative unix time
        created_at = role.created_at.strftime('%Y-%m-%d %H:%M:%S:%f')
        created_at = convert_to_unix_time(created_at)

        # Getting the colour of the role
        rgb_colour = role.colour.to_rgb()  # type: tuple[int, int, int]
        hex_colour = str(role.colour)  # type: str

        # Getting the permissions of the role
        permissions = [permission[0].replace('_', ' ').title() for permission in role.permissions if
                       permission[1]]  # type: list[str]

        embed = discord.Embed(colour=role.colour, timestamp=datetime.datetime.now())
        embed.set_footer(text=f'ID: {role.id}')
        embed.set_thumbnail(url=role.icon or discord.Embed.Empty)
        embed.set_author(name=role.name, icon_url=role.icon or role.guild.icon or discord.Embed.Empty)

        embed.add_field(name='Members', value=str(len(role.members)), inline=True)
        embed.add_field(name='Creation Date', value=created_at, inline=True)
        embed.add_field(name='Colour',
                        value=f'**RGB:** {rgb_colour[0]}, {rgb_colour[1]}, {rgb_colour[2]}\n**Hex Code:** {hex_colour}',
                        inline=True)
        embed.add_field(name='Mentionable', value=str(role.mentionable), inline=True)
        embed.add_field(name='Position', value=str(role.position), inline=True)
        embed.add_field(name='Hoisted', value=str(role.hoist), inline=True)
        embed.add_field(name='Permissions', value=', '.join(permissions) or 'None', inline=False)

        await ctx.respond(embed=embed)

    @roleinfo.error
    async def roleinfo_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Handles errors for the roleinfo command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        await ctx.respond('An error has occurred while running the roleinfo command! The owner has been notified.',
                            ephemeral=True)
        await inform_owner(self.bot, error)
    
    invert = SlashCommandGroup('invert', 'Invert images of users or from URLs')

    @invert.command(name='user', description='Inverts the avatar of a user')
    async def invert_user(self, ctx: discord.ApplicationContext, member: Option(discord.Member, 'The user\' avatar to invert', required=False, default=None)):
        """
        Inverts the avatar of a user
        
        :param ctx: The context of where the message was sent
        :param member: The user to invert the avatar of
        
        :type ctx: discord.ApplicationContext
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        await ctx.interaction.response.defer()

        member = member or ctx.author  # type: discord.Member
        request_url = member.display_avatar  # type: str

        # Saving the image
        response = requests.get(request_url)  # type: requests.Response
        with open(f'image_{ctx.author.id}.png', 'wb') as f:
            f.write(response.content)

        # Inverting the image
        image = Image.open(f'image_{ctx.author.id}.png')
        invert = ImageChops.invert(image.convert('RGB'))
        invert.save(f'{member.id}_inverted.png')

        # Checking if file size is greater than 8mb
        if os.path.getsize(f'{member.id}_inverted.png') > 8000000:
            await ctx.respond('Image is too large to send', ephemeral=True)
            os.remove(f'image_{ctx.author.id}.png')
            os.remove(f'{member.id}_inverted.png')
            return

        await ctx.respond(file=discord.File(f'{member.id}_inverted.png', 'invert.png'))

        # Removing the files
        os.remove(f'image_{ctx.author.id}.png')
        os.remove(f'{member.id}_inverted.png')
    
    @invert_user.error
    async def invert_user_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Handles errors for the invert_user command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        await ctx.respond('An error has occurred while running the invert_user command! The owner has been notified.',
                            ephemeral=True)
        await inform_owner(self.bot, error)
    
    @invert.command(name='url', description='Inverts the from a URL')
    async def invert_url(self, ctx: discord.ApplicationContext, url: Option(str, 'The URL to get the image from', required=True)):
        """
        Inverts the image from a URL
        
        :param ctx: The context of where the message was sent
        :param url: The URL to invert the image from
        
        :type ctx: discord.ApplicationContext
        :type url: str
        
        :return: None
        :rtype: None
        """
        await ctx.interaction.response.defer()

        # Saving the image
        response = requests.get(url)  # type: requests.Response
        with open(f'image_{ctx.author.id}.png', 'wb') as f:
            f.write(response.content)

        # Inverting the image
        image = Image.open(f'image_{ctx.author.id}.png')
        invert = ImageChops.invert(image.convert('RGB'))
        invert.save(f'inverted_{ctx.author.id}.png')

        # Checking if file size is greater than 8mb
        if os.path.getsize(f'inverted_{ctx.author.id}.png') > 8000000:
            await ctx.respond('Image is too large to send', ephemeral=True)
            os.remove(f'image_{ctx.author.id}.png')
            os.remove(f'inverted_{ctx.author.id}.png')
            return

        await ctx.respond(file=discord.File(f'inverted_{ctx.author.id}.png', 'invert.png'))

        # Removing the files
        os.remove(f'image_{ctx.author.id}.png')
        os.remove(f'inverted_{ctx.author.id}.png')
    
    @invert_url.error
    async def invert_url_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Handles errors for the invert_url command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, (ConnectionError, requests.exceptions.MissingSchema, UnidentifiedImageError)):
            await ctx.respond('Invalid URL', ephemeral=True)
            with contextlib.suppress(FileNotFoundError):
                os.remove(f'image_{ctx.author.id}.png')
                os.remove(f'inverted_{ctx.author.id}.png')
        else:
            await ctx.respond('An error has occurred while running the invert command! The owner has been notified.',
                              ephemeral=True)
            await inform_owner(self.bot, error)

    @commands.slash_command(name='embed', description='Make an embed! Visit https://imgur.com/a/kbFJCL1 for more info')
    async def embed(self, ctx: discord.ApplicationContext,
                    channel: Option(discord.TextChannel, description='The channel to send the embed in',
                                    required=True)):
        """
        Send an embed to the channel specified.

        :param ctx: The context of the command.
        :param channel: The channel to send the embed to

        :type ctx: discord.ApplicationContext
        :type channel: discord.TextChannel

        :return: None
        :rtype: None        
        """
        embed = discord.Embed(title='This is the title', description='This is the description')
        await ctx.respond(content='This is how the embed will look!', embed=embed,
                          view=EmbedView(ctx.author.id, embed, channel, timeout=None))

    @embed.error
    async def embed_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the embed command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, discord.HTTPException):
            await ctx.respond('URL provided is invalid', ephemeral=True)
        else:
            await ctx.respond('An error has occurred while running the embed command! The owner has been informed.',
                              ephemeral=True)
            await inform_owner(self.bot, error)

    @commands.slash_command(name='datetime', desription='Get a dynamic datetime display string',
                            usage='datetime <year> <month> <day> <hour> <minute> <second>')
    async def datetime(self, ctx: discord.ApplicationContext,
                       year: Option(int, description='Year of the datetime (cannot be before 1970)', required=True),
                       month: Option(int, description='Month of the datetime', required=True,
                                     choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]),
                       day: Option(int, description='Day of the datetime', required=True),
                       hour: Option(int, description='Hour of the datetime', required=True),
                       minute: Option(int, description='Minute of the datetime', required=True),
                       second: Option(int, description='Second of the datetime', required=True),
                       display_type: Option(str, description='Type of the datetime display', required=True,
                                            choices=['short time', 'long time', 'short date', 'long date',
                                                     'long date with short time',
                                                     'long date with day of the week and short time', 'relative'])):
        """
        Gets a dynamic datetime display string

        :param ctx: command context
        :param year: year of the datetime
        :param month: month of the datetime
        :param day: day of the datetime
        :param hour: hour of the datetime
        :param minute: minute of the datetime
        :param second: second of the datetime
        :param display_type: type of the datetime display

        :type ctx: discord.ApplicationContext
        :type year: int
        :type month: int
        :type day: int
        :type hour: int
        :type minute: int
        :type second: int`
        :type display_type: str

        :return: None
        :rtype: None
        """
        date_time = datetime.datetime(year, month, day, hour, minute, second).strftime(
            '%Y-%m-%d %H:%M:%S:%f')

        # Getting the right format
        fmt: str = ''
        if display_type == 'short time':
            fmt = 't'
        elif display_type == 'long time':
            fmt = 'T'
        elif display_type == 'short date':
            fmt = 'd'
        elif display_type == 'long date':
            fmt = 'D'
        elif display_type == 'long date with short time':
            fmt = 'f'
        elif display_type == 'long date with day of the week and short time':
            fmt = 'F'
        elif display_type == 'relative':
            fmt = 'R'

        await ctx.respond(
            f'{convert_to_unix_time(date_time, fmt)}\nPaste this and send to get the same result: \\{convert_to_unix_time(date_time, fmt)}')

    @datetime.error
    async def datetime_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the datetime command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError

        :return: None
        :rtype: None
        """
        if isinstance(error, ValueError):
            await ctx.respond('Invalid datetime provided', ephemeral=True)
        elif isinstance(error, OverflowError):
            await ctx.respond('Time provided is too far off in the past/future', ephemeral=True)
        else:
            await ctx.respond('An error has occurred while running the datetime command! The owner has been notified.',
                              ephemeral=True)
            await inform_owner(self.bot, error)

    verify = SlashCommandGroup('verify', 'Manage verification systems')

    @verify.command(name='add', description='Create a verifying message')
    @commands.has_permissions(manage_guild=True)
    async def verify_add(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel,
                                                                                description='The channel to send the verification message to',
                                                                                required=True),
                         verified_role: Option(discord.Role, description='The role to add when a user is verified',
                                               required=True),
                         unverified_role: Option(discord.Role, description='The role to remove when a user verifies',
                                                 required=False, default=None)):
        """
        Creates a verifying message
        
        :param ctx: The context of where the message was sent
        :param channel: The channel to send the verification message to
        :param verified_role: The role to add when a user is verified
        :param unverified_role: The role to remove when a user verifies
        
        :type ctx: discord.ApplicationContext
        :type channel: discord.TextChannel
        :type verified_role: discord.Role
        :type unverified_role: discord.Role
        
        :return: None
        :rtype: None
        """
        await ctx.interaction.response.defer()

        sql = SQL('b0ssbot')

        # Check if a verification system already exists
        if sql.select(['*'], 'verifications', where=f"guild_id = '{ctx.guild.id}'"):
            await ctx.respond('Verification already exists', ephemeral=True)
            return

        # Creating embed
        embed = discord.Embed(title='SUCCESSFUL', description='Verification system has been successfully created.',
                              colour=0x21ba5e)
        embed.add_field(name='Channel', value=channel.mention)
        embed.add_field(name='Verified role', value=verified_role.mention, inline=True)
        embed.add_field(name='Unverified role', value=unverified_role.mention if unverified_role else 'None',
                        inline=True)

        # Sending the verify-message and adding the reaction
        msg = await channel.send(embed=discord.Embed(description='Please verify yourself to get access to the server.',
                                                     colour=discord.Colour.teal()))
        await msg.add_reaction('✅')

        # Insert into database
        sql.insert('verifications', ['message_id', 'role_id', 'unverified_role_id', 'channel_id', 'guild_id'],
                   [f"'{msg.id}'", f"'{verified_role.id}'", f"'{unverified_role.id}'" if unverified_role else "'None'",
                    f"'{channel.id}'", f"'{ctx.guild.id}'"])

        await ctx.respond(embed=embed)

    @verify_add.error
    async def verify_add_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the verify_add command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have permission to use this command', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the verify add command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @verify.command(name='remove', description='Remove a verifying message')
    @commands.has_permissions(manage_guild=True)
    async def verify_remove(self, ctx: discord.ApplicationContext):
        """
        Removes a verifying message
        
        :param ctx: The context of where the message was sent
        
        :type ctx: discord.ApplicationContext
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        # Check if verification does not exist
        if not sql.select(['*'], 'verifications', where=f"guild_id = '{ctx.guild.id}'"):
            await ctx.respond('Verification does not exist', ephemeral=True)
            return

        # Remove from database
        sql.delete('verifications', where=f"guild_id = '{ctx.guild.id}'")

        await ctx.respond('Verification has been removed')

    @verify_remove.error
    async def verify_remove_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the verify remove command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have permission to use this command', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the verify remove command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @verify.command(name='update', description='Update the verification system for the server')
    @commands.has_permissions(manage_guild=True)
    async def verify_update(self, ctx: discord.ApplicationContext,
                            verified_role: Option(discord.Role, description='The role to add when a user is verified',
                                                  required=False, default=None),
                            unverified_role: Option(discord.Role, description='The role to remove when a user verifies',
                                                    required=False, default=None)):
        """
        Updates the verification system for the server
        
        :param ctx: The context of where the message was sent
        :param verified_role: The role to add when a user is verified
        :param unverified_role: The role to remove when a user verifies
        
        :type ctx: discord.ApplicationContext
        :type verified_role: discord.Role
        :type unverified_role: discord.Role
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        # Check iff verification does not exist
        if not sql.select(['*'], 'verifications', where=f"guild_id = '{ctx.guild.id}'"):
            await ctx.respond('Verification does not exist', ephemeral=True)
            return

        # Check if changes were made
        if not verified_role and not unverified_role:
            await ctx.respond('No changes made!', ephemeral=True)
            return

        # Update database
        if verified_role:
            sql.update('verifications', 'role_id', f"'{verified_role.id}'", where=f"guild_id = '{ctx.guild.id}'")

        if unverified_role:
            sql.update('verifications', 'unverified_role_id', f"'{unverified_role.id}'",
                       where=f"guild_id = '{ctx.guild.id}'")

        await ctx.respond('Verification has been updated')

    @verify_update.error
    async def verify_update_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the verify update command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have permission to use this command', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the verify update command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @commands.slash_command(name='history', description='View your or another user\'s internet search history')
    async def history(self, ctx: discord.ApplicationContext,
                      member: Option(discord.Member, description='The user to get the history of', required=False,
                                     default=None)):
        """
        View your or another user\'s internet search history
        
        :param ctx: The context of where the message was sent
        :param member: The user to get the history of
        
        :type ctx: discord.ApplicationContext
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        member = member or ctx.author

        sql = SQL('b0ssbot')

        # Check if the user has any history
        if not sql.select(['*'], 'history', where=f"member_id = '{member.id}' AND guild_id = '{ctx.guild.id}'"):
            await ctx.respond(f'{member.mention} has no history', ephemeral=True)
            return

        await ctx.interaction.response.defer()

        # Create embed
        embed = discord.Embed(title=f'{member.display_name}\'s history', description='',
                              colour=discord.Colour.blurple())
        embed.set_footer(text=f'{member.display_name}\'s History', icon_url=member.display_avatar)

        history = list(reversed(sql.select(['type', 'query', 'timestamp'], 'history',
                                           f'member_id = \'{member.id}\' AND guild_id = \'{ctx.guild.id}\'')))[:50]

        for h in reversed(history):
            query = h[1].replace("''", "'")
            embed.description += f'{h[0]}: {query} - <t:{h[2]}:R>\n'

        embed.description = embed.description[:-1]

        await ctx.respond(embed=embed)

    serverjoin = SlashCommandGroup('serverjoin', 'Roles to be added when a member/bot joins the server')

    @serverjoin.command(name='add', description='Add a role to be added when a member/bot joins the server')
    @commands.has_permissions(manage_roles=True)
    async def serverjoin_add(self, ctx: discord.ApplicationContext,
                             user: Option(str, description='The type of user', required=True,
                                          choices=['member', 'bot', 'all']),
                             role: Option(discord.Role, description='The role to add', required=True)):
        """
        Add a role to be added when a member/bot joins the server
        
        :param ctx: The context of where the message was sent
        :param user: The type of user
        :param role: The role to add
        
        :type ctx: discord.ApplicationContext
        :type user: str
        :type role: discord.Role
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        # Check if serverjoin already exists
        roles = sql.select(['member_role_id', 'bot_role_id'], 'serverjoin', where=f"guild_id = '{ctx.guild.id}'")
        if roles and not roles[0][0] and not roles[0][1]:
            await ctx.respond('Server join already exists, use the update subcommand instead', ephemeral=True)
            return

        # Update database
        if user == 'all':
            sql.insert('serverjoin', ['guild_id', 'member_role_id', 'bot_role_id'],
                       [f"'{ctx.guild.id}'", f"'{role.id}'", f"'{role.id}'"])
        else:
            sql.insert('serverjoin', ['guild_id', f'{user}_role_id'], [f"'{ctx.guild.id}'", f"'{role.id}'"])

        await ctx.respond('Role has been added')

    @serverjoin_add.error
    async def serverjoin_add_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the serverjoin add command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have permission to use this command', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the serverjoin add command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @serverjoin.command(name='remove', description='Remove the serverjoin configurations')
    @commands.has_permissions(manage_roles=True)
    async def serverjoin_remove(self, ctx: discord.ApplicationContext):
        """
        Remove a role to be added when a member/bot joins the server
        
        :param ctx: The context of where the message was sent
        
        :type ctx: discord.ApplicationContext
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        # Check if serverjoin even exists
        if not sql.select(['*'], 'serverjoin', where=f"guild_id = '{ctx.guild.id}'"):
            await ctx.respond('Server join does not exist', ephemeral=True)
            return

        # Remove from database
        sql.delete('serverjoin', where=f"guild_id = '{ctx.guild.id}'")

        await ctx.respond('Role has been removed')

    @serverjoin_remove.error
    async def serverjoin_remove_error(self, ctx: discord.ApplicationContext,
                                      error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the serverjoin remove command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have permission to use this command', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the serverjoin remove command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @serverjoin.command(name='update', description='Update the role to be added when a member/bot joins the server')
    @commands.has_permissions(manage_roles=True)
    async def serverjoin_update(self, ctx: discord.ApplicationContext,
                                user: Option(str, description='The type of user', required=True,
                                             choices=['member', 'bot', 'all']),
                                role: Option(discord.Role, description='The role to add', required=True)):
        """
        Update the role to be added when a member/bot joins the server
        
        :param ctx: The context of where the message was sent
        :param user: The type of user
        :param role: The role to add
        
        :type ctx: discord.ApplicationContext
        :type user: str
        :type role: discord.Role
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        # Check if serverjoin even exists
        if not sql.select(['*'], 'serverjoin', where=f"guild_id = '{ctx.guild.id}'"):
            await ctx.respond('Server join does not exist', ephemeral=True)
            return

        # Update database
        if user == 'all':
            sql.update('serverjoin', 'bot_role_id', f"'{role.id}'", where=f"guild_id = '{ctx.guild.id}'")
            sql.update('serverjoin', 'member_role_id', f"'{role.id}'", where=f"guild_id = '{ctx.guild.id}'")
        else:
            sql.update('serverjoin', f'{user}_role_id', f"'{role.id}'", where=f"guild_id = '{ctx.guild.id}'")

        await ctx.respond('Role has been updated')

    @serverjoin_update.error
    async def serverjoin_update_error(self, ctx: discord.ApplicationContext,
                                      error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the serverjoin update command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        if isinstance(error.original, commands.MissingPermissions):
            await ctx.respond('You do not have permission to use this command', ephemeral=True)
        else:
            await ctx.respond(
                'An error has occurred while running the serverjoin update command! The owner has been notified.',
                ephemeral=True)
            await inform_owner(self.bot, error)

    @serverjoin.command(name='list', description='List the roles to be added when a member/bot joins the server')
    async def serverjoin_list(self, ctx: discord.ApplicationContext):
        """
        List the roles to be added when a member/bot joins the server
        
        :param ctx: The context of where the message was sent
        
        :type ctx: discord.ApplicationContext
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        # Check if serverjoin even exists
        if not sql.select(['*'], 'serverjoin', where=f"guild_id = '{ctx.guild.id}'"):
            await ctx.respond('Server join does not exist', ephemeral=True)
            return

        # Get the roles
        roles = sql.select(['member_role_id', 'bot_role_id'], 'serverjoin', where=f"guild_id = '{ctx.guild.id}'")

        member_role = discord.utils.get(ctx.guild.roles, id=int(roles[0][0])) if roles[0][0] else None
        bot_role = discord.utils.get(ctx.guild.roles, id=int(roles[0][1])) if roles[0][1] else None

        # Create embed
        embed = discord.Embed(title='Server Join Roles',
                              description=f'Members: {member_role.mention if member_role else member_role}\nBots: {bot_role.mention if bot_role else bot_role}',
                              color=discord.Colour.blurple())

        await ctx.respond(embed=embed)

    @serverjoin_list.error
    async def serverjoin_list_error(self, ctx: discord.ApplicationContext,
                                    error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the serverjoin list command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        await ctx.respond(
            'An error has occurred while running the serverjoin list command! The owner has been notified.',
            ephemeral=True)
        await inform_owner(self.bot, error)
    
    banner = SlashCommandGroup('banner', 'Get banner\'s for users or the guild')

    @banner.command(name='user', description='Shows the specified user\'s banner')
    async def banner_user(self, ctx: discord.ApplicationContext, member: Option(discord.Member, description='The member to fetch the banner of', required=False, default=None)):
        """
        Shows the specified user's banner

        :param ctx: The command context
        :param member: The member to get the banner of

        :type ctx: discord.ApplicationContext
        :type member: discord.Member

        :return: None
        :rtype: None
        """
        member = member or ctx.author  # type: discord.Member
        
        req = await self.bot.http.request(discord.http.Route("GET", "/users/{uid}", uid=member.id))
        
        banner_id = req['banner']

        if banner_id is None:
            await ctx.respond('This user has no banner', ephemeral=True)
            return
        
        url = f'https://cdn.discordapp.com/banners/{member.id}/{banner_id}?size=1024'

        embed = discord.Embed(colour=member.colour)
        embed.set_image(url=url)
        embed.set_author(name=member.name, icon_url=member.display_avatar)
        embed.add_field(name='Download this image', value=f'[Click Here]({url})')
        await ctx.respond(embed=embed)
    
    @banner_user.error
    async def banner_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the banner command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError

        :return: None
        :rtype: None
        """
        await ctx.respond('An error has occurred while running the banner command! The owner has been notified.', ephemeral=True)
        await inform_owner(self.bot, error)
    
    @banner.command(name='guild', description='Shows the guild\'s banner')
    async def banner_guild(self, ctx: discord.ApplicationContext):
        """
        Shows the guild's banner

        :param ctx: The command context

        :type ctx: discord.ApplicationContext

        :return: None
        :rtype: None
        """
        req = await self.bot.http.request(discord.http.Route("GET", "/guilds/{gid}", gid=ctx.guild.id))
        
        banner_id = req['banner']

        if banner_id is None:
            await ctx.respond('This guild has no banner', ephemeral=True)
            return
        
        url = f'https://cdn.discordapp.com/banners/{ctx.guild.id}/{banner_id}?size=1024'

        embed = discord.Embed(colour=ctx.guild.colour)
        embed.set_image(url=url)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.add_field(name='Download this image', value=f'[Click Here]({url})')
        await ctx.respond(embed=embed)
    
    @banner_guild.error
    async def banner_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the banner command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError

        :return: None
        :rtype: None
        """
        await ctx.respond('An error has occurred while running the banner command! The owner has been notified.', ephemeral=True)
        await inform_owner(self.bot, error)


def setup(bot: commands.Bot):
    """
    Loads the Cog.
    
    :param bot: The bot object
    
    :type bot: commands.Bot
    
    :return: None
    :rtype: None
    """
    bot.add_cog(Slash(bot))

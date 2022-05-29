import contextlib
import discord
import datetime
import requests
import os
import asyncio
from discord.ext import commands
from discord.commands import Option
from tools import convert_to_unix_time
from sql_tools import SQL
from googleapiclient.discovery import build


class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='prefix', description='Change the prefix of the bot', usage='prefix <new_prefix>')
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, new_prefix: Option(str, descrciption='The new prefix', required=True)):
        if len(new_prefix) > 2:
            await ctx.respond('Prefix must be 2 characters or less')
            return

        sql = SQL('b0ssbot')
        sql.update(table='prefixes', column='prefix', value=f'\'{new_prefix}\'', where=f'guild_id=\'{ctx.guild.id}\'')
        await ctx.respond(f'Prefix changed to **{new_prefix}**')

    @prefix.error
    async def prefix_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    @commands.slash_command(name='userinfo',
                            description='Shows the mentioned user\'s information. Leave it blank to get your information',
                            usage='userinfo <member>')
    async def userinfo(self, ctx,
                       member: Option(discord.Member, description='The user to get info on', required=False,
                                      default=None)):
        if member is None:
            member = ctx.author

        # Getting the dates
        joined_at = member.joined_at.strftime('%Y-%m-%d %H:%M:%S:%f')
        registered_at = member.created_at.strftime('%Y-%m-%d %H:%M:%S:%f')

        joined_at = convert_to_unix_time(joined_at)
        registered_at = convert_to_unix_time(registered_at)

        embed = discord.Embed(colour=member.colour)
        embed.set_author(name=str(member), icon_url=str(member.avatar)) if member.avatar else embed.set_author(
            name=str(member), icon_url=str(member.default_avatar))
        embed.add_field(name='Display Name', value=member.mention, inline=True)
        embed.add_field(name='Top Role', value=member.top_role.mention, inline=True)
        if len(member.roles) > 1:
            role_string = ' '.join([r.mention for r in member.roles][1:])
            embed.add_field(name=f'Roles[{len(member.roles) - 1}]', value=role_string, inline=False)
        else:
            embed.add_field(name='Roles[1]', value=member.top_role.mention, inline=False)
        embed.set_thumbnail(url=str(member.avatar)) if member.avatar else embed.set_thumbnail(
            url=str(member.default_avatar))
        embed.add_field(name='Joined', value=joined_at, inline=True)
        embed.add_field(name='Registered', value=registered_at, inline=True)
        embed.set_footer(text=f'ID: {member.id}')
        embed.timestamp = datetime.datetime.now()
        await ctx.respond(embed=embed)

    @userinfo.error
    async def userinfo_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    @commands.slash_command(name='avatar', description='Shows the specified user\'s avatar', usage='avatar <user>')
    async def avatar(self, ctx,
                     member: Option(discord.Member, description='User to get the avatar of', required=False,
                                    default=None)):
        if member is None:
            member = ctx.author
        # Response embed
        embed = discord.Embed(colour=member.colour)
        embed.set_author(name=member.name, icon_url=member.avatar or member.default_avatar)
        embed.set_image(url=member.avatar or member.default_avatar)
        embed.add_field(name='Download this image', value=f'[Click Here]({member.avatar or member.default_avatar})')
        await ctx.respond(embed=embed)

    @avatar.error
    async def avatar_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    @commands.slash_command(name='youtubenotification', description='Configure youtube notifications for the server',
                            usage='youtubenotification <mode> <text_channel_id> <youtube_channel_id>')
    @commands.has_permissions(manage_guild=True)
    async def youtubenotification(self, ctx,
                                  mode: Option(str, description='Mode for configuration',
                                               choices=['add', 'remove', 'view'], required=True),
                                  text_channel_id: Option(str, description='Text channel ID',
                                                          required=False, default=None),
                                  youtube_channel: Option(str, description='Youtube channel', required=False,
                                                          default=None)):
        # sourcery no-metrics

        sql = SQL('b0ssbot')
        youtube = build('youtube', 'v3', developerKey=os.getenv('youtube_api_key'))
        text_channel = discord.utils.get(ctx.guild.text_channels, id=int(text_channel_id)) if text_channel_id else None

        if mode == 'add':

            if text_channel is None:
                await ctx.respond('Error: Text channel not found', ephemeral=True)
                return

            youtube_channel_id = requests.get(
                f"https://www.googleapis.com/youtube/v3/search?part=id&q={youtube_channel.split('/c/')[1]}&type=channel&key={os.getenv('youtube_api_key')}").json()[
                'items'][0]['id']['channelId'] if '/c/' in youtube_channel else youtube_channel.split('/channel/')[1]

            if sql.select(elements=['*'], table='youtube',
                          where=f"guild_id='{ctx.guild.id}' and channel_id = '{youtube_channel_id}'"):
                await ctx.respond('Channel already added', ephemeral=True)
                return

            channel = youtube.channels().list(id=youtube_channel_id, part='snippet, contentDetails').execute()
            latest_video_id = youtube.playlistItems().list(
                playlistId=channel['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
                part='contentDetails').execute()['items'][0]['contentDetails']['videoId']
            channel_name = channel['items'][0]['snippet']['title'].replace("'", "''")

            sql.insert(table='youtube',
                       columns=['guild_id', 'text_channel_id', 'channel_id', 'channel_name', 'latest_video_id'],
                       values=[f"'{ctx.guild.id}'", f"'{text_channel.id}'", f"'{channel['items'][0]['id']}'",
                               f"'{channel_name}'", f"'{latest_video_id}'"])
            await ctx.respond(
                f'NOTE: This command requires **Send Webhooks** to be enabled in {text_channel.mention}',
                embed=discord.Embed(
                    colour=discord.Colour.green(),
                    description=f'YouTube notifications for the channel **[{channel["items"][0]["snippet"]["title"]}](https://youtube.com/channel/{channel["items"][0]["id"]})** will now be sent to {text_channel.mention}').set_thumbnail(
                    url=channel["items"][0]["snippet"]["thumbnails"]["high"]["url"]).set_footer(
                    text='Use the command again to update the channel')
            )

        elif mode == 'remove':
            youtube_channel_id = requests.get(
                f"https://www.googleapis.com/youtube/v3/search?part=id&q={youtube_channel.split('/c/')[1]}&type=channel&key={os.getenv('youtube_api_key')}").json()[
                'items'][0]['id']['channelId'] if '/c/' in youtube_channel else youtube_channel.split('/channel/')[1]
            channel = youtube.channels().list(id=youtube_channel_id, part='snippet, contentDetails').execute()

            if not sql.select(elements=['*'], table='youtube',
                              where=f"guild_id='{ctx.guild.id}' and channel_id = '{youtube_channel_id}'"):
                await ctx.respond('Channel not added', ephemeral=True)
                return

            text_channel_id = int(sql.select(elements=['text_channel_id'], table='youtube',
                                             where=f'guild_id = \'{ctx.guild.id}\' AND channel_id = \'{youtube_channel_id}\'')[
                                      0][0])
            sql.delete(table='youtube',
                       where=f'guild_id = \'{ctx.guild.id}\' AND channel_id = \'{channel["items"][0]["id"]}\'')
            text_channel = discord.utils.get(ctx.guild.text_channels, id=text_channel_id)
            await ctx.respond(embed=discord.Embed(
                colour=discord.Colour.green(),
                description=f'YouTube notifications for the channel **[{channel["items"][0]["snippet"]["title"]}](https://youtube.com/channel{channel["items"][0]["id"]})** will no longer be sent to {text_channel.mention}').set_thumbnail(
                url=channel["items"][0]["snippet"]["thumbnails"]["high"]["url"]))

        else:
            if youtube_channel:
                channel_id = requests.get(
                    f"https://www.googleapis.com/youtube/v3/search?part=id&q={youtube_channel.split('/c/')[1]}&type=channel&key={os.getenv('youtube_api_key')}").json()[
                    'items'][0]['id']['channelId'] if '/c/' in youtube_channel else youtube_channel.split('/channel/')[
                    1]
            else:
                channel_id = None
            where = f"guild_id = '{ctx.guild.id}' AND channel_id = '{channel_id}'" if channel_id else f"guild_id = '{ctx.guild.id}'"
            channels = sql.select(elements=['channel_name', 'channel_id', 'text_channel_id'], table='youtube',
                                  where=where)
            if not channels:
                await ctx.respond('No channels are currently set up for notifications', ephemeral=True)
                return
            embed = discord.Embed(
                description='',
                colour=discord.Colour.dark_red()
            )
            for index, channel in enumerate(channels):
                text_channel = discord.utils.get(ctx.guild.text_channels, id=int(channel[2]))
                embed.description += f'{index + 1}. **[{channel[0]}](https://youtube.com/channel/{channel[1]})** in {text_channel.mention}\n'
            if ctx.guild.icon:
                embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
            else:
                embed.set_author(name=ctx.guild.name)
            embed.set_thumbnail(
                url='https://yt3.ggpht.com/584JjRp5QMuKbyduM_2k5RlXFqHJtQ0qLIPZpwbUjMJmgzZngHcam5JMuZQxyzGMV5ljwJRl0Q=s176-c-k-c0x00ffffff-no-rj')
            await ctx.respond(embed=embed)

    @youtubenotification.error
    async def youtubenotification_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    # Hourlyweather command
    @commands.slash_command(name='hourlyweather', aliases=['hw'],
                            description='Configure monitored weather locations for the server',
                            usage='hourlyweather <mode> <channel_id> <location>')
    @commands.has_permissions(manage_guild=True)
    async def hourlyweather(self, ctx,
                            mode: Option(str, description='The mode to use', choices=['add', 'remove', 'view'],
                                         required=True),
                            channel_id: Option(str, description='The text channel to configure',
                                               required=False, default=None),
                            location: Option(str, description='The location to be monitored', required=False,
                                             default=None)):
        # sourcery no-metrics
        sql = SQL('b0ssbot')
        channel = discord.utils.get(ctx.guild.text_channels, id=int(channel_id)) if channel_id else None

        if mode == 'add':

            if channel is None:
                await ctx.respond('The channel ID is invalid', ephemeral=True)
                return

            if not location:
                await ctx.respond('Please specify a location', ephemeral=True)
                return

            original_location = location
            location = location.lower().replace("'", "''")  # Make sure the location is lowercase

            if channel is None or location is None:  # If the channel or location is not specified
                await ctx.respond('Please provide a channel and location', ephemeral=True)
                return

            with contextlib.suppress(IndexError):
                if location == \
                        sql.select(elements=['location'], table='hourlyweather', where=f"guild_id = '{ctx.guild.id}'")[
                            0][0]:  # If the location is already in the database
                    sql.update(table='hourlyweather', column='channel_id', value=f'{channel.id}',
                               where=f"guild_id = '{ctx.guild.id}'")  # Update the channel
                    await ctx.respond(
                        embed=discord.Embed(description=f'Updated the hourly weather channel to {channel.mention}',
                                            colour=discord.Colour.green()))  # Send a success embed
                    return

            sql.insert(table='hourlyweather', columns=['guild_id', 'channel_id', 'location'],
                       values=[f"'{ctx.guild.id}'", f"'{channel.id}'", f"'{location}'"])  # Insert the location
            await ctx.respond(embed=discord.Embed(description=f'Added hourly weather for {original_location}',
                                                  colour=discord.Colour.green()))  # Send a success embed

        elif mode == 'remove':

            original_location = location

            if not location:
                await ctx.respond('Please specify a location', ephemeral=True)
                return

            if sql.select(elements=['*'], table='hourlyweather', where=f"guild_id = '{ctx.guild.id}'"):
                location = location.lower().replace("'", "''")  # Make sure the location is lowercase
                sql.delete(table='hourlyweather', where=f"guild_id = '{ctx.guild.id}' AND location = '{location}'")
                await ctx.respond(embed=discord.Embed(description=f'Removed hourly weather for {original_location}',
                                                      colour=discord.Colour.green()))  # Send a success embed
            else:
                await ctx.respond(f'{original_location} is not monitored', ephemeral=True)

        elif mode == 'view':
            response = sql.select(elements=['location', 'channel_id'], table='hourlyweather',
                                  where=f"guild_id = '{ctx.guild.id}'")  # Get the locations and channels
            if not response:
                await ctx.respond('No locations are monitored', ephemeral=True)
                return

            embed = discord.Embed(title=f'Hourly Weather Locations for {ctx.guild.name}', description='',
                                  colour=discord.Colour.blue())
            for item in response:  # Append each location to embed.description along with the text channel
                channel = discord.utils.get(ctx.guild.text_channels, id=int(item[1]))
                location = item[0].replace("''", "'")
                embed.description += f'{location} in {channel.mention}\n'

            await ctx.respond(embed=embed)

    @hourlyweather.error
    async def hourlyweather_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    # Warn command
    @commands.slash_command(name='warn',
                            description='Configure warns for the user',
                            usage='warn <subcommand> <user> <reason>')
    @commands.has_permissions(manage_guild=True)
    async def warn(self, ctx,
                   subcommand: Option(str, description='The subcommand to use', choices=['add', 'remove', 'view'],
                                      required=True),
                   member: Option(discord.Member, description='The member to warn', required=True),
                   reason: Option(str, description='The reason for the warning', required=False,
                                  default='No reason provided')):
        # sourcery no-metrics
        sql = SQL('b0ssbot')

        if subcommand == 'add':
            if member == ctx.author:
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

        elif subcommand == 'view':
            warn = sql.select(elements=['member_id', 'warns', 'reason'], table='warns',
                              where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
            if not warn:
                await ctx.respond(f'{member.mention} has no warns', ephemeral=True)
                return

            embed = discord.Embed(
                title=f'{member} has {warn[0][1]} {("warn" if warn[0][1] == 1 else "warns")}',
                description=f'Reason for latest warn: **{warn[0][2][warn[0][1] - 1]}**',
                colour=discord.Colour.red()
            ).set_author(name=member.name, icon_url=str(member.avatar) if member.avatar else str(member.default_avatar))
            await ctx.respond(embed=embed)

        else:
            warns = sql.select(elements=['warns', 'reason'], table='warns',
                               where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
            if not warns:
                await ctx.respond(f'{member.mention} has no warns', ephemeral=True)
                return

            if not warns[0][0] - 1:
                sql.delete(table='warns', where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
                await ctx.respond(embed=discord.Embed(description=f'{member.mention}\'s oldest warn has been removed',
                                                      colour=discord.Colour.green()))
                return

            reason_arr = warns[0][1]
            reason_arr.pop(0)
            reason_str = ''.join(f'\'{r}\', ' for r in reason_arr)
            sql.update(table='warns', column='warns', value=f'{warns[0][0] - 1}')
            reason_str = reason_str[:-2]
            sql.update(table='warns', column='reason', value=f'ARRAY[{reason_str}]',
                       where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
            await ctx.respond(f'{member.mention}\'s oldest warn has been removed',
                              colour=discord.Colour.green())

    @commands.slash_command(name='messageresponse', description='Configure chat triggers for the server',
                            usage='messageresponse <mode> <message> <response>')
    @commands.has_permissions(manage_guild=True)
    async def message_response(self, ctx,
                               mode: Option(str, description='Mode for the command', choices=['add', 'remove', 'view'],
                                            required=True),
                               message: Option(str, description='The message to trigger on', required=False,
                                               default=None),
                               response: Option(str, description='The response to be sent', required=False,
                                                default=None)):
        # sourcery no-metrics
        sql = SQL('b0ssbot')
        original_message = message
        if mode == 'remove':
            if not message:
                await ctx.respond('You must specify a message to remove', ephemeral=True)
                return

            message = message.replace('\'', '\'\'')
            if not sql.select(elements=['message'], table='message_responses',
                              where=f"guild_id = '{ctx.guild.id}' AND message = '{message}'"):
                await ctx.respond(embed=discord.Embed(description=f'No chat triggers found for **{original_message}**',
                                                      colour=discord.Colour.red()))
                return
            sql.delete(table='message_responses',
                       where=f"guild_id = '{ctx.guild.id}' AND message = '{message}'")
            await ctx.respond(embed=discord.Embed(description=f'Removed the response for **{original_message}**',
                                                  colour=discord.Colour.green()))

        elif mode == 'add':
            if not message:
                await ctx.respond('You must specify a message to add', ephemeral=True)
                return

            if not response:
                await ctx.respond('You must specify a response to add', ephemeral=True)
                return

            if message.strip() == '' or response.strip() == '':
                await ctx.respond(
                    embed=discord.Embed(description='Please provide both, a message and a response',
                                        colour=discord.Colour.red()))
                return

            message = message.replace("'", "''").lower()
            response = response.replace("'", "''")
            if sql.select(elements=['message', 'response'], table='message_responses',
                          where=f"guild_id = '{ctx.guild.id}' AND message = '{message}'"):
                sql.update(table='message_responses', column='response', value=f"'{response}'",
                           where=f"guild_id = '{ctx.guild.id}' AND message = '{message}'")
                await ctx.respond(embed=discord.Embed(description=f'Updated the response for **{original_message}**',
                                                      colour=discord.Colour.green()))
            else:
                sql.insert(table='message_responses', columns=['guild_id', 'message', 'response'],
                           values=[f"'{ctx.guild.id}'", f"'{message}'", f"'{response}'"])
                await ctx.respond(
                    embed=discord.Embed(description=f'Added the response for **{original_message}**',
                                        colour=discord.Colour.green()))

        else:
            if not sql.select(elements=['message', 'response'], table='message_responses',
                              where=f"guild_id = '{ctx.guild.id}'"):
                await ctx.respond('No responses found', ephemeral=True)
                return

            if message is None and response is None:
                embed = discord.Embed(title=f'Message Responses for the server {ctx.guild.name}',
                                      colour=discord.Colour.green())
                responses = sql.select(elements=['message', 'response'], table='message_responses',
                                       where=f"guild_id = '{ctx.guild.id}'")
                for row in responses:
                    embed.add_field(name=f'Message: {row[0]}', value=f'Response: {row[1]}', inline=False)

                try:
                    await ctx.respond(embed=embed)
                except discord.HTTPException:
                    with open('responses.txt', 'w') as f:
                        for row in responses:
                            f.write(f'Message: {row[0]}\nResponse: {row[1]}\n\n')
                    await ctx.respond(file=discord.File('responses.txt'))
                    os.remove('responses.txt')

            else:
                text = message.replace("'", "''").lower() if message else response.replace("'", "''")
                elements = sql.select(elements=['message', 'response'], table='message_responses',
                                      where=f"guild_id = '{ctx.guild.id}' AND (message = '{text}' OR response = '{text}')")
                if not elements:
                    await ctx.respond('No chat triggers found', ephemeral=True)
                    return
                embed = discord.Embed(title=f'Message Responses for the server {ctx.guild.name}',
                                      colour=discord.Colour.green())
                for row in elements:
                    embed.add_field(name=f'Message: {row[0]}', value=f'Response: {row[1]}', inline=False)
                try:
                    await ctx.respond(embed=embed)
                except discord.HTTPException:
                    with open('responses.txt', 'w') as f:
                        for row in elements:
                            f.write(f'Message: {row[0]}\nResponse: {row[1]}\n\n')
                    await ctx.respond(file=discord.File('responses.txt'))

    @message_response.error
    async def message_response_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    @commands.slash_command(name='mute', description='Mutes the user specified', usage='mute <user> <duration>')
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: Option(discord.Member, description='The member to be muted', required=True),
                   duration: Option(int,
                                    description='The duration of the mute in minutes. Leave blank for permanent mute',
                                    required=False,
                                    default=None),
                   reason: Option(str, description='The reason for the mute', required=False,
                                  default='No reason provided')):

        if member == ctx.author:
            await ctx.respond('You cannot mute yourself', ephemeral=True)
            return

        if member == self.bot.user:
            await ctx.respond('I cannot mute myself', ephemeral=True)
            return

        if member.guild_permissions >= ctx.author.guild_permissions:
            await ctx.respond('You cannot mute a member with the same or higher permissions', ephemeral=True)
            return

        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')  # Get the muted role
        if not muted_role:
            muted_role = await ctx.guild.create_role(name='Muted')  # Create a muted role if not present
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False,
                                              respond_messages=False)  # Set permissions of the muted role

        try:
            await member.add_roles(muted_role, reason=reason)  # Add muted role
            await ctx.respond(
                embed=discord.Embed(description=f'{member} has been muted for {reason}', colour=discord.Colour.red()))
            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                await member.send(f'You were muted in {ctx.guild.name} for {reason}')
                if duration:
                    await asyncio.sleep(duration * 60)
                    await member.remove_roles(muted_role, reason=reason)
                    await ctx.respond(
                        embed=discord.Embed(description=f'{member} has been unmuted', colour=discord.Colour.green()))
                    with contextlib.suppress(discord.HTTPException):
                        await member.send(f'You have been unmuted in {ctx.guild.name}')
        except discord.Forbidden:  # Permission error
            await ctx.respond('Permission error', ephemeral=True)

    @mute.error
    async def mute_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    @commands.slash_command(name='unmute', description='Unmutes the user specified', usage='unmute <user>')
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: Option(discord.Member, description='The member to be unmuted', required=True)):
        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')  # Get the muted role
        if not muted_role:
            await ctx.respond('There is no muted role', ephemeral=True)
            return

        try:
            await member.remove_roles(muted_role, reason='Unmuted')  # Remove muted role
            await ctx.respond(
                embed=discord.Embed(description=f'{member} has been unmuted', colour=discord.Colour.green()))
        except discord.Forbidden:  # Permission error
            await ctx.respond('Permission error', ephemeral=True)

    @unmute.error
    async def unmute_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    @commands.slash_command(name='timeout', description='Manage timeouts for the user',
                            usage='timeout <user> <mode> <duration> <reason>')
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx,
                      member: Option(discord.Member, description='The member to be timed out', required=True),
                      mode: Option(str, description='The mode of the command', required=True,
                                   choices=['add', 'remove']),
                      minutes: Option(int, description='The duration of the timeout in seconds', required=False,
                                      default=0),
                      reason: Option(str, description='The reason for the timeout', required=False,
                                     default='No reason')):

        if mode == 'add':
            if member.timed_out:
                await ctx.respond(f'{member} is already timed out', ephemeral=True)
                return

            if not minutes:
                await ctx.respond('Mention a value in minutes above 0', ephemeral=True)
                return

            if member.guild_permissions >= ctx.author.guild_permissions:
                await ctx.respond('You cannot timeout this user', ephemeral=True)
                return

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
                await ctx.respond('Permission error', ephemeral=True)

        elif mode == 'remove':
            if not member.timed_out:
                await ctx.respond(f'{member} is not timed out', ephemeral=True)
                return

            if member.guild_permissions >= ctx.author.guild_permissions:
                await ctx.respond('You cannot remove this user\'s timeout', ephemeral=True)
                return

            try:
                await member.remove_timeout()
                await ctx.respond(f'{member} has been removed from timeout',
                                  colour=discord.Colour.green())
                with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                    await member.send(
                        f'You were removed from timeout in {ctx.guild.name}.')

            except discord.Forbidden:  # Permission error
                await ctx.respond('Permission error', ephemeral=True)

    @timeout.error
    async def timeout_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    # Code command
    @commands.slash_command(name='code',
                            description='Code for the modules of the bot', usage='code <module>')
    async def code(self, ctx,
                   module: Option(str, description='The module to get the code for', required=True,
                                  choices=['events', 'fun', 'help', 'info', 'internet', 'misc', 'music', 'moderation',
                                           'util', 'owner', 'slash', 'main', 'keep_alive', 'sql_tools', 'tools',
                                           'games']
                                  )):
        try:
            await ctx.respond('https://github.com/SandeepKanekal/b0ssBot -> Source Code',
                              file=discord.File(f'{module}.py', filename=f'{module}.py'))
        except FileNotFoundError:
            await ctx.respond('https://github.com/SandeepKanekal/b0ssBot -> Source Code',
                              file=discord.File(f'cogs/{module}.py', filename=f'{module}.py'))

    @code.error
    async def code_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)


def setup(bot):
    bot.add_cog(Slash(bot))

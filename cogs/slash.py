import contextlib
import discord
import datetime
import requests
import os
from discord.ext import commands
from discord.commands import Option
from tools import convert_to_unix_time
from sql_tools import SQL
from googleapiclient.discovery import build


class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='prefix', desrciption='Change the prefix of the bot', usage='prefix <new_prefix>')
    @commands.has_permissions(administrator=True)
    async def prefix_slash(self, ctx, new_prefix: Option(str, descrciption='The new prefix', required=True)):
        if len(new_prefix) > 2:
            await ctx.respond('Prefix must be 2 characters or less')
            return

        sql = SQL('b0ssbot')
        sql.update(table='prefixes', column='prefix', value=f'\'{new_prefix}\'', where=f'guild_id=\'{ctx.guild.id}\'')
        await ctx.respond(f'Prefix changed to **{new_prefix}**')

    @prefix_slash.error
    async def prefix_slash_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    @commands.slash_command(name='userinfo',
                            description='Shows the mentioned user\'s information. Leave it blank to get your information',
                            usage='userinfo <member>')
    async def userinfo_slash(self, ctx,
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

    @userinfo_slash.error
    async def userinfo_slash_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    @commands.slash_command(name='avatar', description='Shows the specified user\'s avatar', usage='avatar <user>')
    async def avatar_slash(self, ctx,
                           member: Option(discord.Member, description='User to get the avatar of', required=False,
                                          default=None)):
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
        await ctx.respond(embed=embed)

    @avatar_slash.error
    async def avatar_slash_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    @commands.slash_command(name='youtubenotification', description='Configure youtube notifications for the server',
                            usage='youtubenotification <mode> <text_channel_id> <youtube_channel_id>',
                            guild_ids=[930715526441885696])
    @commands.has_permissions(manage_guild=True)
    async def youtubenotification_slash(self, ctx,
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
            channels = sql.select(elements=['channel_name', 'channel_id', 'text_channel_id'], table='youtube',
                                  where=f'guild_id = \'{ctx.guild.id}\'')
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

    @youtubenotification_slash.error
    async def youtubenotification_slash_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    # Hourlyweather command
    @commands.slash_command(name='hourlyweather', aliases=['hw'],
                            description='Get the hourly weather for a location',
                            usage='hourlyweather <mode> <channel_id> <location>')
    @commands.has_permissions(manage_guild=True)
    async def hourlyweather_slash(self, ctx,
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

    @hourlyweather_slash.error
    async def hourlyweather_slash_error(self, ctx, error):
        await ctx.respond(f'Error: `{error}`', ephemeral=True)

    # Warn command
    @commands.slash_command(name='warn',
                            description='Configure warns for the server',
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
                await ctx.respond(f'{member.mention} has no warns')
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


def setup(bot):
    bot.add_cog(Slash(bot))

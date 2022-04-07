# All Util commands stored here
import contextlib
import os
import discord
import datetime
import asyncio
import time
from sql_tools import SQL
from discord.ext import commands


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description: str) -> None:
    # Response embed
    embed = discord.Embed(description=description, colour=discord.Colour.red())
    await ctx.send(embed=embed)


# A function to convert datetime to unix time for dynamic date-time displays
def convert_to_unix_time(date_time: str, fmt: str = 'R') -> str:
    date_time = date_time.split(' ')
    date_time1 = date_time[0].split('-')
    date_time2 = date_time[1].split(':')
    date_time1 = [int(x) for x in date_time1]
    date_time2 = [int(x) for x in date_time2]
    datetime_tuple = tuple(date_time1 + date_time2)
    date_time = datetime.datetime(*datetime_tuple)
    return f'<t:{int(time.mktime(date_time.timetuple()))}:{fmt}>'


class Util(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # A listener which defines what must be done when a message is deleted
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        sql = SQL('b0ssbot')
        values = [f'\'{message.author.id}\'', f'\'{message.content}\'', f'\'{message.channel.id}\'',
                  f'\'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")}\'']
        if sql.select(elements=['*'], table='snipes', where=f'channel_id = \'{message.channel.id}\''):
            sql.update(table='snipes', column='author_id', value=values[0],
                       where=f'channel_id = \'{message.channel.id}\'')
            sql.update(table='snipes', column='message', value=values[1],
                       where=f'channel_id = \'{message.channel.id}\'')
            sql.update(table='snipes', column='time', value=values[3], where=f'channel_id = \'{message.channel.id}\'')
        else:
            sql.insert(table='snipes', columns=['author_id', 'message', 'channel_id', 'time'], values=values)

        await asyncio.sleep(60)
        sql.delete(table='snipes', where=f'channel_id = \'{message.channel.id}\'')

    # Snipe command
    @commands.command(name='snipe', description='Snipes the most recently deleted message')
    async def snipe(self, ctx):
        sql = SQL('b0ssbot')
        if message := sql.select(
                elements=['author_id', 'message', 'channel_id', 'time'],
                table='snipes',
                where=f'channel_id = \'{ctx.channel.id}\'',
        ):
            # Get the time of deletion and convert to unix time
            del_time = message[0][3]
            del_time = convert_to_unix_time(del_time)
            channel = discord.utils.get(ctx.guild.channels, id=int(message[0][2]))
            member = discord.utils.get(ctx.guild.members, id=int(message[0][0]))
            # Response embed
            embed = discord.Embed(
                title='Sniped a message!',
                description=f'Author: {member.mention}\nDeleted message: {message[0][1]}\nChannel: {channel.mention}\nTime: {del_time}',
                colour=discord.Colour.green()
            ).set_thumbnail(url=str(ctx.guild.icon) if ctx.guild.icon else None)
            await ctx.send(embed=embed)
        else:
            await send_error_embed(ctx, 'There are no messages to snipe')

    @snipe.error
    async def snipe_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # AFK command
    @commands.command(name='afk', description='Marks the user as AFK')
    async def afk(self, ctx, *, reason: str = 'No reason'):
        member = ctx.author
        sql = SQL('b0ssbot')
        with contextlib.suppress(discord.Forbidden):
            await member.edit(nick=f'[AFK] {member.display_name}')  # Changing the nickname
        # Adds member details to the database
        sql.insert(table='afks', columns=['member', 'member_id', 'guild_id', 'reason'],
                   values=[f'\'{member}\'', f'\'{str(member.id)}\'', f'\'{str(ctx.guild.id)}\'', f'\'{reason}\''])
        embed = discord.Embed(title='AFK', description=f'{member.mention} has gone AFK', colour=member.colour)
        embed.set_thumbnail(url=str(member.avatar) if member.avatar else str(member.default_avatar))
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.add_field(name='AFK note', value=reason)
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    @afk.error
    async def afk_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Ping command
    @commands.command(name="ping", description='Replies with the latency of the bot')
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(description=f'**Pong!!** Bot latency is {str(latency)}ms', colour=discord.Colour.yellow())
        await ctx.reply(embed=embed)

    # Clear command
    @commands.command(aliases=['purge'], description='Purges the amount of messages specified by the user')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, limit=0):
        if not limit:
            await send_error_embed(description='Provide a limit')
            return
        if limit > 100:
            await ctx.send('Limit must be lesser than 100')
            return
        await ctx.message.delete()
        await ctx.channel.purge(limit=limit)

    # Permission errors in the clear command is handled here
    @clear.error
    async def clear_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Poll command
    @commands.command(name='poll', description='Make a poll!')
    async def poll(self, ctx, channel: discord.TextChannel = None, *, question):
        embed = discord.Embed(title='Poll', description=question, colour=discord.Colour.yellow())
        embed.set_author(
            name=ctx.author,
            icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(ctx.author.default_avatar)
        )
        embed.timestamp = datetime.datetime.now()

        msg = await channel.send(embed=embed)
        # Adding reactions
        await msg.add_reaction('👍')
        await msg.add_reaction('👎')

    @poll.error
    async def poll_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # Refer command
    @commands.command(name='refer', description='Refers to a message, message ID or link required as a parameter')
    async def refer(self, ctx, message_reference=None):
        if not message_reference.startswith('https://discord.com/channels/'):  # Message ID
            try:
                guild_id = ctx.guild.id
                channel_id = ctx.channel.id
                message_id = message_reference
                message_link = f'https://discord.com/channels/{str(guild_id)}/{str(channel_id)}/{str(message_id)}'
                message = await ctx.fetch_message(message_id)
                try:
                    embed = message.embeds[0]
                    if embed:  # Sends the embed if it exists
                        await ctx.send(embed=embed)
                except IndexError:
                    embed = discord.Embed(colour=message.author.colour)
                    embed.set_author(name=message.author,
                                     icon_url=str(message.author.avatar) if message.author.avatar else str(
                                         message.author.default_avatar))
                    embed.add_field(name=message.content, value=f'\n[Jump to message]({message_link})')
                    embed.set_footer(text=f'Requested by {ctx.author}',
                                     icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(
                                         ctx.author.default_avatar))
                    embed.timestamp = datetime.datetime.now()
                    await ctx.send(embed=embed)
            except discord.NotFound:
                await ctx.send('Message could not be found')
        else:
            try:
                message_link = message_reference
                link = message_link.split('/')
                message_id = int(link[6])  # Getting the message_id
                message = await ctx.fetch_message(message_id)
                try:
                    embed = message.embeds[0]
                    if embed:  # Sends the embed if it exists
                        await ctx.send(embed=embed)
                except IndexError:
                    embed = discord.Embed(colour=message.author.colour)
                    embed.set_author(name=message.author,
                                     icon_url=str(message.author.avatar) if message.author.avatar else str(
                                         message.author.default_avatar))
                    embed.add_field(name=message.content, value=f'\n[Jump to message]({message_link})')
                    embed.set_footer(text=f'Requested by {ctx.author}',
                                     icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(
                                         ctx.author.default_avatar))
                    embed.timestamp = datetime.datetime.now()
                    await ctx.send(embed=embed)
            except discord.NotFound:
                await ctx.send('Message could not be found')

    @refer.error
    async def refer_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    @commands.command(name='prefix', desrciption='Change the prefix of the bot')
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, prefix):
        if len(prefix) > 2:
            await ctx.send('Prefix must be 2 characters or less')
            return

        sql = SQL('b0ssbot')
        sql.update(table='prefixes', column='prefix', value=f'\'{prefix}\'', where=f'guild_id=\'{ctx.guild.id}\'')
        embed = discord.Embed(
            description=f'Prefix changed to **{prefix}**',
            colour=discord.Colour.green()
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon)
        await ctx.reply(embed=embed)

    @prefix.error
    async def prefix_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def query(self, ctx, *, query):
        sql = SQL('b0ssbot')
        results = sql.query(query)
        try:
            await ctx.send(results)
        except discord.HTTPException:
            if results:
                with open('query.txt', 'w') as f:
                    f.write(str(results))
                await ctx.send(file=discord.File('query.txt'))
                os.remove('query.txt')
            else:
                await ctx.send('Query provided returns None')

    @query.error
    async def query_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')


def setup(bot):
    bot.add_cog(Util(bot))

# All Util commands stored here
import contextlib
import discord
import datetime
import asyncio
import time
from discord.ext import commands
from afks import afks


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description: str) -> None:
    # Response embed
    embed = discord.Embed(description=description, colour=discord.Colour.red())
    await ctx.send(embed=embed)


# A function to convert datetime to unix time for dynamic date-time displays
def convert_to_unix_time(datetime: str, fmt: str = 'R') -> str:
    datetime_tuple = tuple(int(x) for x in datetime[:10].split('-')) + tuple(int(x) for x in datetime[11:].split(':'))
    datetime = datetime.datetime(*datetime_tuple)
    return f'<t:{int(time.mktime(datetime.timetuple()))}:{fmt}>'


class Util(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sniped_message = {}
    
    # A listener which defines what must be done when a message is deleted
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        self.sniped_message[message.guild.id] = {  # Store the details of the message
            'author': message.author,
            'message': message.content,
            'channel': message.channel,
            'time': datetime.datetime.now()
        }

        await asyncio.sleep(60)
        self.snipe_message.pop(message.guild.id)
    
    # Snipe command
    @commands.command(name='snipe', description='Snipes the most recently deleted message')
    async def snipe(self, ctx):
        try:
            # Get the time of deletion and convert to unix time
            del_time = self.sniped_message[ctx.guild.id]['time']
            del_time = convert_to_unix_time(del_time)
            # Response embed
            embed = discord.Embed(
                title='Sniped a message!',
                description=f'Author: {self.sniped_message[ctx.guild.id]["author"].mention}\nDeleted message: {self.sniped_message[ctx.guild.id]["message"]}\nChannel: {self.sniped_message[ctx.guild.id]["channel"].mention}\nTime: {del_time}',
                colour=discord.Colour.green()
            )
            await ctx.send(embed=embed)
        except KeyError:
            await send_error_embed(ctx, 'There are no messages to snipe')

    @snipe.error
    async def snipe_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')

    # AFK command
    @commands.command(name='afk', description='Marks the user as AFK')
    async def afk(self, ctx, *, reason='No reason'):
        member = ctx.author
        with contextlib.suppress(discord.Forbidden):
            await member.edit(nick=f'[AFK] {member.display_name}')  # Changing the nickname
        # Append the member's details to the afk list
        afks.append(
            {
                'member_id': member.id,
                'reason': reason,
                'guild_id': ctx.guild.id
            }
        )
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
                    embed.set_author(name=message.author, icon_url=str(message.author.avatar) if message.author.avatar else str(message.author.default_avatar))
                    embed.add_field(name=message.content, value=f'\n[Jump to message]({message_link})')
                    embed.set_footer(text=f'Requested by {ctx.author}', icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(ctx.author.default_avatar))
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
                    embed.set_author(name=message.author, icon_url=str(message.author.avatar) if message.author.avatar else str(message.author.default_avatar))
                    embed.add_field(name=message.content, value=f'\n[Jump to message]({message_link})')
                    embed.set_footer(text=f'Requested by {ctx.author}', icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(ctx.author.default_avatar))
                    embed.timestamp = datetime.datetime.now()
                    await ctx.send(embed=embed)
            except discord.NotFound:
                await ctx.send('Message could not be found')

    @refer.error
    async def refer_error(self, ctx, error):
        await send_error_embed(ctx, description=f'Error: {error}')


def setup(bot):
    bot.add_cog(Util(bot))

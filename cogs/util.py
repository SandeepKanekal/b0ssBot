# All Util commands stored here
import discord
import datetime
from discord.ext import commands
from afks import afks

today = datetime.date.today()


class Util(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # AFK command
    @commands.command(name='afk', description='Marks the user as AFK')
    async def afk(self, ctx, *, reason='No reason'):
        member = ctx.author
        if member.id in afks.keys():
            afks.pop(member.id)
        else:
            try:
                await member.edit(nick=f'[AFK] {member.display_name}')
            except discord.Forbidden:
                await ctx.send('Added AFK, but could not change the nickname')
        afks[member.id] = reason
        embed = discord.Embed(title='AFK', description=f'{member.mention} has gone AFK', colour=member.colour)
        embed.set_thumbnail(url=member.avatar)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.add_field(name='AFK note', value=reason)
        await ctx.send(embed=embed)

    # Ping command
    @commands.command(name="ping", description='Shows the bot latency')
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(colour=discord.Colour.random())
        embed.add_field(name='Pong!!', value=f'Bot latency is {latency}ms')
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(text=f'Requested by {ctx.author} • {today.strftime("%B %d, %Y")}',
                         icon_url=ctx.author.avatar)
        await ctx.reply(embed=embed)

    # Clear command
    @commands.command(aliases=['purge'], description='Purges the amount of messages specified by the user')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, limit=0):
        await ctx.message.delete()
        await ctx.channel.purge(limit=limit)

    # Refer command
    @commands.command(name='refer', description='Refers to a message, message ID or link required as a parameter')
    async def refer(self, ctx, message_reference=None):
        if not message_reference.startswith('https://discord.com/channels/'):
            try:
                guild_id = ctx.guild.id
                channel_id = ctx.channel.id
                message_id = message_reference
                message_link = 'https://discord.com/channels/' + str(guild_id) + '/' + str(channel_id) + '/' + str(
                    message_id)
                message = await ctx.fetch_message(message_id)
                try:
                    embed = message.embeds[0]
                    if embed:
                        await ctx.send(embed=embed)
                except IndexError:
                    embed = discord.Embed(colour=message.author.colour)
                    embed.set_author(name=message.author, icon_url=message.author.avatar)
                    embed.add_field(name=message.content, value=f'\n[Jump to message]({message_link})')
                    embed.set_footer(text=f'Requested by {ctx.author} • {today.strftime("%B %d, %Y")}',
                                     icon_url=str(ctx.author.avatar))
                    await ctx.send(embed=embed)
            except discord.NotFound:
                await ctx.send('Message could not be found')
        else:
            try:
                message_link = message_reference
                link = message_link.split('/')
                message_id = int(link[6])
                message = await ctx.fetch_message(message_id)
                try:
                    embed = message.embeds[0]
                    if embed:
                        await ctx.send(embed=embed)
                except IndexError:
                    embed = discord.Embed(colour=message.author.colour)
                    embed.set_author(name=message.author, icon_url=message.author.avatar)
                    embed.add_field(name=message.content, value=f'\n[Jump to message]({message_link})')
                    embed.set_footer(text=f'Requested by {ctx.author} • {today.strftime("%B %d, %Y")}',
                                     icon_url=str(ctx.author.avatar))
                    await ctx.send(embed=embed)
            except discord.NotFound:
                await ctx.send('Message could not be found')


def setup(bot):
    bot.add_cog(Util(bot))

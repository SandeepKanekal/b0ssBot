# Information commands defined here
import discord
import datetime
from tools import send_error_embed, convert_to_unix_time
from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.uptime: str = None
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.uptime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")

    # Userinfo command
    @commands.command(aliases=['whois', 'user', 'ui'],
                      description='Shows the mentioned user\'s information. Leave it blank to get your information',
                      usage='userinfo <member>')
    async def userinfo(self, ctx, *, member: discord.Member = None):
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
        await ctx.send(embed=embed)

    @userinfo.error
    async def userinfo_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await send_error_embed(ctx,
                                   description=f'Please mention a valid user\n\nProper Usage: `{self.bot.get_command("userinfo").usage}`')
            return
        await send_error_embed(ctx, description=f'Error: `{error}`')

    # Serverinfo command
    @commands.command(aliases=['si', 'server'], description='Shows the server information', usage='serverinfo')
    async def serverinfo(self, ctx):
        # User stats
        user_count = len(ctx.guild.members)  # includes bots
        member_count = len([m for m in ctx.guild.members if not m.bot])  # bots not included
        bot_count = user_count - member_count
        ban_count = 0
        async for _ in ctx.guild.bans():
            ban_count += 1

        # Channel stats
        text_channel_count = sum(1 for _ in ctx.guild.text_channels)
        voice_channel_count = sum(1 for _ in ctx.guild.voice_channels)

        # Emoji stats
        emojis = ctx.guild.emojis
        emoji_string = f'Total: **{len(emojis)}**\n'
        animated_emojis_len = len(list(filter(lambda emoji: emoji.animated, emojis)))
        emoji_string += f'Animated: **{animated_emojis_len}**\n'
        emoji_string += f'Non Animated: **{len(emojis) - animated_emojis_len}**'

        # Getting the creation date of the server relative unix time
        created_at = ctx.guild.created_at.strftime('%Y-%m-%d %H:%M:%S:%f')
        created_at = convert_to_unix_time(created_at)

        # User and channel strings
        member_string = f'Total: **{user_count}**\nMembers: **{member_count}**\nBots: **{bot_count}**'
        channel_string = f'Text Channels: **{text_channel_count}**\nVoice Channels **{voice_channel_count}**'

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon) if ctx.guild.icon else None
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon) if ctx.guild.icon else embed.set_author(
            name=ctx.guild.name)
        embed.add_field(name="Owner", value=str(ctx.guild.owner.mention))
        embed.add_field(name='Roles', value=str(len(ctx.guild.roles)))
        embed.add_field(name='Creation Date', value=created_at)
        embed.add_field(name='Users', value=member_string)
        embed.add_field(name='Channels', value=channel_string)
        embed.add_field(name='Server Emojis', value=emoji_string)
        embed.add_field(name='Server Boosts', value=ctx.guild.premium_subscription_count)
        embed.add_field(name='Number of Bans', value=str(ban_count))
        try:
            embed.add_field(name='Muted Users', value=len(discord.utils.get(ctx.guild.roles, name='Muted').members))
        except AttributeError:
            embed.add_field(name='Muted Users', value=str(0))
        embed.set_footer(text=f'ID: {ctx.guild.id}')
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    # Botinfo command
    @commands.command(aliases=['bi', 'bot'], description='Shows the bot\'s information', usage='botinfo')
    async def botinfo(self, ctx):
        # Getting the creation date of the server relative unix time
        created_at = self.bot.user.created_at.strftime('%Y-%m-%d %H:%M:%S:%f')
        created_at = convert_to_unix_time(created_at)

        embed = discord.Embed(colour=self.bot.user.colour)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.add_field(name='Bot Username', value=str(self.bot.user.name), inline=True)
        embed.add_field(name='Bot Owner', value='Dose#7204')
        embed.add_field(name='Total Servers', value=str(len(list(self.bot.guilds))))
        embed.add_field(name='Bot ID', value=str(self.bot.user.id))
        embed.add_field(name='Bot Creation Date', value=created_at)
        embed.add_field(name='Total Users', value=str(len(self.bot.users)))
        embed.add_field(name='Bot Tag', value=f'{self.bot.user.name}#{self.bot.user.discriminator}')
        embed.add_field(name='Source Code', value='[Click here](https://github.com/SandeepKanekal/b0ssBot)')
        embed.add_field(name='Invite Link',
                        value='[Click here](https://discord.com/api/oauth2/authorize?client_id=930715008025890887'
                              '&permissions=8&scope=applications.commands%20bot)')
        embed.set_footer(text=f'Requested by {ctx.author}',
                         icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(ctx.author.default_avatar))
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)

    @commands.command(aliases=['cl'], description='Shows the changelog', usage='changelog')
    async def changelog(self, ctx):
        with open('CHANGELOG.md', 'r') as f:
            changelog = f.read()

        changelog = changelog.replace('#', '**')
        changelog = changelog.replace('+', '•')

        embed = discord.Embed(
            title='Changelog',
            url='https://github.com/SandeepKanekal/b0ssBot/blob/main/CHANGELOG.md',
            description=changelog,
            colour=self.bot.user.colour
        )
        embed.set_thumbnail(url=self.bot.user.avatar)
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)
    
    @commands.command(name='uptime', description='Shows the bot\'s uptime', usage='uptime')
    async def uptime(self, ctx):
        await ctx.send(
            embed=discord.Embed(description=f'The bot was started {convert_to_unix_time(self.uptime)}', colour=self.bot.user.colour)
        )


# Setup
def setup(bot):
    bot.add_cog(Info(bot))

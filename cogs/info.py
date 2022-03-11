# Information commands defined here
import discord
import datetime
from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Userinfo command
    @commands.command(aliases=['whois'], description='Shows the mentioned user\'s information')
    async def userinfo(self, ctx, member: discord.Member = None):
        if member is not None:
            embed = discord.Embed(colour=member.colour)
            embed.set_author(name=str(member), icon_url=str(member.avatar))
            embed.add_field(name='Display Name', value=member.mention, inline=True)
            embed.add_field(name='Top Role', value=member.top_role, inline=False)
            embed.set_thumbnail(url=str(member.avatar))
            embed.add_field(name='Joined', value=member.joined_at.strftime("%b %d, %Y, %T"), inline=True)
            embed.add_field(name='Registered', value=member.created_at.strftime("%b %d, %Y, %T"), inline=True)
            if len(member.roles) > 1:
                role_string = ' '.join([r.mention for r in member.roles][1:])
                embed.add_field(name=f'Roles[{len(member.roles) - 1}]', value=role_string, inline=False)
            else:
                embed.add_field(name='Roles[1]', value=member.top_role.mention, inline=False)
            embed.set_footer(text=f'ID: {member.id} • Requested by {ctx.author}', icon_url=ctx.author.avatar)
            embed.timestamp = datetime.datetime.now()
            await ctx.send(embed=embed)
        else:
            member = ctx.author
            embed = discord.Embed(colour=member.colour)
            embed.set_author(name=str(member), icon_url=member.avatar)
            embed.add_field(name='Display Name', value=member.mention, inline=True)
            embed.add_field(name='Top Role', value=member.top_role, inline=False)
            embed.set_thumbnail(url=member.avatar)
            embed.add_field(name='Joined', value=member.joined_at.strftime("%b %d, %Y, %T"), inline=True)
            embed.add_field(name='Registered', value=member.created_at.strftime("%b %d, %Y, %T"), inline=True)
            if len(member.roles) > 1:
                role_string = ' '.join([r.mention for r in member.roles][1:])
                embed.add_field(name=f'Roles[{len(member.roles) - 1}]', value=role_string, inline=False)
            else:
                embed.add_field(name='Roles[1]', value=member.top_role.mention, inline=False)
            embed.set_footer(text=f'ID: {member.id} • Requested by {ctx.author}', icon_url=ctx.author.avatar)
            embed.timestamp = datetime.datetime.now()
            await ctx.send(embed=embed)

    # Serverinfo command
    @commands.command(name='serverinfo', description='Shows the server information')
    async def serverinfo(self, ctx):
        user_count = len(ctx.guild.members)  # includes bots
        member_count = len([m for m in ctx.guild.members if not m.bot])  # bots not included
        bot_count = user_count - member_count
        text_channel_count = 0
        for _ in ctx.guild.text_channels:
            text_channel_count += 1
        voice_channel_count = 0
        for _ in ctx.guild.voice_channels:
            voice_channel_count += 1

        emojis = ctx.guild.emojis
        emoji_string = f'Total: **{len(emojis)}**\n'
        animated_emojis = filter(lambda emoji: emoji.animated, emojis)
        animated_emojis_len = len(list(animated_emojis))
        emoji_string += f'Animated: **{animated_emojis_len}**\n'
        emoji_string += f'Non Animated: **{len(emojis) - animated_emojis_len}**'

        member_string = f'Total: **{user_count}**\nMembers: **{member_count}**\nBots: **{bot_count}**'
        channel_string = f'Text Channels: **{text_channel_count}**\nVoice Channels **{voice_channel_count}**'
        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        embed.add_field(name="Owner", value=str(ctx.guild.owner.mention))
        embed.add_field(name='Roles', value=str(len(ctx.guild.roles)))
        embed.add_field(name='Top Role', value=ctx.guild.owner.top_role.mention)
        embed.add_field(name='Users', value=member_string)
        embed.add_field(name='Channels', value=channel_string)
        embed.add_field(name='Server Emojis', value=emoji_string)
        embed.add_field(name='Server Boosts', value=ctx.guild.premium_subscription_count)
        embed.add_field(name='Number of Bans', value=len(await ctx.guild.bans()))
        embed.add_field(name='Muted Users', value=len(discord.utils.get(ctx.guild.roles, name='Muted').members))
        embed.set_footer(
            text=f'ID: {ctx.guild.id} | Created • {str(ctx.guild.created_at.strftime("%b %d, %Y, %T"))}')
        await ctx.send(embed=embed)

    # Botinfo command
    @commands.command(name='botinfo', description='Shows the bot\'s information')
    async def botinfo(self, ctx):
        guilds = len([s for s in self.bot.guilds])
        embed = discord.Embed(colour=self.bot.user.colour)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.add_field(name='Bot Username', value=str(self.bot.user.name), inline=True)
        embed.add_field(name='Bot Owner', value='Dose#7204', inline=True)
        embed.add_field(name='Total Servers', value=str(guilds), inline=True)
        embed.add_field(name='Bot ID', value=str(self.bot.user.id), inline=True)
        embed.add_field(name='Bot Creation Date', value=str(self.bot.user.created_at.strftime('%b %d, %Y, %T')),
                        inline=True)
        embed.add_field(name='Total Users', value=str(len(self.bot.users)), inline=True)
        embed.add_field(name='Bot Tag', value=f'{self.bot.user.name}#{self.bot.user.discriminator}', inline=True)
        embed.add_field(name='Source Code', value='[Click here](https://github.com/SandeepKanekal/b0ssBot)',
                        inline=True)
        embed.add_field(name='Invite Link',
                        value='[Click here](https://discord.com/api/oauth2/authorize?client_id=930715008025890887'
                              '&permissions=8&scope=applications.commands%20bot)',
                        inline=True)
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=str(ctx.author.avatar))
        embed.timestamp = datetime.datetime.now()
        await ctx.send(embed=embed)


# Setup
def setup(bot):
    bot.add_cog(Info(bot))

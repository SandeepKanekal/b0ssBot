# Copyright (c) 2022 Sandeep Kanekal
# Information commands defined here
import discord
import datetime
from tools import send_error_embed, convert_to_unix_time, inform_owner
from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """
        Initialize the cog
        
        :param bot: The bot
        :type bot: commands.Bot
        
        :return: None
        :rtype: None
        """
        self.bot = bot  # type: commands.Bot
        self.uptime = None

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Event listener for when the bot is ready

        :return: None
        :rtype: None
        """
        self.uptime = datetime.datetime.now()  # Sets the uptime to now

    # Userinfo command
    @commands.command(aliases=['whois', 'user', 'ui'],
                      description='Shows the mentioned user\'s information. Leave it blank to get your information',
                      usage='userinfo <member>')
    async def userinfo(self, ctx: commands.Context, *, member: discord.Member = None):
        """
        Shows the mentioned user's information. Member is author if left blank.
        
        :param ctx: The context of where the message was sent
        :param member: The member to get the information of (defaults to author)

        :type ctx: commands.Context
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
        embed.set_image(url=member.banner or discord.Embed.Empty)

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

        await ctx.send(embed=embed)

    @userinfo.error
    async def userinfo_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Error handler for the userinfo command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.BadArgument):
            await send_error_embed(ctx,
                                   description=f'Please mention a valid user\n\nProper Usage: `{self.bot.get_command("userinfo").usage}`')
            return
        await send_error_embed(ctx,
                               description='An error occurred while running the userinfo command! The owner has been notified.')
        await inform_owner(ctx, error)

    # Serverinfo command
    @commands.command(aliases=['si', 'server'], description='Shows the server information', usage='serverinfo')
    async def serverinfo(self, ctx: commands.Context):
        """
        Shows the server information
        
        :param ctx: The context of where the message was sent
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        # User stats
        user_count = len(ctx.guild.members)  # includes bots
        member_count = len([m for m in ctx.guild.members if not m.bot])  # bots not included
        bot_count = user_count - member_count
        ban_count = 0
        async for _ in ctx.guild.bans():
            ban_count += 1

        # Channel stats
        text_channel_count = sum(1 for _ in ctx.guild.text_channels)  # type: int
        voice_channel_count = sum(1 for _ in ctx.guild.voice_channels)  # type: int

        # Emoji stats
        emojis = ctx.guild.emojis
        emoji_string = f'Total: **{len(emojis)}**\n'
        animated_emojis_len = len(list(filter(lambda emoji: emoji.animated, emojis)))
        emoji_string += f'Animated: **{animated_emojis_len}**\n'
        emoji_string += f'Non Animated: **{len(emojis) - animated_emojis_len}**'

        # Getting the creation date of the server relative unix time
        created_at = ctx.guild.created_at.strftime('%Y-%m-%d %H:%M:%S:%f')  # type: str
        created_at = convert_to_unix_time(created_at)  # type: str

        # User and channel strings
        member_string = f'Total: **{user_count}**\nMembers: **{member_count}**\nBots: **{bot_count}**'  # type: str
        channel_string = f'Text Channels: **{text_channel_count}**\nVoice Channels **{voice_channel_count}**'  # type: str

        embed = discord.Embed(color=discord.Color.blue(), timestamp=datetime.datetime.now())

        embed.set_thumbnail(url=ctx.guild.icon) if ctx.guild.icon else None
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon or discord.Embed.Empty)
        embed.set_footer(text=f'ID: {ctx.guild.id}')

        embed.add_field(name="Owner", value=str(ctx.guild.owner.mention))
        embed.add_field(name='Roles', value=str(len(ctx.guild.roles)))
        embed.add_field(name='Creation Date', value=created_at)
        embed.add_field(name='Users', value=member_string)
        embed.add_field(name='Channels', value=channel_string)
        embed.add_field(name='Server Emojis', value=emoji_string)
        embed.add_field(name='Server Boosts', value=str(ctx.guild.premium_subscription_count))
        embed.add_field(name='Number of Bans', value=str(ban_count))
        try:
            embed.add_field(name='Muted Users',
                            value=str(len(discord.utils.get(ctx.guild.roles, name='Muted').members)))
        except AttributeError:
            embed.add_field(name='Muted Users', value=str(0))
        await ctx.send(embed=embed)

    # Botinfo command
    @commands.command(aliases=['bi', 'bot'], description='Shows the bot\'s information', usage='botinfo')
    async def botinfo(self, ctx: commands.Context):
        """
        Shows the bots information
        
        :param ctx: The context of where the message was sent
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        # Getting the creation date of the server relative unix time
        created_at = self.bot.user.created_at.strftime('%Y-%m-%d %H:%M:%S:%f')  # type: str
        created_at = convert_to_unix_time(created_at)  # type: str

        embed = discord.Embed(
            description=f'I am {self.bot.user.name}! I was created by Dose#7204. I was coded using the [pycord](https://github.com/Pycord-Development/pycord) library and my code is available [here](https://github.com/SandeepKanekal/b0ssBot). Though I am a multipurpose bot, my best feature is the internet commands. Use the help command to get to know all my commands.',
            colour=0x0c1e4a, timestamp=datetime.datetime.now())

        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.display_avatar)

        embed.add_field(name='Bot Username', value=self.bot.user.name, inline=True)
        embed.add_field(name='Bot Owner', value='Dose#7204')
        embed.add_field(name='Total Servers', value=str(len(list(self.bot.guilds))))
        embed.add_field(name='Bot ID', value=str(self.bot.user.id))
        embed.add_field(name='Bot Creation Date', value=created_at)
        embed.add_field(name='Total Users', value=str(len(self.bot.users)))
        embed.add_field(name='Bot Tag', value=f'{self.bot.user.name}#{self.bot.user.discriminator}')
        embed.add_field(name='Source Code', value='[Click here](https://github.com/SandeepKanekal/b0ssBot)')
        embed.add_field(name='Invite Link',
                        value='[Click here](https://discord.com/api/oauth2/authorize?client_id=930715008025890887&permissions=8&scope=bot%20applications.commands)')

        await ctx.send(embed=embed)

    @commands.command(aliases=['cl'], description='Shows the changelog', usage='changelog')
    async def changelog(self, ctx: commands.Context):
        """
        Shows the bots changelog
        
        :param ctx: The context of where the message was sent
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        # Copy content from CHANGELOG.md
        with open('CHANGELOG.md', 'r') as f:
            changelog = f.read().replace('#', '**').replace('+', '•')  # type: str

        embed = discord.Embed(
            title='Changelog',
            url='https://github.com/SandeepKanekal/b0ssBot/blob/main/CHANGELOG.md',
            description=changelog,
            colour=0x0c1e4a,
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=self.bot.user.avatar)
        await ctx.send(embed=embed)

    @commands.command(name='uptime', description='Shows the bot\'s uptime', usage='uptime')
    async def uptime_(self, ctx: commands.Context):
        """
        Shows the bots uptime
        
        :param ctx: The context of where the message was sent
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        await ctx.send(
            embed=discord.Embed(
                description=f'The bot was started on {convert_to_unix_time(self.uptime.strftime("%Y-%m-%d %H:%M:%S:%f"), "F")}.',
                colour=0x0c1e4a
            )
        )

    @commands.command(name='roleinfo', aliases=['role', 'ri'], description='Shows the information of a role',
                      usage='roleinfo <role>')
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role):
        """
        Shows the information of a role
        
        :param ctx: The context of where the message was sent
        
        :type ctx: commands.Context
        
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

        # Create embed
        embed = discord.Embed(colour=role.colour, timestamp=datetime.datetime.now())

        # Add data
        embed.set_author(name=role.name, icon_url=role.icon or role.guild.icon or discord.Embed.Empty)
        embed.set_footer(text=f'ID: {role.id}')
        embed.set_thumbnail(url=role.icon or discord.Embed.Empty)

        # Add fields
        embed.add_field(name='Members', value=str(len(role.members)), inline=True)
        embed.add_field(name='Creation Date', value=created_at, inline=True)
        embed.add_field(name='Colour',
                        value=f'**RGB:** {rgb_colour[0]}, {rgb_colour[1]}, {rgb_colour[2]}\n**Hex Code:** {role.colour}',
                        inline=True)
        embed.add_field(name='Mentionable', value=str(role.mentionable), inline=True)
        embed.add_field(name='Position', value=str(role.position), inline=True)
        embed.add_field(name='Hoisted', value=str(role.hoist), inline=True)
        embed.add_field(name='Permissions', value=', '.join(
            [permission[0].replace('_', ' ').title() for permission in role.permissions if permission[1]]) or 'None',
                        inline=False)

        await ctx.send(embed=embed)

    @roleinfo.error
    async def roleinfo_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Handles errors for the roleinfo command
        
        :param ctx: The context of where the message was sent
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.BadArgument):
            await send_error_embed(ctx, 'Invalid role')
        elif isinstance(error, commands.MissingRequiredArgument):
            await send_error_embed(ctx,
                                   f'Missing required argument. Please specify a role\n\nProper Usage: `{self.bot.get_command("roleinfo").usage}`')
        else:
            await send_error_embed(ctx, 'An error has occurred while running the roleinfo command.')
            await inform_owner(self.bot, error)


# Setup
def setup(bot: commands.Bot):
    """
    Loads the cog
    
    :param bot: The bot object
    
    :type bot: commands.Bot
    
    :return: None
    :rtype: None
    """
    bot.add_cog(Info(bot))

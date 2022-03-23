# Moderation commands defined here
import contextlib
import discord
import datetime
from discord.ext import commands


# A function to make simple embeds without thumbnails, footers and authors
async def send_embed(ctx, description, colour: discord.Colour = discord.Colour.red()):
    # Response embed
    embed = discord.Embed(description=description, colour=colour)
    await ctx.send(embed=embed)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Ban command
    @commands.command(name='ban', description='Bans the mentioned user from the server')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason='reason not provided'):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot ban yourself', colour=discord.Colour.red())
            return
        try:
            await send_embed(ctx, description=f'{member} was banned for {reason}', colour=discord.Colour.red())
            with contextlib.suppress(discord.HTTPException):
                await member.send(f'You were banned in {ctx.guild.name} for: {reason}')
            await member.ban(reason=reason)
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error')
    
    # Ban error response
    @ban.error
    async def ban_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')

    # Kick command
    @commands.command(name='kick', description='Kicks the mentioned user from the server')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason='no reason'):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot kick yourself', colour=discord.Colour.red())
            return
        try:
            await send_embed(ctx, description=f'{member} was kicked for {reason}', colour=discord.Colour.red())
            with contextlib.suppress(discord.HTTPException):
                await member.send(f'You were kicked in {ctx.guild.name} for {reason}')
            await member.kick(reason=reason)
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error')
    
    # Kick error response
    @kick.error
    async def kick_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')

    # Unban command
    @commands.command(aliases=['ub'], description='Unbans the mentioned member from the server')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot unban yourself', colour=discord.Colour.red())
            return
        banned_users = await ctx.guild.bans()
        name, discriminator = member.split('#')
        for _ in banned_users:
            user = _.user
            if (user.name, user, discriminator) == (name, discriminator):
                try:
                    await send_embed(ctx, description=f'{member} was unbanned', colour=discord.Colour.green())
                    with contextlib.suppress(discord.HTTPException):
                        await member.send(f'You were unbanned in {ctx.guild}')
                    await ctx.guild.unban(user)
                    return
                except discord.Forbidden:  # Permission error
                    await send_embed(ctx, description='Permission error')
                    return
    
    # Unban error response
    @unban.error
    async def unban_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')

    # Mute command
    @commands.command(name='mute', description='Mutes the specified user')
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, *, reason='no reason'):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot mute yourself', colour=discord.Colour.red())
            return
        guild = ctx.guild
        muted_role = discord.utils.get(guild.roles, name='Muted')  # Get the muted role
        if not muted_role:
            muted_role = await guild.create_role(name='Muted')  # Create a muted role if not present
            for channel in guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)  # Set permissions of the muted role
        try:
            await member.add_roles(muted_role, reason=reason)  # Add muted role
            await send_embed(ctx, description=f'{member} has been muted for {reason}', colour=discord.Colour.red())
            with contextlib.suppress(discord.HTTPException):
                await member.send(f'You were muted in {guild.name} for {reason}')
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error')
    
    # Mute error response
    @mute.error
    async def mute_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')

    # Unmute command
    @commands.command(aliases=['um'], description='Unmutes the specified user')
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot unmute yourself', colour=discord.Colour.red())
            return
        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')  # Get muted role
        try:
            await member.remove_roles(muted_role)  # Remove role
            await send_embed(ctx, description=f'{member} was unmuted', colour=discord.Colour.green())
            with contextlib.suppress(discord.HTTPException):
                await member.send(f'You have been unmuted in {ctx.guild.name}')
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error')
    
    # Unmute error response
    @unmute.error
    async def unmute_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')

    # Nuke command
    @commands.command(aliases=['nk'], description='Nukes the mentioned text channel')
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        nuke_channel = None
        if channel is None:
            await ctx.send('Please mention the text channel to be nuked')
            return
        try:
            nuke_channel = discord.utils.get(ctx.guild.channels, name=channel.name)  # Get the channel to be nuked
        except commands.errors.ChannelNotFound:
            await ctx.send('Channel not found')
        if nuke_channel is not None:
            try:
                new_channel = await nuke_channel.clone(reason="Has been Nuked!")
                await nuke_channel.delete()
                await send_embed(new_channel, description='This channel was nuked!', colour=discord.Colour.red())
                await new_channel.send('https://tenor.com/view/explosion-mushroom-cloud-atomic-bomb-bomb-boom-gif-4464831')
                with contextlib.suppress(discord.NotFound):
                    await ctx.reply("Nuked the Channel successfully!")
            except discord.Forbidden:  # Permission error
                await send_embed(ctx, description='Permission error')
    
    # Nuke error response
    @nuke.error
    async def nuke_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')

    # Lock command
    @commands.command(name='lock', description='Locks the current channel')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        try:
            channel = ctx.channel
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await send_embed(ctx, description=f'{channel} is in lockdown', colour=discord.Colour.red())
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error')
    
    # Lock error response
    @lock.error
    async def lock_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')

    # Unlock command
    @commands.command(name='unlock', description='Unlocks te current channel')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        try:
            channel = ctx.channel
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await send_embed(ctx, description=f'{channel} has been unlocked', colour=discord.Colour.red())
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error')
    
    # Unlock error response
    @unlock.error
    async def unlock_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')
    
    # Timeout commands
    @commands.command(name='timeout', description='Times out the mentioned user. Duration in minutes')
    async def timeout(self, ctx, member: discord.Member, minutes: int, *, reason: str = 'No reason provided'):
        if not member:
            await send_embed(ctx, description='Whom must I timeout?')
            return

        if not minutes:
            await send_embed(ctx, description='Mention a value in minutes above 0')
            return

        try:
            duration = datetime.timedelta(minutes=minutes)
            await member.timeout_for(duration=duration, reason=reason)
            embed = discord.Embed(
                description=f'{member.mention} has been timed out for {minutes} {"minute" if minutes == 1 else "minutes"}. Reason: {reason}',
                colour = discord.Colour.green()
            )
            await ctx.send(embed=embed)
            with contextlib.suppress(discord.HTTPException):
                await member.send(f'You were timed out in {ctx.guild.name} for {minutes} {"minute" if minutes == 1 else "minutes"}. Reason: {reason}')
        
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error')
    
    # Timeout error response
    @timeout.error
    async def timeout_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')


# Setup
def setup(bot):
    bot.add_cog(Moderation(bot))

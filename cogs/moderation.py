# Moderation commands defined here
import discord
from discord.ext import commands


# A function to make simple embeds without thumbnails, footers and authors
async def send_embed(ctx, description, colour: discord.Colour):
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
        try:
            await send_embed(ctx, description=f'{member} was banned for {reason}', colour=discord.Colour.red())
            try:
                await member.send(f'You were banned in {ctx.guild.name} for: {reason}')
            except discord.HTTPException:  # Direct messages cannot be sent to bots
                pass
            await member.ban(reason=reason)
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error', colour=discord.Colour.red())
    
    # Ban error response
    @ban.error
    async def ban_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}', colour=discord.Colour.red())

    # Kick command
    @commands.command(name='kick', description='Kicks the mentioned user from the server')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason='no reason'):
        try:
            await send_embed(ctx, description=f'{member} was kicked for {reason}', colour=discord.Colour.red())
            try:
                await member.send(f'You were kicked in {ctx.guild.name} for {reason}')
            except discord.HTTPException:  # Direct messages cannot be sent to bots
                pass
            await member.kick(reason=reason)
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error', colour=discord.Colour.red())
    
    # Kick error response
    @kick.error
    async def kick_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}', colour=discord.Colour.red())

    # Unban command
    @commands.command(aliases=['ub'], description='Unbans the mentioned member from the server')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        banned_users = await ctx.guild.bans()
        name, discriminator = member.split('#')
        for _ in banned_users:
            user = _.user
            if (user.name, user, discriminator) == (name, discriminator):
                try:
                    await send_embed(ctx, description=f'{member} was unbanned', colour=discord.Colour.green())
                    try:
                        await member.send(f'You were unbanned in {ctx.guild}')
                    except discord.HTTPException:  # Direct messages cannot be sent to bots
                        pass
                    await ctx.guild.unban(user)
                    return
                except discord.Forbidden:  # Permission error
                    await send_embed(ctx, description='Permission error', colour=discord.Colour.red())
                    return
    
    # Unban error response
    @unban.error
    async def unban_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}', colour=discord.Colour.red())

    # Mute command
    @commands.command(name='mute', description='Mutes the specified user')
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, *, reason='no reason'):
        guild = ctx.guild
        muted_role = discord.utils.get(guild.roles, name='Muted')  # Get the muted role
        if not muted_role:
            muted_role = await guild.create_role(name='Muted')  # Create a muted role if not present
            for channel in guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)  # Set permissions of the muted role
        try:
            await member.add_roles(muted_role, reason=reason)  # Add muted role
            await send_embed(ctx, description=f'{member} has been muted for {reason}', colour=discord.Colour.red())
            try:
                await member.send(f'You were muted in {guild.name} for {reason}')
            except discord.HTTPException:  # Direct messages cannot be sent to bots
                pass
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error', colour=discord.Colour.red())
    
    # Mute error response
    @mute.error
    async def mute_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}', colour=discord.Colour.red())

    # Unmute command
    @commands.command(aliases=['um'], description='Unmutes the specified user')
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member):
        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')  # Get muted role
        try:
            await member.remove_roles(muted_role)  # Remove role
            await send_embed(ctx, description=f'{member} was unbanned', colour=discord.Colour.green())
            try:
                await member.send(f'You have been unmuted in {ctx.guild.name}')
            except discord.HTTPException:  # Direct messages cannot be sent to bots
                pass
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error', colour=discord.Colour.red())
    
    # Unmute error response
    @unmute.error
    async def unmute_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}', colour=discord.Colour.red())

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
                try:
                    await ctx.reply("Nuked the Channel successfully!")
                except discord.NotFound:  # The previous channel itself could have been nuked
                    pass
            except discord.Forbidden:  # Permission error
                await send_embed(ctx, description='Permission error', colour=discord.Colour.red())
    
    # Nuke error response
    @nuke.error
    async def nuke_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}', colour=discord.Colour.red())

    # Lock command
    @commands.command(name='lock', description='Locks the current channel')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        try:
            channel = ctx.channel
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await send_embed(ctx, description=f'{channel} is in lockdown', colour=discord.Colour.red())
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error', colour=discord.Colour.red())
    
    # Lock error response
    @lock.error
    async def lock_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}', colour=discord.Colour.red())

    # Unlock command
    @commands.command(name='unlock', description='Unlocks te current channel')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        try:
            channel = ctx.channel
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await send_embed(ctx, description=f'{channel} has been unlocked', colour=discord.Colour.red())
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error', colour=discord.Colour.red())
    
    # Unlock error response
    @unlock.error
    async def unlock_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}', colour=discord.Colour.red())


# Setup
def setup(bot):
    bot.add_cog(Moderation(bot))

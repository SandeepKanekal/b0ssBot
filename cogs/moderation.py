# Moderation commands defined here
import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Ban command
    @commands.command(name='ban', description='Bans the mentioned user from the server')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason='reason not provided'):
        try:
            embed = discord.Embed(title=f'{member} was banned for {reason}', colour=discord.Colour.red())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            try:
                await member.send(f'You were banned in {ctx.guild.name} for: {reason}')
            except discord.HTTPException:  # Direct messages cannot be sent to bots
                pass
            await member.ban(reason=reason)
        except discord.Forbidden:  # Permission error
            embed = discord.Embed(title=f'Error in banning {member}',
                                  description=f'You or I may not have the permission to ban {member}',
                                  colour=discord.Colour.red())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    # Kick command
    @commands.command(name='kick', description='Kicks the mentioned user from the server')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason='no reason'):
        try:
            embed = discord.Embed(title=f'{member} was kicked for {reason}', colour=discord.Colour.red())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            try:
                await member.send(f'You were kicked in {ctx.guild.name} for {reason}')
            except discord.HTTPException:  # Direct messages cannot be sent to bots
                pass
            await member.kick(reason=reason)
        except discord.Forbidden:  # Permission error
            embed = discord.Embed(title=f'Error in kicking {member}',
                                  description=f'You or I may not have the permission to kick {member}',
                                  colour=discord.Colour.red())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

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
                    embed = discord.Embed(title=f'{member} was unbanned', colour=discord.Colour.blue())
                    embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                    try:
                        await member.send(f'You were unbanned in {ctx.guild}')
                    except discord.HTTPException:  # Direct messages cannot be sent to bots
                        pass
                    await ctx.send(embed=embed)
                    await ctx.guild.unban(user)
                    return
                except discord.Forbidden:  # Permission error
                    embed = discord.Embed(title=f'Error in unbanning {member}',
                                          description=f'You or I may not have the permission to unban {member}',
                                          colour=discord.Colour.red())
                    embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                    await ctx.send(embed=embed)
                    return

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
            embed = discord.Embed(title=f'{member} has been muted for {reason}', colour=discord.Colour.red())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            try:
                await member.send(f'You were muted in {guild.name} for {reason}')
            except discord.HTTPException:  # Direct messages cannot be sent to bots
                pass
        except discord.Forbidden:  # Permission error
            embed = discord.Embed(title=f'Error in muting {member}',
                                  description=f'You or I may not have the permission to mute {member}',
                                  colour=discord.Colour.red())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

    # Unmute command
    @commands.command(aliases=['um'], description='Unmutes the specified user')
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member):
        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')  # Get muted role
        try:
            await member.remove_roles(muted_role)  # Remove role
            embed = discord.Embed(title=f'{member} has been unmuted', colour=discord.Colour.blue())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
            try:
                await member.send(f'You have been unmuted in {ctx.guild.name}')
            except discord.HTTPException:  # Direct messages cannot be sent to bots
                pass
        except discord.Forbidden:  # Permission error
            embed = discord.Embed(title=f'Error in unmuting {member}',
                                  description=f'You or I may not have the permission to unmute {member}',
                                  colour=discord.Colour.red())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

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
            new_channel = await nuke_channel.clone(reason="Has been Nuked!")
            await nuke_channel.delete()
            await new_channel.send('**THIS CHANNEL HAS BEEN NUKED!**')
            await new_channel.send('https://tenor.com/view/explosion-mushroom-cloud-atomic-bomb-bomb-boom-gif-4464831')
            try:
                await ctx.reply("Nuked the Channel successfully!")
            except discord.NotFound:  # The previous channel itself could have been nuked
                pass

    # Lock command
    @commands.command(name='lock', description='Locks the current channel')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        channel = ctx.channel
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        embed = discord.Embed(title=f'{channel.mention} **is now in lockdown**', colour=discord.Colour.random())
        await ctx.send(embed=embed)

    # Unlock command
    @commands.command(name='unlock', description='Unlocks te current channel')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        channel = ctx.channel
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        embed = discord.Embed(title=f'{channel.mention} **has been unlocked**', colour=discord.Colour.random())
        await ctx.send(embed=embed)


# Setup
def setup(bot):
    bot.add_cog(Moderation(bot))

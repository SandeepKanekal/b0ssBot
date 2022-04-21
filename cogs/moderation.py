# Moderation commands defined here
import contextlib
import discord
import datetime
import asyncio
from sql_tools import SQL
from discord.ext import commands


# A function to make simple embeds without thumbnails, footers and authors
async def send_embed(ctx, description: str, colour: discord.Colour = discord.Colour.red()) -> None:
    # Response embed
    embed = discord.Embed(description=description, colour=colour)
    await ctx.send(embed=embed)


def modlog_enabled(guild_id) -> bool:
    # Check if modlog is enabled
    sql = SQL('b0ssbot')
    return sql.select(elements=['mode'], table='modlogs', where=f"guild_id='{guild_id}'")[0][0]


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if modlog_enabled(member.guild.id):  # Check if modlog is enabled
            sql = SQL('b0ssbot')
            channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{member.guild.id}'")[0][
                0]  # Get modlog channel id
            channel = discord.utils.get(member.guild.channels, id=int(channel_id))  # Get modlog channel

            # Make embed
            embed = discord.Embed(
                title='Member Joined',
                description=f'{member.mention} has joined the server',
                colour=discord.Colour.green()
            )
            embed.set_author(name=member.name,
                             icon_url=str(member.avatar) if member.avatar else str(member.default_avatar))
            embed.set_footer(text=f'ID: {member.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if modlog_enabled(member.guild.id):  # Check if modlog is enabled
            sql = SQL('b0ssbot')
            channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{member.guild.id}'")[0][
                0]  # Get modlog channel id
            channel = discord.utils.get(member.guild.channels, id=int(channel_id))  # Get modlog channel

            # Make embed
            embed = discord.Embed(
                title='Member Left',
                description=f'{member.name}#{member.discriminator} has left the server',
                colour=discord.Colour.red()
            )
            embed.set_author(name=member.name,
                             icon_url=str(member.avatar) if member.avatar else str(member.default_avatar))
            embed.set_footer(text=f'ID: {member.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if not modlog_enabled(message.guild.id):  # Check if modlog is enabled
            return

        sql = SQL('b0ssbot')
        channel_id = \
            sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{message.guild.id}'")[0][
                0]  # Get modlog channel id
        channel = discord.utils.get(message.guild.channels, id=int(channel_id))  # Get modlog channel

        if not message.embeds:  # Embeds cannot contain embeds
            # Make embed
            embed = discord.Embed(
                title=f'Message Deleted in #{message.channel}',
                description=message.content,
                colour=discord.Colour.green()
            )
            embed.set_author(name=message.author.name,
                             icon_url=str(message.author.avatar) if message.author.avatar else str(
                                 message.author.default_avatar))
            if message.attachments:  # If message has attachments
                embed.add_field(name='Attachments',
                                value='\n'.join([attachment.url for attachment in message.attachments]))
            embed.set_footer(text=f'ID: {message.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if not modlog_enabled(before.guild.id):  # Check if modlog is enabled
            return

        # Get modlog channel
        sql = SQL('b0ssbot')
        channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{before.guild.id}'")[0][
            0]
        channel = discord.utils.get(before.guild.channels, id=int(channel_id))

        if before.content == after.content:
            return

        if before.embeds or after.embeds:
            return

        # Make embed
        embed = discord.Embed(
            title=f'Message Edited in #{before.channel}',
            description=f'{before.author.mention} has edited a message\n**Before**: {before.content}\n**After**: {after.content}',
            colour=discord.Colour.green()
        )
        embed.set_author(name=before.author.name,
                         icon_url=str(before.author.avatar) if before.author.avatar else str(
                             before.author.default_avatar))
        embed.set_footer(text=f'ID: {before.id}')
        embed.timestamp = datetime.datetime.now()

        # Send webhook
        webhooks = await channel.guild.webhooks()
        webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
        if webhook is None:
            webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
        await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User) -> None:
        if modlog_enabled(guild.id):  # Check if modlog is enabled
            sql = SQL('b0ssbot')
            channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{guild.id}'")[0][
                0]  # Get channel id
            channel = discord.utils.get(guild.channels, id=int(channel_id))  # Get channel

            # Make embed
            embed = discord.Embed(
                title=f'Member Banned in {guild.name}',
                description=f'{user} has been banned',
                colour=discord.Colour.green()
            )
            embed.set_author(name=user.name, icon_url=str(user.avatar) if user.avatar else str(user.default_avatar))
            embed.set_footer(text=f'ID: {user.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        if modlog_enabled(guild.id):  # Check if modlog is enabled
            sql = SQL('b0ssbot')
            channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{guild.id}'")[0][
                0]  # Get channel id
            channel = discord.utils.get(guild.channels, id=int(channel_id))  # Get channel

            # Make embed
            embed = discord.Embed(
                title=f'Member Unbanned in {guild.name}',
                description=f'{user} has been unbanned',
                colour=discord.Colour.green()
            )
            embed.set_author(name=user.name, icon_url=str(user.avatar) if user.avatar else str(user.default_avatar))
            embed.set_footer(text=f'ID: {user.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.TextChannel) -> None:
        if modlog_enabled(channel.guild.id):  # Check if modlog is enabled
            sql = SQL('b0ssbot')
            channel_id = \
                sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{channel.guild.id}'")[0][
                    0]  # Get channel id
            mod_channel = discord.utils.get(channel.guild.channels, id=int(channel_id))  # Get channel

            # Make embed
            embed = discord.Embed(
                title=f'Channel Created in {channel.guild.name}',
                description=f'#{channel} has been created',
                colour=discord.Colour.green()
            )
            if channel.guild.icon:
                embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon)
            else:
                embed.set_author(name=channel.guild.name)
            embed.set_footer(text=f'ID: {channel.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await mod_channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await mod_channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel) -> None:
        if modlog_enabled(channel.guild.id):  # Check if modlog is enabled
            sql = SQL('b0ssbot')
            channel_id = \
                sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{channel.guild.id}'")[0][
                    0]  # Get channel id
            mod_channel = discord.utils.get(channel.guild.channels, id=int(channel_id))  # Get channel

            # Make embed
            embed = discord.Embed(
                title=f'Channel Deleted in {channel.guild.name}',
                description=f'#{channel} has been deleted',
                colour=discord.Colour.green()
            )
            if channel.guild.icon:
                embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon)
            else:
                embed.set_author(name=channel.guild.name)
            embed.set_footer(text=f'ID: {channel.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await mod_channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await mod_channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.TextChannel, after: discord.TextChannel) -> None:
        if modlog_enabled(before.guild.id):  # Check if modlog is enabled
            sql = SQL('b0ssbot')
            channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{before.guild.id}'")[0][
                0]  # Get channel id
            mod_channel = discord.utils.get(before.guild.channels, id=int(channel_id))  # Get channel

            # Make embed
            if before.name != after.name:
                embed = discord.Embed(
                    title=f'Channel Updated in {before.guild.name}',
                    description=f'#{before.name} has been updated to #{after.name}',
                    colour=discord.Colour.green()
                )
                if before.guild.icon:
                    embed.set_author(name=before.guild.name, icon_url=before.guild.icon)
                else:
                    embed.set_author(name=before.guild.name)
                embed.set_footer(text=f'ID: {before.id}')
                embed.timestamp = datetime.datetime.now()

                # Send webhook
                webhooks = await mod_channel.guild.webhooks()
                webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
                if webhook is None:
                    webhook = await mod_channel.create_webhook(name=f'{self.bot.user.name} Logging')
                await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging',
                                   avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        if modlog_enabled(role.guild.id):  # Check if modlog is enabled
            sql = SQL('b0ssbot')
            channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{role.guild.id}'")[0][
                0]  # Get channel id
            channel = discord.utils.get(role.guild.channels, id=int(channel_id))  # Get channel

            # Make embed
            embed = discord.Embed(
                title=f'Role Created in {role.guild.name}',
                description=f'{role.mention} has been created',
                colour=discord.Colour.green()
            )
            if channel.guild.icon:
                embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon)
            else:
                embed.set_author(name=channel.guild.name)
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        if modlog_enabled(role.guild.id):  # Check if modlog is enabled
            sql = SQL('b0ssbot')
            channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{role.guild.id}'")[0][
                0]  # Get channel id
            channel = discord.utils.get(role.guild.channels, id=int(channel_id))  # Get channel

            # Make embed
            embed = discord.Embed(
                title=f'Role Deleted in {role.guild.name}',
                description=f'{role.mention} has been deleted',
                colour=discord.Colour.green()
            )
            if role.guild.icon:
                embed.set_author(name=role.guild.name, icon_url=role.guild.icon)
            else:
                embed.set_author(name=role.guild.name)
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role) -> None:
        if modlog_enabled(
                before.guild.id) and before.name != after.name:  # Check if modlog is enabled and if the name changed
            sql = SQL('b0ssbot')
            channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{before.guild.id}'")[0][
                0]  # Get channel id
            channel = discord.utils.get(before.guild.channels, id=int(channel_id))  # Get channel

            # Make embed
            embed = discord.Embed(
                title=f'Role Updated in {before.guild.name}',
                description=f'@{before.name} has been updated to @{after.name}',
                colour=discord.Colour.green()
            )
            if before.guild.icon:
                embed.set_author(name=before.guild.name, icon_url=before.guild.icon)
            else:
                embed.set_author(name=before.guild.name)
            embed.set_footer(text=f'ID: {before.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        if modlog_enabled(before.id):  # Check if modlog is enabled
            sql = SQL('b0ssbot')
            channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{before.id}'")[0][
                0]  # Get channel id
            channel = discord.utils.get(before.channels, id=int(channel_id))  # Get channel

            # Make embed
            if before.name != after.name:
                embed = discord.Embed(
                    title='Server Name Changed',
                    description=f'{before.name} has been changed to {after.name}',
                    colour=discord.Colour.green()
                )
                if before.icon:
                    embed.set_author(name=before.name, icon_url=before.icon)
                else:
                    embed.set_author(name=before.name)
                embed.set_footer(text=f'ID: {before.id}')
                embed.timestamp = datetime.datetime.now()

                # Send webhook
                webhooks = await channel.guild.webhooks()
                webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
                if webhook is None:
                    webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
                await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging',
                                   avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        # sourcery no-metrics
        if not modlog_enabled(before.guild.id):  # Check if modlog is enabled
            return

        sql = SQL('b0ssbot')
        channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{before.guild.id}'")[0][
            0]  # Get channel id
        channel = discord.utils.get(before.guild.channels, id=int(channel_id))  # Get channel

        if before.roles != after.roles:
            role_str = ''

            # Get removed roles
            if len(after.roles) < len(before.roles):
                for role in before.roles:
                    if role not in after.roles:
                        role_str += f'{role.mention} '
                embed = discord.Embed(
                    title=f'Member Updated in {before.guild.name}',
                    description=f'Edited Member: {before.mention}\nRemoved Roles: {role_str}',
                    colour=discord.Colour.green()
                )

            # Get added roles
            else:
                for role in after.roles:
                    if role not in before.roles:
                        role_str += f'{role.mention} '
                embed = discord.Embed(
                    title=f'Member Updated in {before.guild.name}',
                    description=f'Edited Member: {before.mention}\nAdded Roles: {role_str}',
                    colour=discord.Colour.green()
                )

            if before.guild.icon:
                embed.set_author(name=before.guild.name, icon_url=before.guild.icon)
            else:
                embed.set_author(name=before.guild.name)
            embed.set_footer(text=f'ID: {before.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

        if before.nick != after.nick:  # Check if nickname was changed
            # Make embed
            embed = discord.Embed(
                title=f'Member Updated in {before.guild.name}',
                description=f'Edited Member: {before.mention}\nNickname: {before.nick} -> {after.nick}',
                colour=discord.Colour.green()
            )
            if before.guild.icon:
                embed.set_author(name=before.guild.name, icon_url=before.guild.icon)
            else:
                embed.set_author(name=before.guild.name)
            embed.set_footer(text=f'ID: {before.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    # Ban command
    @commands.command(name='ban', description='Bans the mentioned user from the server')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = 'No reason provided'):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot ban yourself', colour=discord.Colour.red())
            return
        try:
            await send_embed(ctx, description=f'{member} was banned for {reason}', colour=discord.Colour.red())
            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
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
    async def kick(self, ctx, member: discord.Member, *, reason: str = 'No reason provided'):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot kick yourself', colour=discord.Colour.red())
            return
        try:
            await send_embed(ctx, description=f'{member} was kicked for {reason}', colour=discord.Colour.red())
            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
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
        if member == f'{ctx.author}#{ctx.author.discriminator}':
            await send_embed(ctx, description='You cannot unban yourself', colour=discord.Colour.red())
            return
        banned_users = ctx.guild.bans()
        if '#' not in member:
            await send_embed(ctx, description='Invalid user')
            return
        name, discriminator = member.split('#')
        user_flag = 0
        async for ban in banned_users:
            user = ban.user
            if (user.name, user.discriminator) == (name, discriminator):
                user_flag += 1
                try:
                    await send_embed(ctx, description=f'{member} was unbanned', colour=discord.Colour.green())
                    await ctx.guild.unban(user)
                    return
                except discord.Forbidden:  # Permission error
                    await send_embed(ctx, description='Permission error')
                    return
        if user_flag == 0:
            await send_embed(ctx, description='User not found')

    # Unban error response
    @unban.error
    async def unban_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')

    # Mute command
    @commands.command(name='mute', description='Mutes the specified user')
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = 'No reason provided'):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot mute yourself', colour=discord.Colour.red())
            return
        guild = ctx.guild
        muted_role = discord.utils.get(guild.roles, name='Muted')  # Get the muted role
        if not muted_role:
            muted_role = await guild.create_role(name='Muted')  # Create a muted role if not present
            for channel in guild.channels:
                await channel.set_permissions(muted_role, speak=False,
                                              send_messages=False)  # Set permissions of the muted role
        try:
            await member.add_roles(muted_role, reason=reason)  # Add muted role
            await send_embed(ctx, description=f'{member} has been muted for {reason}', colour=discord.Colour.red())
            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                await member.send(f'You were muted in {guild.name} for {reason}')
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error')

    # Mute error response
    @mute.error
    async def mute_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')

    # Tempmute command
    @commands.command(aliases=['tm'],
                      description='Temporarily mutes the specified user\nDuration must be mentioned in minutes')
    @commands.has_permissions(manage_messages=True)
    async def tempmute(self, ctx, member: discord.Member, duration: int, *, reason: str = 'No reason provided'):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot mute yourself', colour=discord.Colour.red())
            return
        guild = ctx.guild
        muted_role = discord.utils.get(guild.roles, name='Muted')  # Get the muted role
        if not muted_role:
            muted_role = await guild.create_role(name='Muted')
            for channel in guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        try:
            await member.add_roles(muted_role, reason=reason)
            await send_embed(ctx, description=f'{member} has been muted for {reason} for {duration} seconds',
                             colour=discord.Colour.red())
            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                await member.send(f'You were muted in {guild.name} for {reason} for {duration} seconds')
            await asyncio.sleep(duration * 60)
            await member.remove_roles(muted_role, reason=reason)
            await send_embed(ctx, description=f'{member} has been unmuted', colour=discord.Colour.green())
            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                await member.send(f'You were unmuted in {guild.name}')
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error')

    # Tempmute error response
    @tempmute.error
    async def tempmute_error(self, ctx, error):
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
            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
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
                await new_channel.send(
                    'https://tenor.com/view/explosion-mushroom-cloud-atomic-bomb-bomb-boom-gif-4464831')
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
    @commands.command(name='timeout',
                      description='Timeout management command.\nmode can be `add` or `remove`\nAdd: `-timeout add @user <time> <reason>`\nRemove: `-timeout remove @user`')
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, mode: str, member: discord.Member, minutes: int = 0, *,
                      reason: str = 'No reason provided'):
        if not member:
            await send_embed(ctx, description='Please specify a user')
            return

        if mode == 'add':
            if member.timed_out:
                await send_embed(ctx, description=f'{member} is already timed out')
                return

            if not minutes:
                await send_embed(ctx, description='Mention a value in minutes above 0')
                return

            try:
                duration = datetime.timedelta(minutes=minutes)
                await member.timeout_for(duration=duration, reason=reason)
                embed = discord.Embed(
                    description=f'{member.mention} has been timed out for {minutes} {"minute" if minutes == 1 else "minutes"}. Reason: {reason}',
                    colour=discord.Colour.green()
                )
                await ctx.send(embed=embed)
                with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                    await member.send(
                        f'You were timed out in {ctx.guild.name} for {minutes} {"minute" if minutes == 1 else "minutes"}. Reason: {reason}')

            except discord.Forbidden:  # Permission error
                await send_embed(ctx, description='Permission error')

        elif mode == 'remove':
            if not member.timed_out:
                await send_embed(ctx, description=f'{member} is not timed out')
                return

            try:
                await member.remove_timeout()
                await send_embed(ctx, description=f'{member} has been removed from timeout',
                                 colour=discord.Colour.green())
                with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                    await member.send(
                        f'You were removed from timeout in {ctx.guild.name}.')

            except discord.Forbidden:  # Permission error
                await send_embed(ctx, description='Permission error')

        else:
            await send_embed(ctx, description='Invalid mode\nValid modes are `add` and `remove`')

    # Timeout error response
    @timeout.error
    async def timeout_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')

    # Modlogs command
    @commands.command(aliases=['modlog', 'ml'],
                      description='Sets the modlog channel\nMention channel for setting or updating the channel\nDon\'t mention channel to disable modlogs')
    @commands.has_permissions(manage_guild=True)
    async def modlogs(self, ctx, channel: discord.TextChannel = None):
        sql = SQL('b0ssbot')
        if channel is None and not sql.select(elements=['mode'], table='modlogs', where=f"guild_id = '{ctx.guild.id}'"):
            await send_embed(ctx, description='Please mention the channel to set the modlogs to')
            return

        if channel is None:
            await send_embed(ctx, description='Modlogs have been disabled for this server')
            sql.update(table='modlogs', column='mode', value=0, where=f"guild_id = '{ctx.guild.id}'")
            sql.update(table='modlogs', column='channel_id', value="'None'", where=f"guild_id = '{ctx.guild.id}'")
            return

        sql.update(table='modlogs', column='channel_id', value=channel.id, where=f"guild_id = '{ctx.guild.id}'")
        sql.update(table='modlogs', column='mode', value=1, where=f"guild_id = '{ctx.guild.id}'")
        await ctx.send(f'NOTE: Modlogs requires the **Send Webhooks** to be enabled in {channel.mention}')
        await send_embed(ctx, description=f'Modlogs channel has been set to {channel.mention}')

    # Modlogs error response
    @modlogs.error
    async def modlogs_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')

    # Warn command
    @commands.command(name='warn',
                      description='View: `warn view <user>`\nWarn: `warn add <user> <reason>`\nUnwarn: `warn remove <user>`')
    @commands.has_permissions(manage_guild=True)
    async def warn(self, ctx, subcommand: str, member: discord.Member, *, reason: str = 'No reason provided'):
        # sourcery no-metrics
        if subcommand not in ['view', 'add', 'remove']:
            await send_embed(ctx, description='Please specify a valid subcommand\nSubcommands: `view`, `add`, `remove`')
            return

        sql = SQL('b0ssbot')

        if subcommand == 'add':
            if not member:
                await send_embed(ctx, description='Please mention a user to warn')
                return

            if member == ctx.author:
                await send_embed(ctx, description='You can\'t warn yourself')
                return

            if not reason:
                await send_embed(ctx, description='Please specify a reason for the warn')
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
            await ctx.send(embed=embed)

        elif subcommand == 'view':
            if not member:
                await send_embed(ctx, description='Please mention a user to view their warns')
                return

            warn = sql.select(elements=['member_id', 'warns', 'reason'], table='warns',
                              where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
            if not warn:
                await send_embed(ctx, description=f'{member.mention} has no warns')
                return

            embed = discord.Embed(
                title=f'{member} has {warn[0][1]} {("warn" if warn[0][1] == 1 else "warns")}',
                description=f'Reason for latest warn: **{warn[0][2][warn[0][1] - 1]}**',
                colour=discord.Colour.red()
            ).set_author(name=member.name, icon_url=str(member.avatar) if member.avatar else str(member.default_avatar))
            await ctx.send(embed=embed)

        else:
            if not member:
                await send_embed(ctx, description='Please mention a user to unwarn')
                return

            warns = sql.select(elements=['warns', 'reason'], table='warns',
                               where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
            if not warns:
                await send_embed(ctx, description=f'{member.mention} has no warns')
                return

            if not warns[0][0] - 1:
                sql.delete(table='warns', where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
                await send_embed(ctx, description=f'{member.mention}\'s oldest warn has been removed',
                                 colour=discord.Colour.green())
                return

            reason_arr = warns[0][1]
            reason_arr.pop(0)
            reason_str = ''.join(f'\'{r}\', ' for r in reason_arr)
            sql.update(table='warns', column='warns', value=f'{warns[0][0] - 1}')
            reason_str = reason_str[:-2]
            sql.update(table='warns', column='reason', value=f'ARRAY[{reason_str}]',
                       where=f"guild_id = '{ctx.guild.id}' AND member_id = '{member.id}'")
            await send_embed(ctx, description=f'{member.mention}\'s oldest warn has been removed',
                             colour=discord.Colour.green())

    @warn.error
    async def warn_error(self, ctx, error):
        await send_embed(ctx, description=f'Error: {error}')


# Setup
def setup(bot):
    bot.add_cog(Moderation(bot))

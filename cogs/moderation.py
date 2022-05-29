# Moderation commands defined here
import contextlib
import discord
import datetime
import asyncio
from typing import List
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
                             icon_url=member.avatar or member.default_avatar)
            embed.set_footer(text=f'ID: {member.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.webhooks()
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
                             icon_url=member.avatar or member.default_avatar)
            embed.set_footer(text=f'ID: {member.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.webhooks()
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

        # Make embed
        embed = discord.Embed(
            title=f'Message Deleted in #{message.channel}',
            description=message.content.replace("''", "'") or 'No content',
            colour=discord.Colour.green()
        )
        embed.set_author(name=message.author.name,
                         icon_url=message.author.avatar or message.author.default_avatar)
        if message.attachments:  # If message has attachments
            embed.add_field(name='Attachments',
                            value='\n'.join([attachment.url for attachment in message.attachments]))
        embed.set_footer(text=f'ID: {message.id}')
        embed.timestamp = datetime.datetime.now()

        # Send webhook
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
        if webhook is None:
            webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
        await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

        if message.embeds:
            await webhook.send('Message contained embeds', embeds=message.embeds)

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

        before_content, after_content = before.content.replace("''", "'"), after.content.replace("''", "'")
        # Make embed
        embed = discord.Embed(
            title=f'Message Edited in #{before.channel}',
            description=f'{before.author.mention} has edited a message\n**Before**: {before_content}\n**After**: {after_content}',
            colour=discord.Colour.green()
        )
        embed.set_author(name=before.author.name,
                         icon_url=after.author.avatar or after.author.default_avatar)
        embed.set_footer(text=f'ID: {before.id}')
        embed.timestamp = datetime.datetime.now()

        # Send webhook
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
        if webhook is None:
            webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
        await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

        if after.embeds:
            await webhook.send('Edited message contains embeds', embeds=after.embeds)

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
            embed.set_author(name=user.name, icon_url=user.avatar or user.default_avatar)
            embed.set_footer(text=f'ID: {user.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.webhooks()
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
            embed.set_author(name=user.name, icon_url=user.avatar or user.default_avatar)
            embed.set_footer(text=f'ID: {user.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.webhooks()
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
            webhooks = await mod_channel.webhooks()
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
            webhooks = await mod_channel.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await mod_channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.TextChannel, after: discord.TextChannel) -> None:
        if not modlog_enabled(before.guild.id):
            return
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
        elif before.category != after.category:
            embed = discord.Embed(
                title=f'Channel Updated in {before.guild.name}',
                description=f'#{before.name} moved from {before.category.name} to {after.category.name}',
                colour=discord.Colour.green()
            )
        else:
            return

        if before.guild.icon:
            embed.set_author(name=before.guild.name, icon_url=before.guild.icon)
        else:
            embed.set_author(name=before.guild.name)
        embed.set_footer(text=f'ID: {before.id}')
        embed.timestamp = datetime.datetime.now()

        # Send webhook
        webhooks = await mod_channel.webhooks()
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
            webhooks = await channel.webhooks()
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
            webhooks = await channel.webhooks()
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
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        if not modlog_enabled(before.id):
            return
        sql = SQL('b0ssbot')
        channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{before.id}'")[0][
            0]  # Get channel id
        channel = discord.utils.get(before.channels, id=int(channel_id))  # Get channel
        embeds = []

        # Make embed
        if before.name != after.name:
            embed1 = discord.Embed(
                title='Server Name Changed',
                description=f'{before.name} ---> {after.name}',
                colour=discord.Colour.green()
            )
            embeds.append(embed1)

        if after.icon and before.icon != after.icon:
            embed2 = discord.Embed(
                    title='Icon Update',
                    description=f'{after.name}\'s previous icon -->',
                    colour=discord.Colour.green()
                )
            if before.icon:
                embed2.set_thumbnail(url=before.icon)
            else:
                embed2.description = f'No previous icon found for {after.name}'
            embed2.add_field(name='New Icon', valur=f'[Click here]({after.icon})')
            embeds.append(embed2)

        for embed in embeds:
            if after.icon:
                embed.set_author(name=after.name, icon_url=after.icon)
            else:
                embed.set_author(name=after.name)
            embed.set_footer(text=f'ID: {before.id}')
            embed.timestamp = datetime.datetime.now()

        # Send webhook
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
        if webhook is None:
            webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
        await webhook.send(embeds=embeds, username=f'{self.bot.user.name} Logging',
                           avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: List[discord.Emoji],
                                     after: List[discord.Emoji]) -> None:
        if not modlog_enabled(guild.id):
            return
        sql = SQL('b0ssbot')
        channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{guild.id}'")[0][
            0]  # Get channel id
        channel = discord.utils.get(guild.channels, id=int(channel_id))  # Get channel

        # Make the description string
        description = ''
        if len(before) != len(after):
            removed_emojis = [emoji for emoji in before if emoji not in after]
            added_emojis = [emoji for emoji in after if emoji not in before]
            if removed_emojis:
                description += f'{len(removed_emojis)} emoji(s) were removed:\n'
                for emoji in removed_emojis:
                    description += f'{emoji} '
                description += '\n'
            if added_emojis:
                description += f'{len(added_emojis)} emoji(s) were added:\n'
                for emoji in added_emojis:
                    description += f'{emoji} '
                description += '\n'
        else:
            for index, emoji in enumerate(before):
                if emoji.name != after[index].name:
                    description += f'`{emoji.name}`{emoji} has been updated to `{after[index].name}`{after[index]}\n'

        # Make embed
        embed = discord.Embed(
            title='Emojis Updated',
            description=description,
            colour=discord.Colour.green()
        )
        if guild.icon:
            embed.set_author(name=guild.name, icon_url=guild.icon)
        else:
            embed.set_author(name=guild.name)
        embed.set_footer(text=f'ID: {guild.id}')
        embed.timestamp = datetime.datetime.now()

        # Send webhook
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
        if webhook is None:
            webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
        await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState) -> None:
        if not modlog_enabled(member.guild.id):
            return
        sql = SQL('b0ssbot')
        channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{member.guild.id}'")[0][
            0]  # Get channel id
        channel = discord.utils.get(member.guild.channels, id=int(channel_id))  # Get channel

        # Make embed
        embed = discord.Embed(
            title=f'Voice State Updated in {member.guild.name}',
            colour=discord.Colour.green()
        )

        if before.channel is None and after.channel:
            embed.description = f'{member.mention} has joined {after.channel.mention}'
        elif before.channel and after.channel is None:  # noinspection PyUnresolvedReferences
            embed.description = f'{member.mention} has left {before.channel.mention}'
        elif before.channel != after.channel:  # noinspection PyUnresolvedReferences
            embed.description = f'{member.mention} has moved from {before.channel.mention} to {after.channel.mention}'

        embed.set_author(name=member.name, icon_url=member.avatar or member.default_avatar)
        embed.set_footer(text=f'ID: {member.id}')
        embed.timestamp = datetime.datetime.now()

        if embed.description:
            # Send webhook
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

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

            embed.set_author(name=after.name, icon_url=after.avatar or after.default_avatar)
            embed.set_footer(text=f'ID: {before.id}')
            embed.timestamp = datetime.datetime.now()

            # Send webhook
            webhooks = await channel.webhooks()
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
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User) -> None:
        embeds = []
        # Make embed
        if before.name != after.name:
            embed = discord.Embed(
                title='Username update',
                description=f'{before.name} -> {after.name}',
                colour=discord.Colour.green()
            )
            embeds.append(embed)

        if before.avatar != after.avatar:
            embed = discord.Embed(
                title='Avatar update',
                description=f'{before.mention}\'s previous avatar -->',
                colour=discord.Colour.green()
            )
            embed.set_thumbnail(url=before.avatar or before.default_avatar)
            embed.add_field(name='New Avatar', value=f'[Click here]({after.avatar or after.default_avatar})')
            embed.set_image(url=after.avatar or after.default_avatar)
            embeds.append(embed)

        if before.discriminator != after.discriminator:
            embed = discord.Embed(
                title='Discriminator update',
                description=f'{before.discriminator} -> {after.discriminator}',
                colour=discord.Colour.green()
            )
            embeds.append(embed)

        for guild in list(filter(lambda g: before in g.members, self.bot.guilds)):
            if modlog_enabled(guild.id):
                sql = SQL('b0ssbot')
                channel_id = sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{guild.id}'")[0][
                    0]  # Get channel id
                channel = discord.utils.get(guild.channels, id=int(channel_id))  # Get channel

                for embed in embeds:
                    embed.set_author(name=after.name, icon_url=after.avatar or after.default_avatar)
                    embed.set_footer(text=f'ID: {before.id}')
                    embed.timestamp = datetime.datetime.now()

                # Send webhook
                webhooks = await guild.webhooks()
                webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
                if webhook is None:
                    webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
                await webhook.send(embeds=embeds, username=f'{self.bot.user.name} Logging',
                                   avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: List[discord.Message]) -> None:
        if not modlog_enabled(messages[0].guild.id):
            return
        sql = SQL('b0ssbot')
        channel_id = \
            sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{messages[0].guild.id}'")[0][
                0]  # Get channel id
        channel = discord.utils.get(messages[0].guild.channels, id=int(channel_id))  # Get channel

        # Make embed
        embed = discord.Embed(
            title=f'{len(messages)} messages purged in #{messages[0].channel}',
            description='',
            colour=discord.Colour.red()
        )
        for message in messages:
            content = message.content.replace("''", "'")
            embed.description += f'{message.author.mention}: {content}\n'

        if messages[0].guild.icon:
            embed.set_author(name=messages[0].guild.name, icon_url=messages[0].guild.icon)
        else:
            embed.set_author(name=messages[0].guild.name)
        embed.timestamp = datetime.datetime.now()

        # Send webhook
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
        if webhook is None:
            webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
        await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    # Ban command
    @commands.command(name='ban', description='Bans the mentioned user from the server', usage='ban <user> <reason>')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = 'No reason provided'):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot ban yourself', colour=discord.Colour.red())
            return
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await send_embed(ctx, description='You cannot ban this user', colour=discord.Colour.red())
            return
        try:
            await member.ban(reason=reason)
            await send_embed(ctx, description=f'{member} was banned for {reason}', colour=discord.Colour.red())
            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                await member.send(f'You were banned in {ctx.guild.name} for: {reason}')
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error')

    # Ban error response
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("ban").usage}`')
            return
        await send_embed(ctx, description=f'Error: `{error}`')

    # Kick command
    @commands.command(name='kick', description='Kicks the mentioned user from the server', usage='kick <user> <reason>')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = 'No reason provided'):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot kick yourself', colour=discord.Colour.red())
            return
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await send_embed(ctx, description='You cannot kick this user', colour=discord.Colour.red())
            return
        try:
            await member.kick(reason=reason)
            await send_embed(ctx, description=f'{member} was kicked for {reason}', colour=discord.Colour.red())
            with contextlib.suppress(discord.HTTPException):  # A DM cannot be sent to a bot, hence the suppression
                await member.send(f'You were kicked in {ctx.guild.name} for {reason}')
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='Permission error')

    # Kick error response
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("kick").usage}`')
            return
        await send_embed(ctx, description=f'Error: `{error}`')

    # Unban command
    @commands.command(aliases=['ub'], description='Unbans the mentioned member from the server', usage='unban <user>')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        if member == f'{ctx.author}#{ctx.author.discriminator}':
            await send_embed(ctx, description='You cannot unban yourself', colour=discord.Colour.red())
            return
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await send_embed(ctx, description='You cannot unban this user', colour=discord.Colour.red())
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
                    await ctx.guild.unban(user)
                    await send_embed(ctx, description=f'{member} was unbanned', colour=discord.Colour.green())
                    return
                except discord.Forbidden:  # Permission error
                    await send_embed(ctx, description='Permission error')
                    return
        if user_flag == 0:
            await send_embed(ctx, description='User not found')

    # Unban error response
    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("unban").usage}`')
            return
        await send_embed(ctx, description=f'Error: `{error}`')

    # Mute command
    @commands.command(name='mute', description='Mutes the specified user', usage='mute <user> <reason>')
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = 'No reason provided'):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot mute yourself', colour=discord.Colour.red())
            return
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await send_embed(ctx, description='You cannot mute this user', colour=discord.Colour.red())
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
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("mute").usage}`')
            return
        await send_embed(ctx, description=f'Error: `{error}`')

    # Tempmute command
    @commands.command(aliases=['tm'],
                      description='Temporarily mutes the specified user\nDuration must be mentioned in minutes',
                      usage='tempmute <user> <duration> <reason>')
    @commands.has_permissions(manage_messages=True)
    async def tempmute(self, ctx, member: discord.Member, duration: int, *, reason: str = 'No reason provided'):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot mute yourself', colour=discord.Colour.red())
            return
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await send_embed(ctx, description='You cannot mute this user', colour=discord.Colour.red())
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
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("tempmute").usage}`')
            return
        await send_embed(ctx, description=f'Error: `{error}`')

    # Unmute command
    @commands.command(aliases=['um'], description='Unmutes the specified user', usage='unmute <user>')
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member):
        if member == ctx.author:
            await send_embed(ctx, description='You cannot unmute yourself', colour=discord.Colour.red())
            return
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await send_embed(ctx, description='You cannot unmute this user', colour=discord.Colour.red())
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
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("unmute").usage}`')
            return
        await send_embed(ctx, description=f'Error: `{error}`')

    # Nuke command
    @commands.command(aliases=['nk'], description='Nukes the mentioned text channel', usage='nuke <channel>')
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        sql = SQL('b0ssbot')
        if channel is None:
            await ctx.send('Please mention the text channel to be nuked')
            return
        try:
            nuke_channel = discord.utils.get(ctx.guild.channels, id=channel.id)  # Get the channel to be nuked
        except commands.errors.ChannelNotFound:
            await send_embed(ctx, description='Channel not found')
            return

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
            return

        if sql.select(elements=['*'], table='modlogs', where=f"guild_id = '{ctx.guild.id}' AND channel_id = '{nuke_channel.id}'"):
            sql.update(table='modlogs', column='channel_id', value=f"'{new_channel.id}'", where=f"guild_id = '{ctx.guild.id}' AND channel_id = '{nuke_channel.id}'")

    # Nuke error response
    @nuke.error
    async def nuke_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: {self.bot.get_command("nuke").usage}')
            return
        await send_embed(ctx, description=f'Error: `{error}`')

    # Lock command
    @commands.command(name='lock', description='Locks the current channel', usage='lock')
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
        await send_embed(ctx, description=f'Error: `{error}`')

    # Unlock command
    @commands.command(name='unlock', description='Unlocks te current channel', usage='unlock')
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
        await send_embed(ctx, description=f'Error: `{error}`')

    # Modlogs command
    @commands.command(aliases=['modlog', 'ml'],
                      description='Sets the modlog channel\nMention channel for setting or updating the channel\nDon\'t mention channel to disable modlogs',
                      usage='modlogs <channel>')
    @commands.has_permissions(manage_guild=True)
    async def modlogs(self, ctx, channel: discord.TextChannel = None):
        sql = SQL('b0ssbot')
        try:
            mod_channel = discord.utils.get(ctx.guild.text_channels, id=int(
                sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id = '{ctx.guild.id}'")[0][0]))
        except ValueError:
            mod_channel = None

        if channel is None and not int(
                sql.select(elements=['mode'], table='modlogs', where=f"guild_id = '{ctx.guild.id}'")[0][0]):
            await send_embed(ctx, description='Please mention the channel to set the modlogs to')
            return

        if channel is None:
            await send_embed(ctx, description='Modlogs have been disabled for this server')
            sql.update(table='modlogs', column='mode', value=0, where=f"guild_id = '{ctx.guild.id}'")
            sql.update(table='modlogs', column='channel_id', value="'None'", where=f"guild_id = '{ctx.guild.id}'")

            # Delete webhook
            if mod_channel:
                webhooks = await mod_channel.webhooks()
                if webhook := discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging'):
                    await webhook.delete(reason='Modlogs disabled')
            return

        sql.update(table='modlogs', column='channel_id', value=channel.id, where=f"guild_id = '{ctx.guild.id}'")
        sql.update(table='modlogs', column='mode', value=1, where=f"guild_id = '{ctx.guild.id}'")
        await ctx.send(f'NOTE: Modlogs requires the **Send Webhooks** to be enabled in {channel.mention}')
        await send_embed(ctx, description=f'Modlogs channel has been set to {channel.mention}')

        if mod_channel and channel:  # Delete previous webhook
            webhooks = await mod_channel.webhooks()
            if webhook := discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging'):
                await webhook.delete(reason='Modlogs channel updated')

    # Modlogs error response
    @modlogs.error
    async def modlogs_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await send_embed(ctx,
                             description=f'Invalid channel\n\nProper Usage: `{self.bot.get_command("modlogs").usage}`')

        elif isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("modlogs").usage}`')

        else:
            await send_embed(ctx, description=f'Error: `{error}`')


# Setup
def setup(bot):
    bot.add_cog(Moderation(bot))

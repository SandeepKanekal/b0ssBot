# Moderation commands defined here
import contextlib
import discord
import datetime
import asyncio
from sql_tools import SQL
from tools import convert_to_unix_time
from discord.ext import commands


# A function to make simple embeds without thumbnails, footers and authors
async def send_embed(ctx, description: str, colour: discord.Colour = discord.Colour.red()) -> None:
    """
    Sends an embed with the specified description
    
    :param ctx: The context of the command
    :param description: The description of the embed
    :param colour: The colour of the embed
    
    :type ctx: commands.Context
    :type description: str
    :type colour: discord.Colour
    
    :return: None
    :rtype: None
    """
    embed = discord.Embed(description=description, colour=colour)
    await ctx.send(embed=embed)


def modlog_enabled(guild_id: int) -> bool:
    """
    Checks if the modlog is enabled for the guild
    
    :param guild_id: The id of the guild

    :type guild_id: int

    :return: True if the modlog is enabled, False otherwise
    :rtype: bool
    """
    sql = SQL('b0ssbot')
    return sql.select(elements=['mode'], table='modlogs', where=f"guild_id='{guild_id}'")[0][0]


def get_mod_channel(guild: discord.Guild) -> discord.TextChannel:
    """
    Gets the modlog channel for the guild
    
    :param guild: The guild
    
    :type guild: discord.Guild
    
    :return: The modlog channel
    :rtype: discord.TextChannel
    """
    sql = SQL('b0ssbot')
    return discord.utils.get(guild.text_channels, id=int(
        sql.select(elements=['channel_id'], table='modlogs', where=f"guild_id='{guild.id}'")[0][0]))


async def send_webhook(channel: discord.TextChannel, embed: discord.Embed, bot: commands.Bot) -> None:
    """
    Sends a webhook to the specified channel

    :param channel: The channel to send the webhook to
    :param embed: The embed to send to the webhook
    :param bot: The bot
    
    :type channel: discord.TextChannel
    :type embed: discord.Embed
    :type bot: commands.Bot
    
    :return: None
    :rtype: None
    """
    webhooks = await channel.webhooks()
    webhook = discord.utils.get(webhooks, name=f'{bot.user.name} Logging')
    if webhook is None:
        webhook = await channel.create_webhook(name=f'{bot.user.name} Logging')
    await webhook.send(embed=embed, username=f'{bot.user.name} Logging', avatar_url=bot.user.avatar)


class Moderation(commands.Cog):
    def __init__(self, bot):
        """
        Initialises the Cog
        
        :param bot: The bot
        
        :type bot: commands.Bot
        
        :return: None
        :rtype: None
        """
        self.bot = bot  # type: commands.Bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        Event listener for when a member joins the server
        
        :param member: The member that joined the server
        
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        if not modlog_enabled(member.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(member.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title='Member Joined',
            description=f'{member.mention} has joined the server',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=member.name, icon_url=member.display_avatar)
        embed.set_footer(text=f'ID: {member.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """
        Event listener for when a member leaves the server
        
        :param member: The member that left the server
        
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        if not modlog_enabled(member.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(member.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title='Member Left',
            description=f'{member.name}#{member.discriminator} has left the server',
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=member.name, icon_url=member.display_avatar)
        embed.set_footer(text=f'ID: {member.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """
        Event listener for when a message is deleted
        
        :param message: The message that was deleted
        
        :type message: discord.Message
        
        :return: None
        :rtype: None
        """
        if not modlog_enabled(message.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(message.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Message Deleted in #{message.channel}',
            description=message.content.replace("''", "'") or 'No content',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=message.author.name,
                         icon_url=message.author.avatar or message.author.default_avatar)
        if message.attachments:  # If message has attachments
            embed.add_field(name='Attachments',
                            value='\n'.join([attachment.url for attachment in message.attachments]))
        embed.set_footer(text=f'ID: {message.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

        if message.embeds:
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(content='Message contained embeds', embeds=message.embeds,
                               username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """
        Event listener for when a message is edited
        
        :param before: The message before the edit
        :param after: The message after the edit

        :type before: discord.Message
        :type after: discord.Message

        :return: None
        :rtype: None
        """
        if not modlog_enabled(before.guild.id):  # Check if modlog is enabled
            return

        # Get modlog channel
        channel = get_mod_channel(before.guild)

        if before.content == after.content:
            return

        before_content, after_content = before.content.replace("''", "'"), after.content.replace("''", "'")
        # Make embed
        embed = discord.Embed(
            title=f'Message Edited in #{before.channel}',
            description=f'{before.author.mention} has edited a message\n**Before**: {before_content}\n**After**: {after_content}',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=before.author.name, icon_url=after.author.display_avatar)
        embed.set_footer(text=f'ID: {before.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

        if after.embeds:
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send('Edited message contains embeds', embeds=after.embeds)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User) -> None:
        """
        Event listener for when a member is banned
        
        :param guild: The guild the member was banned from
        :param user: The user that was banned
        
        :type guild: discord.Guild
        :type user: discord.User
        
        :return: None
        :rtype: None
        """
        if not modlog_enabled(guild.id):  # Check if modlog is enabled
            return

        # Get modlog channel
        channel = get_mod_channel(guild)

        # Make embed
        embed = discord.Embed(
            title=f'Member Banned in {guild.name}',
            description=f'{user} has been banned',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=user.name, icon_url=user.display_avatar)
        embed.set_footer(text=f'ID: {user.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        """
        Event listener for when a member is unbanned
        
        :param guild: The guild the member was unbanned from
        :param user: The user that was unbanned
        
        :type guild: discord.Guild
        :type user: discord.User
        
        :return: None
        :rtype: None
        """
        if not modlog_enabled(guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(guild)  # Get modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Member Unbanned in {guild.name}',
            description=f'{user} has been unbanned',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=user.name, icon_url=user.display_avatar)
        embed.set_footer(text=f'ID: {user.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.TextChannel) -> None:
        """
        Event listener for when a channel is created
        
        :param channel: The channel that was created
        
        :type channel: discord.TextChannel
        
        :return: None
        :rtype: None
        """
        if not modlog_enabled(channel.guild.id):  # Check if modlog is enabled
            return

        mod_channel = get_mod_channel(channel.guild)  # Get modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Channel Created in {channel.guild.name}',
            description=f'#{channel} has been created',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon or discord.Embed.Empty)
        embed.set_footer(text=f'ID: {channel.id}')

        # Send webhook
        await send_webhook(mod_channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel) -> None:
        """
        Event listener for when a channel is deleted
        
        :param channel: The channel that was deleted
        
        :type channel: discord.TextChannel
        
        :return: None
        :rtype: None
        """
        if not modlog_enabled(channel.guild.id):  # Check if modlog is enabled
            return

        mod_channel = get_mod_channel(channel.guild)  # Get modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Channel Deleted in {channel.guild.name}',
            description=f'#{channel} has been deleted',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon or discord.Embed.Empty)
        embed.set_footer(text=f'ID: {channel.id}')

        # Send webhook
        await send_webhook(mod_channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.TextChannel, after: discord.TextChannel) -> None:
        """
        Event listener for when a channel is updated
        
        :param before: The channel before the update
        :param after: The channel after the update
        
        :type before: discord.TextChannel
        :type after: discord.TextChannel
        
        :return: None
        :rtype: None
        """
        if not modlog_enabled(before.guild.id):  # Check if modlog is enabled
            return

        mod_channel = get_mod_channel(before.guild)  # Get modlog channel

        # Make embed
        if before.name != after.name:
            embed = discord.Embed(
                title=f'Channel Updated in {before.guild.name}',
                description=f'#{before.name} has been updated to #{after.name}',
                colour=discord.Colour.green(),
                timestamp=datetime.datetime.now()
            )
        elif before.category != after.category:
            embed = discord.Embed(
                title=f'Channel Updated in {before.guild.name}',
                description=f'#{before.name} moved from {before.category.name} to {after.category.name}',
                colour=discord.Colour.green(),
                timestamp=datetime.datetime.now()
            )
        else:
            return

        embed.set_author(name=before.guild.name, icon_url=before.guild.icon or discord.Embed.Empty)
        embed.set_footer(text=f'ID: {before.id}')

        # Send webhook
        webhooks = await mod_channel.webhooks()
        webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
        if webhook is None:
            webhook = await mod_channel.create_webhook(name=f'{self.bot.user.name} Logging')
        await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging',
                           avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        """
        Event listener for when a role is created
        
        :param role: The role that was created
        
        :type role: discord.Role
        
        :return: None
        :rtype: None
        """
        if not modlog_enabled(role.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(role.guild)  # Get modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Role Created in {role.guild.name}',
            description=f'{role.mention} has been created',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        ).set_author(name=role.guild.name, icon_url=role.guild.icon or discord.Embed.Empty)

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """
        Event listener for when a role is deleted
        
        :param role: The role that was deleted

        :type role: discord.Role

        :return: None
        :rtype: None
        """
        if not modlog_enabled(role.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(role.guild)  # Get modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Role Deleted in {role.guild.name}',
            description=f'{role.mention} has been deleted',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        ).set_author(name=role.guild.name, icon_url=role.guild.icon or discord.Embed.Empty)

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role) -> None:
        """
        Event listener for when a role is updated
        
        :param before: The role before the update
        :param after: The role after the update
        
        :type before: discord.Role
        :type after: discord.Role
        
        :return: None
        :rtype: None
        """
        if not modlog_enabled(before.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(before.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Role Updated in {before.guild.name}',
            description='',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        )

        if before.name != after.name:
            embed.description += f'{after.mention}\'s name changed from {before.name} to {after.name}\n'

        if before.colour != after.colour:
            embed.description += f'{after.mention}\'s colour changed from {before.colour} to {after.colour}\n'

        if before.permissions != after.permissions:
            previous_permissions = [perm[0].replace('_', ' ').replace('guild', 'server').title() for perm in
                                    before.permissions if perm[1]]
            new_permissions = [perm[0].replace('_', ' ').replace('guild', 'server').title() for perm in
                               after.permissions if perm[1]]
            changed_permissions = [perm for perm in new_permissions if
                                   perm not in previous_permissions] if new_permissions > previous_permissions else [
                perm for perm in previous_permissions if perm not in new_permissions]
            embed.description += f'{after.mention} {"can now" if previous_permissions < new_permissions else "can no more"} `{", ".join(changed_permissions)}`\n'

        if before.hoist != after.hoist:
            embed.description += f'{after.mention}\'s hoist changed from {before.hoist} to {after.hoist}\n'

        if before.mentionable != after.mentionable:
            embed.description += f'{after.mention}\'s mentionable changed from {before.mentionable} to {after.mentionable}\n'

        if not embed.description:
            return

        embed.set_author(name=before.guild.name, icon_url=before.guild.icon or discord.Embed.Empty)
        embed.set_footer(text=f'ID: {before.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        """
        Event listener for when a guild is updated

        :param before: The guild before the update
        :param after: The guild after the update

        :type before: discord.Guild
        :type after: discord.Guild

        :return: None
        :rtype: None
        """
        if not modlog_enabled(before.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(before)  # Get the modlog channel
        embeds = []

        # Make embed
        if before.name != after.name:
            embed1 = discord.Embed(
                title='Server Name Changed',
                description=f'{before.name} ---> {after.name}',
                colour=discord.Colour.green(),
                timestamp=datetime.datetime.now()
            )
            embeds.append(embed1)

        if after.icon and before.icon != after.icon:
            embed2 = discord.Embed(
                title='Icon Update',
                description=f'{after.name}\'s previous icon -->',
                colour=discord.Colour.green(),
                timestamp=datetime.datetime.now()
            )
            if before.icon:
                embed2.set_thumbnail(url=before.icon)
            else:
                embed2.description = f'No previous icon found for {after.name}'
            embed2.add_field(name='New Icon', value=f'[Click here]({after.icon})')
            embed2.set_image(url=after.icon)
            embeds.append(embed2)

        for embed in embeds:
            embed.set_author(name=before.name, icon_url=after.icon or discord.Embed.Empty)
            embed.set_footer(text=f'ID: {before.id}')

        # Send webhook
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
        if webhook is None:
            webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
        await webhook.send(embeds=embeds, username=f'{self.bot.user.name} Logging',
                           avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: list[discord.Emoji],
                                     after: list[discord.Emoji]) -> None:
        """
        Event listener for when a guild's emojis are updated

        :param guild: The guild
        :param before: The emojis before the update
        :param after: The emojis after the update

        :type guild: discord.Guild
        :type before: list[discord.Emoji]
        :type after: list[discord.Emoji]

        :return: None
        :rtype: None
        """
        if not modlog_enabled(guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(guild)

        # Make the description string
        description = ''
        if len(before) > len(after):
            removed_emojis = [emoji for emoji in before if emoji not in after]
            emoji_str = "\n".join([f"{emoji.name} ---> ({emoji.url})" for emoji in removed_emojis])
            description += f'{guild.name} removed the following emojis:\n\n{emoji_str}\n'

        elif len(before) < len(after):
            added_emojis = [emoji for emoji in after if emoji not in before]
            emoji_str = "\n".join([f"{emoji.name} ---> ({emoji.url})" for emoji in added_emojis])
            description += f'{guild.name} added the following emojis:\n\n{emoji_str}\n'

        else:
            description += '\n'.join(
                [f'`{emoji.name}`{emoji} has been updated to `{after[index].name}`{after[index]}' for index, emoji in
                 enumerate(before) if emoji.name != after[index].name]
            )

        # Make embed
        embed = discord.Embed(
            title='Emojis Updated',
            description=description,
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=guild.name, icon_url=guild.icon or discord.Embed.Empty)
        embed.set_footer(text=f'ID: {guild.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState) -> None:
        if not modlog_enabled(member.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(member.guild)

        # Make embed
        embed = discord.Embed(
            title=f'Voice State Updated in {member.guild.name}',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        )

        if before.channel is None and after.channel:
            embed.description = f'{member.mention} has joined {after.channel.mention}'
        elif before.channel and after.channel is None:  # noinspection PyUnresolvedReferences
            embed.description = f'{member.mention} has left {before.channel.mention}'
        elif before.channel != after.channel:  # noinspection PyUnresolvedReferences
            embed.description = f'{member.mention} has moved from {before.channel.mention} to {after.channel.mention}'

        embed.set_author(name=member.name, icon_url=member.display_avatar)
        embed.set_footer(text=f'ID: {member.id}')

        if embed.description:
            # Send webhook
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """
        Event listener for when a member's data is updated
        
        :param before: The member before the update
        :param after: The member after the update
        
        :type before: discord.Member
        :type after: discord.Member
        
        :return: None
        :rtype: None
        """
        # sourcery skip: low-code-quality
        if not modlog_enabled(before.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(before.guild)  # Get the modlog channel

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
                    colour=discord.Colour.green(),
                    timestamp=datetime.datetime.now()
                )

            # Get added roles
            else:
                for role in after.roles:
                    if role not in before.roles:
                        role_str += f'{role.mention} '
                embed = discord.Embed(
                    title=f'Member Updated in {before.guild.name}',
                    description=f'Edited Member: {before.mention}\nAdded Roles: {role_str}',
                    colour=discord.Colour.green(),
                    timestamp=datetime.datetime.now()
                )

            embed.set_author(name=after.name, icon_url=after.display_avatar)
            embed.set_footer(text=f'ID: {before.id}')

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
                colour=discord.Colour.green(),
                timestamp=datetime.datetime.now()
            )
            if before.guild.icon:
                embed.set_author(name=before.guild.name, icon_url=before.guild.icon)
            else:
                embed.set_author(name=before.guild.name)
            embed.set_footer(text=f'ID: {before.id}')

            # Send webhook
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embed=embed, username=f'{self.bot.user.name} Logging', avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User) -> None:
        """
        Event listener for when a user's data is updated
        
        :param before: The user before the update
        :param after: The user after the update
        
        :type before: discord.User
        :type after: discord.User
        
        :return: None
        :rtype: None
        """
        embeds = []
        # Make embed
        if before.name != after.name:
            embed = discord.Embed(
                title='Username update',
                description=f'{before.name} -> {after.name}',
                colour=discord.Colour.green(),
                timestamp=datetime.datetime.now()
            )
            embeds.append(embed)

        if before.avatar != after.avatar:
            embed = discord.Embed(
                title='Avatar update',
                description=f'{before.mention}\'s previous avatar -->',
                colour=discord.Colour.green(),
                timestamp=datetime.datetime.now()
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
            if not modlog_enabled(guild.id):
                continue

            channel = get_mod_channel(guild)

            for embed in embeds:
                embed.set_author(name=after.name, icon_url=after.display_avatar)
                embed.set_footer(text=f'ID: {before.id}')

            # Send webhook
            webhooks = await guild.webhooks()
            webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} Logging')
            if webhook is None:
                webhook = await channel.create_webhook(name=f'{self.bot.user.name} Logging')
            await webhook.send(embeds=embeds, username=f'{self.bot.user.name} Logging',
                               avatar_url=self.bot.user.avatar)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]) -> None:
        """
        Event listener for when a bulk message delete occurs
        
        :param messages: The messages that were deleted
        
        :type messages: list[discord.Message]
        
        :return: None
        :rtype: None
        """
        if not modlog_enabled(messages[0].guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(messages[0].guild)  # Get modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'{len(messages)} messages purged in #{messages[0].channel}',
            description='',
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.now()
        )
        for message in messages:
            content = message.content.replace("''", "'")
            embed.description += f'{message.author.mention}: {content}\n'

        embed.set_author(name=messages[0].guild.name, icon_url=messages[0].guild.icon or discord.Embed.Empty)

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild: discord.Guild, before: list[discord.Sticker],
                                       after: list[discord.Sticker]) -> None:
        """
        Event listener for when a guild's stickers are updated
        
        :param guild: The guild that the stickers were updated in
        :param before: The stickers before the update
        :param after: The stickers after the update

        :type guild: discord.Guild
        :type before: list[discord.Sticker]
        :type after: list[discord.Sticker]

        :return: None
        :rtype: None
        """
        if not modlog_enabled(guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(guild)

        # Make embed
        embed = discord.Embed(
            title=f'Stickers updated in {guild.name}',
            description='',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        ).set_author(name=guild.name, icon_url=guild.icon or discord.Embed.Empty).set_footer(text=f'ID: {guild.id}')

        if len(before) > len(after):
            removed_stickers = [sticker for sticker in before if sticker not in after]
            embed.description += f'Stickers removed: {", ".join([f"`{sticker.name}`" for sticker in removed_stickers])}\n'

        elif len(before) < len(after):
            added_stickers = [sticker for sticker in after if sticker not in before]
            embed.description += f'Stickers added: {", ".join([f"`{sticker.name}`" for sticker in added_stickers])}\n'

        else:
            embed.description += '\n'.join(
                [f'`{sticker.name}` has been updated to `{after[index].name}`' for index, sticker in
                 enumerate(before) if sticker.name != after[index].name]
            )

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """
        Event listener for when a thread is created
        
        :param thread: The thread that was created
        
        :type thread: discord.Thread

        :return: None
        :rtype: None
        """
        if not modlog_enabled(thread.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(thread.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Thread created in {thread.parent.name}',
            description=f'{thread.mention} has been created in {thread.parent.mention}',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        ).set_author(name=thread.guild.name, icon_url=thread.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {thread.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread) -> None:
        """
        Event listener for when a thread is deleted
        
        :param thread: The thread that was deleted
        
        :type thread: discord.Thread

        :return: None
        :rtype: None
        """
        if not modlog_enabled(thread.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(thread.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Thread deleted in {thread.parent.name}',
            description=f'{thread.name} has been deleted in {thread.parent.mention}',
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.now()
        ).set_author(name=thread.guild.name, icon_url=thread.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {thread.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread) -> None:
        """
        Event listener for when a thread is updated
        
        :param before: The thread before the update
        :param after: The thread after the update

        :type before: discord.Thread
        :type after: discord.Thread

        :return: None
        :rtype: None
        """
        if not modlog_enabled(before.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(before.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Thread updated in {before.parent.name}',
            description='',
            colour=discord.Colour.gold(),
            timestamp=datetime.datetime.now()
        ).set_author(name=before.guild.name, icon_url=before.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {before.id}')

        if before.name != after.name:
            embed.description += f'Name changed from `{before.name}` to `{after.name}`\n'
        if before.archived != after.archived:
            embed.description += f'{before.name} has been {"archived" if after.archived else "unarchived"}\n'

        if not embed.description:
            return

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_thread_remove(self, thread: discord.Thread) -> None:
        """
        Event listener for when a thread is removed
        
        :param thread: The thread that was removed
        
        :type thread: discord.Thread

        :return: None
        :rtype: None
        """
        if not modlog_enabled(thread.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(thread.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Thread removed from {thread.parent.name}',
            description=f'{thread.name} has been removed from {thread.parent.mention}',
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.now()
        ).set_author(name=thread.guild.name, icon_url=thread.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {thread.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_thread_join(self, thread: discord.Thread) -> None:
        """
        Event listener for when a thread is unarchived.

        :param thread: The thread that was unarchived

        :type thread: discord.Thread

        :return: None
        :rtype: None
        """
        if not modlog_enabled(thread.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(thread.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title=f'Thread unarchived in {thread.parent.name}',
            description=f'{thread.name} has been unarchived in {thread.parent.mention}',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        ).set_author(name=thread.guild.name, icon_url=thread.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {thread.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_thread_member_join(self, member: discord.Member) -> None:
        """
        Event listener for when a member joins a thread.

        :param member: The member that joined the thread

        :type member: discord.Member

        :return: None
        :rtype: None
        """
        if not modlog_enabled(member.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(member.guild)

        # Make embed
        embed = discord.Embed(
            title=f'Member joined thread in #{member.thread.parent.name}',
            description=f'{member.mention} has joined {member.thread.mention}',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        ).set_author(name=member.guild.name, icon_url=member.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {member.thread.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member: discord.Member) -> None:
        """
        Event listener for when a member leaves a thread.

        :param member: The member that left the thread

        :type member: discord.Member

        :return: None
        :rtype: None
        """
        if not modlog_enabled(member.guild.id):
            return

        channel = get_mod_channel(member.guild)

        # Make embed
        embed = discord.Embed(
            title=f'Member left thread in #{member.thread.parent.name}',
            description=f'{member.mention} has left {member.thread.mention}',
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.now()
        ).set_author(name=member.guild.name, icon_url=member.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {member.thread.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite) -> None:
        """
        Event listener for when an invite is created.

        :param invite: The invite that was created

        :type invite: discord.Invite

        :return: None
        :rtype: None
        """
        if not modlog_enabled(invite.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(invite.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title='Invite created',
            description=f'{invite.inviter.mention} created an invite to {invite.guild.name}',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        ).set_author(name=invite.guild.name, icon_url=invite.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {invite.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite) -> None:
        """
        Event listener for when an invite is deleted.

        :param invite: The invite that was deleted

        :type invite: discord.Invite

        :return: None
        :rtype: None
        """
        if not modlog_enabled(invite.guild.id):
            return

        channel = get_mod_channel(invite.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title='Invite deleted',
            description=f'An invite created by {invite.inviter.mention} has been deleted',
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.now()
        ).set_author(name=invite.guild.name, icon_url=invite.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {invite.id}')

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent) -> None:
        """
        Event listener for when a scheduled event is created.

        :param event: The scheduled event that was created

        :type event: discord.ScheduledEvent

        :return: None
        :rtype: None
        """
        if not modlog_enabled(event.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(event.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title='Scheduled event created',
            description=f'{event.name} created in {event.guild.name}.\nStart: {convert_to_unix_time(event.start_time.strftime("%Y-%m-%d %H:%M:%S:%f"))}',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        ).set_author(name=event.guild.name, icon_url=event.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {event.guild.id}').set_thumbnail(url=event.cover or discord.Embed.Empty)
        embed.description += f', End: {convert_to_unix_time(event.end_time.strftime("%Y-%m-%d %H:%M:%S:%f"))}' if event.end_time else ''

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent) -> None:
        """
        Event listener for when a scheduled event is deleted.

        :param event: The scheduled event that was deleted

        :type event: discord.ScheduledEvent

        :return: None
        :rtype: None
        """
        if not modlog_enabled(event.guild.id):  # Check if modlog is enabled
            return

        channel = get_mod_channel(event.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title='Scheduled event deleted',
            description=f'{event.name} deleted in {event.guild.name}',
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.now()
        ).set_author(name=event.guild.name, icon_url=event.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {event.guild.id}').set_thumbnail(url=event.cover or discord.Embed.Empty)

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    # @commands.Cog.listener()
    # async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent) -> None:
    #     """
    #     Event listener for when a scheduled event is updated.

    #     :param before: The scheduled event before the update
    #     :param after: The scheduled event after the update

    #     :type before: discord.ScheduledEvent
    #     :type after: discord.ScheduledEvent

    #     :return: None
    #     :rtype: None
    #     """
    #     if not modlog_enabled(after.guild.id):
    #         return

    #     channel = get_mod_channel(after.guild)  # Get the modlog channel

    #     # Make embed
    #     embed = discord.Embed(
    #         title='Scheduled event updated',
    #         description='',
    #         colour=discord.Colour.green(),
    #         timestamp=datetime.datetime.now()
    #     ).set_author(name=after.guild.name, icon_url=after.guild.icon or discord.Embed.Empty).set_footer(text=f'ID: {after.guild.id}').set_thumbnail(url=after.cover or discord.Embed.Empty)

    #     if before.name != after.name:
    #         embed.description += f'Name: {before.name} -> {after.name}\n'
    #     if before.start_time != after.start_time:
    #         embed.description += f'Start time: {convert_to_unix_time(before.start_time.strftime("%Y-%m-%d %H:%M:%S:%f"))} -> {convert_to_unix_time(after.start_time.strftime("%Y-%m-%d %H:%M:%S:%f"))}\n'
    #     if before.end_time and after.end_time and before.end_time != after.end_time:
    #         embed.description += f'End time: {convert_to_unix_time(before.end_time.strftime("%Y-%m-%d %H:%M:%S:%f"))} -> {convert_to_unix_time(after.end_time.strftime("%Y-%m-%d %H:%M:%S:%f"))}\n'
    #     if before.location != after.location:
    #         embed.description += f'Location: {before.location} -> {after.location}\n'

    #     if not embed.description: 
    #         return

    #     # Send webhook
    #     await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_scheduled_event_user_add(self, event: discord.ScheduledEvent, member: discord.Member) -> None:
        """
        Event listener for when a user is added to a scheduled event.

        :param event: The scheduled event that the user was added to
        :param member: The user that was added to the scheduled event

        :type event: discord.ScheduledEvent
        :type member: discord.Member

        :return: None
        :rtype: None
        """
        if not modlog_enabled(event.guild.id):
            return

        channel = get_mod_channel(event.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title='User added to scheduled event',
            description=f'{member.mention} has joined {event.name}',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        ).set_author(name=event.guild.name, icon_url=event.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {member.id}').set_thumbnail(url=event.cover or discord.Embed.Empty)

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_scheduled_event_user_remove(self, event: discord.ScheduledEvent, member: discord.Member) -> None:
        """
        Event listener for when a user is removed from a scheduled event.

        :param event: The scheduled event that the user was removed from
        :param member: The user that was removed from the scheduled event

        :type event: discord.ScheduledEvent
        :type member: discord.Member

        :return: None
        :rtype: None
        """
        if not modlog_enabled(event.guild.id):
            return

        channel = get_mod_channel(event.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title='User removed from scheduled event',
            description=f'{member.mention} has left {event.name}',
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.now()
        ).set_author(name=event.guild.name, icon_url=event.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {member.id}').set_thumbnail(url=event.cover or discord.Embed.Empty)

        # Send webhook
        await send_webhook(channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.abc.GuildChannel) -> None:
        """
        Event listener for when a webhook is created, updated or deleted.

        :param channel: The channel that the webhook was updated in

        :type channel: discord.abc.GuildChannel

        :return: None
        :rtype: None
        """
        if not modlog_enabled(channel.guild.id):
            return

        mod_channel = get_mod_channel(channel.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title='Webhook updated',
            description=f'Webhook(s) updated in {channel.mention}',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        ).set_author(name=channel.guild.name, icon_url=channel.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {channel.id}')

        # Send webhook
        await send_webhook(mod_channel, embed, self.bot)

    @commands.Cog.listener()
    async def on_integration_create(self, integration: discord.Integration) -> None:
        """
        Event listener for when an integration is created.

        :param integration: The integration that was created
        
        :type integration: discord.Integration

        :return: None
        :rtype: None
        """
        if not modlog_enabled(integration.guild.id):
            return

        mod_channel = get_mod_channel(integration.guild)  # Get the modlog channel

        # Make embed
        embed = discord.Embed(
            title='Integration created',
            description=f'Integration {integration.name} created in {integration.guild.name}\nType: {integration.type}',
            colour=discord.Colour.green(),
            timestamp=datetime.datetime.now()
        ).set_author(name=integration.guild.name, icon_url=integration.guild.icon or discord.Embed.Empty).set_footer(
            text=f'ID: {integration.id}')

        # Send webhook
        await send_webhook(mod_channel, embed, self.bot)

    # Ban command
    @commands.command(name='ban', description='Bans the mentioned user from the server', usage='ban <user> <reason>')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = 'No reason provided'):
        """
        Bans the mentioned user from the server
        
        :param ctx: The context of where the command was used
        :param member: The user to be banned
        :param reason: The reason for the ban
        
        :type ctx: commands.Context
        :type member: discord.Member
        :type reason: str

        :return: None
        :rtype: None
        """
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
            await send_embed(ctx, description='I do not have permissionto perform this action!')

    # Ban error response
    @ban.error
    async def ban_error(self, ctx, error):
        """
        Error handler for the ban command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("ban").usage}`')
            return
        if isinstance(error, commands.BadArgument):
            await send_embed(ctx, description='Invalid user provided')
            return
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to ban users')
            return

    # Kick command
    @commands.command(name='kick', description='Kicks the mentioned user from the server', usage='kick <user> <reason>')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = 'No reason provided'):
        """
        Kicks the mentioned user from the server
        
        :param ctx: The context of where the command was used
        :param member: The user to be kicked
        :param reason: The reason for the kick
        
        :type ctx: commands.Context
        :type member: discord.Member
        :type reason: str
        
        :return: None
        :rtype: None
        """
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
            await send_embed(ctx, description='I do not have permissionto perform this action!')

    # Kick error response
    @kick.error
    async def kick_error(self, ctx, error):
        """
        Error handler for the kick command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("kick").usage}`')
            return
        if isinstance(error, commands.BadArgument):
            await send_embed(ctx, description='Invalid user provided')
            return
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to kick users')
            return

    # Unban command
    @commands.command(aliases=['ub'], description='Unbans the mentioned member from the server', usage='unban <user>')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        """
        Unbans the mentioned member from the server
        
        :param ctx: The context of where the command was used
        :param member: The user to be unbanned
        
        :type ctx: commands.Context
        :type member: str
        
        :return: None
        :rtype: None
        """
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
                    await ctx.guild.unban(user)
                    await send_embed(ctx, description=f'{member} was unbanned', colour=discord.Colour.green())
                    return
                except discord.Forbidden:  # Permission error
                    await send_embed(ctx, description='I do not have permissionto perform this action!')
                    return
        if user_flag == 0:
            await send_embed(ctx, description='User not found')

    # Unban error response
    @unban.error
    async def unban_error(self, ctx, error):
        """
        Error handler for the unban command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("unban").usage}`')
            return
        if isinstance(error, commands.BadArgument):
            await send_embed(ctx, description='Invalid user provided')
            return
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to unban users')
            return

    # Mute command
    @commands.command(name='mute', description='Mutes the specified user', usage='mute <user> <reason>')
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = 'No reason provided'):
        """
        Mutes the specified user

        :param ctx: The context of where the command was used
        :param member: The user to be muted
        :param reason: The reason for the mute

        :type ctx: commands.Context
        :type member: discord.Member
        :type reason: str

        :return: None
        :rtype: None
        """
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
            await send_embed(ctx, description='I do not have permissionto perform this action!')

    # Mute error response
    @mute.error
    async def mute_error(self, ctx, error):
        """
        Error handler for the mute command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("mute").usage}`')
            return
        if isinstance(error, commands.BadArgument):
            await send_embed(ctx, description='Invalid user provided')
            return
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to mute users')
            return

    # Tempmute command
    @commands.command(aliases=['tm'],
                      description='Temporarily mutes the specified user\nDuration must be mentioned in minutes',
                      usage='tempmute <user> <duration> <reason>')
    @commands.has_permissions(manage_messages=True)
    async def tempmute(self, ctx, member: discord.Member, duration: int, *, reason: str = 'No reason provided'):
        """
        Temporarily mutes the specified user
        
        :param ctx: The context of where the command was used
        :param member: The user to be muted
        :param duration: The duration of the mute in minutes
        :param reason: The reason for the mute

        :type ctx: commands.Context
        :type member: discord.Member
        :type duration: int
        :type reason: str

        :return: None
        :rtype: None
        """
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
            await send_embed(ctx, description='I do not have permissionto perform this action!')

    # Tempmute error response
    @tempmute.error
    async def tempmute_error(self, ctx, error):
        """
        Error handler for the tempmute command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("tempmute").usage}`')
            return
        if isinstance(error, commands.BadArgument):
            await send_embed(ctx, description='Invalid user provided')
            return
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to mute users')
            return
        if isinstance(error, commands.BadUnionArgument):
            await send_embed(ctx, description='Invalid duration provided')
            return

    # Unmute command
    @commands.command(aliases=['um'], description='Unmutes the specified user', usage='unmute <user>')
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member):
        """
        Unmutes the specified user
        
        :param ctx: The context of where the command was used
        :param member: The user to be unmuted
        
        :type ctx: commands.Context
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
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
            await send_embed(ctx, description='I do not have permissionto perform this action!')

    # Unmute error response
    @unmute.error
    async def unmute_error(self, ctx, error):
        """
        Error handler for the unmute command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("unmute").usage}`')
            return
        if isinstance(error, commands.BadArgument):
            await send_embed(ctx, description='Invalid user provided')
            return
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to mute users')
            return

    # Nuke command
    @commands.command(aliases=['nk'], description='Nukes the mentioned text channel', usage='nuke <channel>')
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        """
        Nukes the mentioned text channel
        
        :param ctx: The context of where the command was used
        :param channel: The channel to be nuked
        
        :type ctx: commands.Context
        :type channel: discord.TextChannel
        
        :return: None
        :rtype: None
        """
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
            await new_channel.send('This channel has been nuked!')
            await new_channel.send(
                'https://tenor.com/view/explosion-mushroom-cloud-atomic-bomb-bomb-boom-gif-4464831')
            with contextlib.suppress(discord.NotFound):
                await ctx.reply("Nuked the Channel successfully!")
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='I do not have permissionto perform this action!')
            return

        if sql.select(elements=['*'], table='modlogs',
                      where=f"guild_id = '{ctx.guild.id}' AND channel_id = '{nuke_channel.id}'"):
            sql.update(table='modlogs', column='channel_id', value=f"'{new_channel.id}'",
                       where=f"guild_id = '{ctx.guild.id}' AND channel_id = '{nuke_channel.id}'")
            await new_channel.send(f'{new_channel.mention} will now be the modlogs channel!')

    # Nuke error response
    @nuke.error
    async def nuke_error(self, ctx, error):
        """
        Error handler for the nuke command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx,
                             description=f'Missing required argument\n\nProper Usage: `{self.bot.get_command("nuke").usage}`')
            return
        if isinstance(error, commands.BadArgument):
            await send_embed(ctx, description='Invalid channel provided')
            return
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to nuke channels')
            return

    # Lock command
    @commands.command(name='lock', description='Locks the current channel', usage='lock')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """
        Locks the current channel
        
        :param ctx: The context of where the command was used
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        try:
            channel = ctx.channel
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await send_embed(ctx, description=f'{channel} is in lockdown', colour=discord.Colour.red())
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='I do not have permissionto perform this action!')

    # Lock error response
    @lock.error
    async def lock_error(self, ctx, error):
        """
        Error handler for the lock command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to lock channels')
            return

    # Unlock command
    @commands.command(name='unlock', description='Unlocks te current channel', usage='unlock')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """
        Unlocks the current channel

        :param ctx: The context of where the command was used

        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
        try:
            channel = ctx.channel
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await send_embed(ctx, description=f'{channel} has been unlocked', colour=discord.Colour.red())
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='I do not have permissionto perform this action!')

    # Unlock error response
    @unlock.error
    async def unlock_error(self, ctx, error):
        """
        Error handler for the unlock command

        :param ctx: The context of where the command was used
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to unlock channels')
            return

    # Modlogs command
    @commands.command(aliases=['modlog', 'ml'],
                      description='Sets the modlog channel\nMention channel for setting or updating the channel\nDon\'t mention channel to disable modlogs',
                      usage='modlogs <channel>')
    @commands.has_permissions(manage_guild=True)
    async def modlogs(self, ctx, channel: discord.TextChannel = None):
        """
        Sets the modlogs channel
        
        :param ctx: The context of where the command was used
        :param channel: The channel to be set as the modlogs channel
        
        :type ctx: commands.Context
        :type channel: discord.TextChannel
        
        :return: None
        :rtype: None
        """
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
        """
        Error handler for the modlogs command
        
        :param ctx: The context of where the command was used
        :param error: The error that occurred
        
        :type ctx: commands.Context
        :type error: commands.CommandError
        
        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to manage server settings')
            return
        if isinstance(error, commands.BadArgument):
            await send_embed(ctx, description='Please mention a channel')
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx, description='Please mention a channel')
            return

    @commands.command(name='deafen', description='Deafen a member', usage='deafen <member>')
    @commands.has_permissions(deafen_members=True)
    async def deafen(self, ctx, member: discord.Member):
        """
        Deafens a member
        
        :param ctx: The context of where the command was used
        :param member: The member to be deafened
        
        :type ctx: commands.Context
        :type member: discord.Member
        
        :return: None
        :rtype: None
        """
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await send_embed(ctx, description='You cannot deafen this user', colour=discord.Colour.red())
            return

        try:
            await member.edit(deafen=True)
            await send_embed(ctx, description=f'{member.mention} has been deafened')
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='I do not have permissionto perform this action!')

    @deafen.error
    async def deafen_error(self, ctx, error):
        """
        Error handler for the deafen command

        :param ctx: The context of where the command was used
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to deafen members')
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx, description='Please mention a member')
            return
        if isinstance(error, commands.BadArgument):
            await send_embed(ctx, description='Please mention a valid member')
            return

    @commands.command(name='undeafen', description='Undeafen a member', usage='undeafen <member>')
    @commands.has_permissions(deafen_members=True)
    async def undeafen(self, ctx, member: discord.Member):
        """
        Undeafens a member
        
        :param ctx: The context of where the command was used
        :param member: The member to be undeafened
        
        :type ctx: commands.Context
        :type member: discord.Member

        :return: None
        :rtype: None
        """
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            await send_embed(ctx, description='You cannot undeafen this user', colour=discord.Colour.red())
            return

        try:
            await member.edit(deafen=False)
            await send_embed(ctx, description=f'{member.mention} has been undeafened')
        except discord.Forbidden:  # Permission error
            await send_embed(ctx, description='I do not have permissionto perform this action!')

    @undeafen.error
    async def undeafen_error(self, ctx, error):
        """
        Error handler for the undeafen command
            
        :param ctx: The context of where the command was used
        :param error: The error that occurred

        :type ctx: commands.Context
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        if isinstance(error, commands.MissingPermissions):
            await send_embed(ctx, description='You do not have permission to undeafen members')
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await send_embed(ctx, description='Please mention a member')
            return
        if isinstance(error, commands.BadArgument):
            await send_embed(ctx, description='Please mention a valid member')
            return


# Setup
def setup(bot):
    """
    Loads the cog
    
    :param bot: The bot to load the cog into
    
    :type bot: commands.Bot
    
    :return: None
    :rtype: None
    """
    bot.add_cog(Moderation(bot))

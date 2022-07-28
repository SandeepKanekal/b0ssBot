# Copyright (c) 2022 Sandeep Kanekal
# Contains all bot events
import contextlib
import os
import discord
import random
from sql_tools import SQL
from discord.ext import commands, tasks
import youtubesearchpython as youtube


def remove(nick_name: str) -> str:
    """
    Removes '[AFK]' from a nickname
    
    :param nick_name: The nickname to remove '[AFK]' from
    :type nick_name: str
    
    :return: The nickname without '[AFK]'
    :rtype: str
    """
    return " ".join(nick_name.split()[1:]) if '[AFK]' in nick_name.split() else nick_name


class Events(commands.Cog):
    def __init__(self, bot):
        """
        Initialize the cog

        :param bot: The client

        :type bot: discord.ext.commands.Bot

        :return: None
        :rtype: None
        """
        self.bot = bot  # type: commands.Bot

    # Bot activity on starting
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        Bot activity on starting

        :return: None
        :rtype: None
        """
        print('Bot is ready')
        await self.bot.change_presence(activity=discord.Game(name='The Game Of b0sses'))

        self.check_for_videos.start()
        self.clear_ytdl_cache.start()

        sql = SQL('b0ssbot')
        sql.delete(table='queue')
        sql.delete(table='loop')

    # Bot activity on receiving a message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # sourcery skip: low-code-quality
        """
        Bot activity on receiving a message

        :param message: The message

        :type message: discord.Message

        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')  # type: SQL
        if message.author.bot:  # Ignore bots
            return

        message.content = message.content.replace("'", "''")  # Replace single quotes with double quotes

        # AFKs
        if sql.select(elements=['member_id', 'guild_id', 'reason'], table='afks',
                      where=f'member_id = \'{message.author.id}\' AND guild_id = \'{message.guild.id}\''):
            # Check if the user is afk
            sql.delete(table='afks',
                       where=f'member_id = \'{message.author.id}\' and guild_id = \'{message.guild.id}\'')  # Remove the afk

            with contextlib.suppress(discord.Forbidden):
                await message.author.edit(nick=remove(message.author.display_name))  # Remove the AFK tag

            await message.reply(
                embed=discord.Embed(
                    description=f'Welcome back {message.author.mention}, I removed your AFK!',
                    colour=discord.Colour.green()
                )
            )  # Reply to the user

        # If an AFK user is mentioned, inform the author
        if message.mentions:
            for mention in message.mentions:
                if afk_user := sql.select(
                        elements=['member_id', 'guild_id', 'reason'],
                        table='afks',
                        where=f'member_id = \'{mention.id}\' and guild_id = \'{message.guild.id}\'',
                ):  # Check if the mentions contains an afk user
                    member = discord.utils.get(message.guild.members, id=int(afk_user[0][0]))  # Get the member

                    if member in message.mentions and message.guild.id == int(
                            afk_user[0][1]):  # Check if the member is mentioned

                        await message.reply(
                            embed=discord.Embed(
                                description=f'{message.author.mention}, {member.mention} is AFK!\nAFK note: {afk_user[0][2]}',
                                colour=discord.Colour.red()
                            ).set_thumbnail(url=member.avatar or member.default_avatar)
                        )  # Reply to the user

        # Ping reply
        if self.bot.user.id in message.raw_mentions and message.content != '@everyone' and message.content != '@here':
            # Ping response
            command_prefix = sql.select(elements=['prefix'], table='prefixes', where=f"guild_id = '{message.guild.id}'")
            embed = discord.Embed(
                description=f'Hi! I am **{self.bot.user.name}**! I was coded by **Dose#7204**. My prefix is **{command_prefix[0][0]}**',
                colour=self.bot.user.colour)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await message.reply(embed=embed)

        # Messageresponse
        with contextlib.suppress(IndexError):
            if response := sql.select(elements=['response'], table='message_responses',
                                      where=f"message = '{message.content.lower()}' AND guild_id = '{message.guild.id}'"
                                      )[0][0]:
                # Check for chat triggers
                await message.reply(response)

        # Markdown
        with contextlib.suppress(discord.HTTPException):
            if '[' in message.content and \
                    ']' in message.content \
                    and '(' in message.content \
                    and ')' in message.content \
                    and (message.content.split('(')[1].startswith('https://')
                         or message.content.split('(')[1].startswith('http://')) \
                    and '.' in message.content \
                    and (message.content.split('https://')[1] or message.content.split('http://')[1]):
                # Check for Markdown syntax

                webhooks = await message.channel.webhooks()
                webhook = discord.utils.get(webhooks, name='Markdown webhook')
                if webhook is None:
                    webhook = await message.channel.create_webhook(name='Markdown webhook')
                await webhook.send(message.content.replace("''", "'"), username=message.author.display_name,
                                   avatar_url=message.author.avatar)  # Send the message to the webhook
                await message.delete()  # Delete original message

    @commands.Cog.listener()
    async def on_command(self, ctx) -> None:
        """
        Bot activity on receiving a command

        :param ctx: The context

        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')  # type: SQL
        prefix = sql.select(elements=['prefix'], table='prefixes', where=f"guild_id = '{ctx.guild.id}'")[0][0]
        if random.choice([True, False, False, False, False, False, False, False, False,
                          False]) and ctx.command != self.bot.get_command('clear'):
            await ctx.send(f'Hello there {ctx.author.mention}! You can check all the commands of the bot using the help command. Type {prefix}help to get the response.')

    @commands.Cog.listener()
    async def on_guild_join(self, guild) -> None:
        """
        Bot activity on joining a guild
        
        :param guild: The guild

        :type guild: discord.Guild

        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        # Add the guild to the database
        sql.insert(table='prefixes', columns=['guild_id', 'prefix'], values=[f'\'{guild.id}\'', '\'-\''])
        sql.insert(table='modlogs', columns=['guild_id', 'mode', 'channel_id'],
                   values=[f"'{guild.id}'", '\'0\'', '\'None\''])

        if guild.system_channel:  # Send an informative embed to the guild's system channel
            command_prefix = sql.select(elements=['prefix'], table='prefixes', where=f"guild_id = '{guild.id}'")
            embed = discord.Embed(
                description=f'Hi! I am **{self.bot.user.name}**! I was coded by **Dose#7204**. My prefix is **{command_prefix[0][0]}**. You can change my prefix using the slash command: `/prefix`!',
                colour=self.bot.user.colour)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await guild.system_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild) -> None:
        """
        Bot activity on leaving a guild

        :param guild: The guild

        :type guild: discord.Guild

        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')
        sql.delete(table='prefixes', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='modlogs', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='afks', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='message_responses', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='youtube', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='snipes', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='warns', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='queue', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='loop', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='verifications', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='serverjoin', where=f'guild_id = \'{guild.id}\'')
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Bot activity on receiving a reaction

        :param payload: The payload

        :type payload: discord.RawReactionActionEvent

        :return: None
        :rtype: None
        """
        if payload.user_id == self.bot.user.id:
            return
        
        sql = SQL('b0ssbot')
        if not sql.select(elements=['message_id'], table='verifications', where=f'guild_id = \'{payload.guild_id}\' AND message_id = \'{payload.message_id}\''):
            return
        
        if payload.emoji.name != '✅':
            return
        
        role_id = sql.select(elements=['role_id'], table='verifications', where=f'guild_id = \'{payload.guild_id}\' AND message_id = \'{payload.message_id}\'')
        if not role_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        role = discord.utils.get(guild.roles, id=int(role_id[0][0]))
        
        unverified_role_id = sql.select(['unverified_role_id'], 'verifications', f"guild_id = '{payload.guild_id}' AND message_id = '{payload.message_id}'")[0][0]
        if unverified_role_id != 'None':
            unverified_role = discord.utils.get(guild.roles, id=int(unverified_role_id))
            await payload.member.remove_roles(unverified_role)
        
        await payload.member.add_roles(role)

        channel = discord.utils.get(guild.channels, id=int(sql.select(elements=['channel_id'], table='verifications', where=f'guild_id = \'{payload.guild_id}\' AND message_id = \'{payload.message_id}\'')[0][0]))
        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction('✅', payload.member)

        await payload.member.send(f'You are now verified in {guild.name}')

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        Bot activity on a member joining a server

        :param member: The member

        :type member: discord.Member

        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')

        if not sql.select(['*'], 'serverjoin', f"guild_id = '{member.guild.id}'"):
            return

        member_role_id = sql.select(['member_role_id'], 'serverjoin', f"guild_id = '{member.guild.id}'")[0][0]
        bot_role_id = sql.select(['bot_role_id'], 'serverjoin', f"guild_id = '{member.guild.id}'")[0][0]
        
        if member.bot and bot_role_id:
            bot_role = discord.utils.get(member.guild.roles, id=int(bot_role_id))
            await member.add_roles(bot_role)
        else:
            member_role = discord.utils.get(member.guild.roles, id=int(member_role_id))
            await member.add_roles(member_role)

    @tasks.loop(minutes=60)
    async def clear_ytdl_cache(self):
        """
        Clears the YTDL cache
        
        :return: None
        :rtype: None
        """
        os.system('youtube-dl --rm-cache-dir')  # Clearing cache to prevent 403 errors

    @tasks.loop(minutes=5)
    async def check_for_videos(self) -> None:
        """
        Check for new videos every few minutes

        :return: None
        :rtype: None
        """
        status: str = ''
        try:
            sql = SQL('b0ssbot')  # type: SQL
            status += 'Checking for videos...'

            channels = sql.select(
                elements=['channel_id', 'latest_video_id', 'guild_id', 'text_channel_id', 'channel_name', 'ping_role'],
                table='youtube')

            notifiable_channels = [channel for channel in channels if
                                   channel[1] != youtube.Playlist(youtube.playlist_from_channel_id(channel[0])).videos[0][
                                       'id']]

            for channel in notifiable_channels:
                latest_video_id = youtube.Playlist(youtube.playlist_from_channel_id(channel[0])).videos[0]['id']

                publish_time = youtube.VideosSearch(latest_video_id, limit=1).result()['result'][0]['publishedTime']
                
                if not publish_time:
                    continue

                if 'second' not in publish_time and 'seconds' not in publish_time and 'minute' not in publish_time and 'minutes' not in publish_time and 'hour' not in publish_time and 'hours' not in publish_time:
                    continue

                guild = discord.utils.get(self.bot.guilds, id=int(channel[2]))
                text_channel = discord.utils.get(guild.text_channels, id=int(channel[3]))
                ping_role = discord.utils.get(guild.roles, id=int(channel[5])) if channel[5] != 'None' else None

                webhooks = await text_channel.webhooks()
                webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} YouTube Notifier')
                if webhook is None:
                    webhook = await text_channel.create_webhook(name=f'{self.bot.user.name} YouTube Notifier')
                
                if isinstance(ping_role, discord.Role):
                    ping_string = "@everyone" if 'everyone' in ping_role.name else ping_role.mention
                else:
                    ping_string = "everyone"

                await webhook.send(
                    f'Hey {ping_string}! New video uploaded by **[{channel[4]}](https://youtube.com/channel/{channel[0]})**!\nhttps://youtube.com/watch?v={latest_video_id}',
                    username=f'{self.bot.user.name} YouTube Notifier',
                    avatar_url=self.bot.user.avatar)  # Send the message to the webhook

                sql.update(table='youtube', column='latest_video_id', value=f"'{latest_video_id}'",
                           where=f'channel_id = \'{channel[0]}\' AND guild_id = \'{guild.id}\'')  # Update the latest video id
        except Exception as e:
            status = f'An error occured in check_for_videos: {e}'
        else:
            status += " Function executed without errors!"
        finally:
            print(status)


# Setup
def setup(bot):
    """
    Loads the cog

    :param bot: The bot object
    :type bot: discord.ext.commands.Bot

    :return: None
    :rtype: None
    """
    bot.add_cog(Events(bot))

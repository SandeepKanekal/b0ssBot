# Contains all bot events
import contextlib
import os
import discord
import random
from googleapiclient.discovery import build
from sql_tools import SQL
from discord.ext import commands, tasks


def remove(nick_name: str) -> str:
    return " ".join(nick_name.split()[1:]) if '[AFK]' in nick_name.split() else nick_name


class Events(commands.Cog):
    def __init__(self, bot):
        """
        Initialize the cog

        :param bot: The client

        :type bot: discord.ext.commands.Bot
        """
        self.bot = bot  # type: commands.Bot

    # Bot activity on starting
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        Bot activity on starting

        :return: None
        """
        print('Bot is ready')
        await self.bot.change_presence(activity=discord.Game(name='The Game Of b0sses'))
        self.check_for_videos.start()
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
        """
        sql = SQL('b0ssbot')  # type: SQL
        if message.author.bot:  # Ignore bots
            return

        if "'" in message.content:
            message.content = message.content.replace("'", "''")  # Replace single quotes with double quotes

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

        if self.bot.user.id in message.raw_mentions and message.content != '@everyone' and message.content != '@here':
            # Ping response
            command_prefix = sql.select(elements=['prefix'], table='prefixes', where=f"guild_id = '{message.guild.id}'")
            embed = discord.Embed(
                description=f'Hi! I am **{self.bot.user.name}**! I was coded by **Dose#7204**. My prefix is **{command_prefix[0][0]}**',
                colour=self.bot.user.colour)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await message.reply(embed=embed)

        with contextlib.suppress(IndexError):
            if response := sql.select(elements=['response'], table='message_responses',
                                      where=f"message = '{message.content.lower()}' AND guild_id = '{message.guild.id}'"
                                      )[0][0]:
                # Check for chat triggers
                await message.reply(response)

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
        """
        sql = SQL('b0ssbot')  # type: SQL
        prefix = sql.select(elements=['prefix'], table='prefixes', where=f"guild_id = '{ctx.guild.id}'")[0][0]
        if random.choice([True, False, False, False, False, False, False, False, False,
                          False]) and ctx.command != self.bot.get_command('clear'):
            await ctx.send(random.choice(
                [f'Hey there {ctx.author.mention}! Check out the new commands: (commands here)',
                 f'Hey there {ctx.author.mention}! Check out the new egghunt! Type `**{prefix}egg**`']))

    @commands.Cog.listener()
    async def on_guild_join(self, guild) -> None:
        """
        Bot activity on joining a guild
        
        :param guild: The guild

        :type guild: discord.Guild

        :return: None
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
        """
        sql = SQL('b0ssbot')
        sql.delete(table='prefixes', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='modlogs', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='afks', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='message_responses', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='youtube', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='hourlyweather', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='snipes', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='warns', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='queue', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='loop', where=f'guild_id = \'{guild.id}\'')

    @tasks.loop(minutes=60)
    async def check_for_videos(self) -> None:
        """
        Check for new videos every hour

        :return: None
        """
        os.system('youtube-dl --rm-cache-dir')  # Clearing cache to prevent 403 errors
        sql = SQL('b0ssbot')  # type: SQL
        print('Checking for videos...')

        channel = sql.select(
            elements=['channel_id', 'latest_video_id', 'guild_id', 'text_channel_id', 'channel_name', 'ping_role'],
            table='youtube')
        youtube = build('youtube', 'v3', developerKey=os.getenv('youtube_api_key'))

        for data in channel:
            c = youtube.channels().list(part='contentDetails', id=data[0]).execute()  # type: dict
            latest_video_id = \
                youtube.playlistItems().list(playlistId=c['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
                                             part='contentDetails').execute()['items'][0]['contentDetails'][
                    'videoId']  # type: str

            if data[1] != latest_video_id:
                guild = discord.utils.get(self.bot.guilds, id=int(data[2]))  # type: discord.Guild
                text_channel = discord.utils.get(guild.text_channels, id=int(data[3]))  # type: discord.TextChannel
                ping_role = discord.utils.get(guild.roles, id=int(data[5])) if data[
                                                                                   5] != 'None' else None  # type: discord.Role | None

                webhooks = await text_channel.webhooks()
                webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} YouTube Notifier')
                if webhook is None:
                    webhook = await text_channel.create_webhook(name=f'{self.bot.user.name} YouTube Notifier')

                await webhook.send(
                    f'{f"Hey {ping_role.mention}" if ping_role else "Hey everyone"}! New video uploaded by **[{data[4]}](https://youtube.com/channel/{data[0]})**!\nhttps://youtube.com/watch?v={latest_video_id}',
                    username=f'{self.bot.user.name} YouTube Notifier',
                    avatar_url=self.bot.user.avatar)  # Send the message to the webhook

                sql.update(table='youtube', column='latest_video_id', value=f"'{latest_video_id}'",
                           where=f'channel_id = \'{data[0]}\'')  # Update the latest video id


# Setup
def setup(bot):
    """
    Loads the cog

    :param bot: The bot object
    :type bot: discord.ext.commands.Bot
    :return: None
    """
    bot.add_cog(Events(bot))

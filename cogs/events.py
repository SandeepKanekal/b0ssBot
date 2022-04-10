# Contains all bot events
import contextlib
import os
import random
import discord
from sql_tools import SQL
from discord.ext import commands, tasks
from googleapiclient.discovery import build
from discord.utils import get


def remove(nick_name: str) -> str:
    return " ".join(nick_name.split()[1:]) if '[AFK]' in nick_name.split() else nick_name


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Bot activity on starting
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print('Bot is ready')
        await self.bot.change_presence(activity=discord.Game(name='The Game Of b0sses'))
        self.check_for_videos.start()

    # Bot activity on receiving a message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:  # sourcery no-metrics
        sql = SQL('b0ssbot')
        if message.author.bot:
            return

        if "'" in message.content:
            message.content = message.content.replace("'", "''")

        afk_user = sql.select(
            elements=['member_id', 'guild_id', 'reason'],
            table='afks',
            where=f'member_id = \'{str(message.author.id)}\' and guild_id = \'{str(message.guild.id)}\'',
        )

        if afk_user and message.author.id == int(afk_user[0][0]):  # Remove AFK if the user is the author
            sql.delete(table='afks',
                       where=f'member_id = \'{str(message.author.id)}\' and guild_id = \'{str(message.guild.id)}\'')
            with contextlib.suppress(discord.Forbidden):
                await message.author.edit(nick=remove(message.author.display_name))
            await message.reply(
                embed=discord.Embed(
                    description=f'Welcome back {message.author.mention}, I removed your AFK!',
                    colour=discord.Colour.green()
                )
            )

        # If an AFK user is mentioned, inform the author
        if message.mentions:
            for mention in message.mentions:
                if afk_user := sql.select(
                        elements=['member_id', 'guild_id', 'reason'],
                        table='afks',
                        where=f'member_id = \'{mention.id}\' and guild_id = \'{message.guild.id}\'',
                ):
                    member = get(message.guild.members, id=int(afk_user[0][0]))
                    if member in message.mentions and message.guild.id == int(afk_user[0][1]):
                        await message.reply(
                            embed=discord.Embed(
                                description=f'{message.author.mention}, {member.mention} is AFK!\nAFK note: {afk_user[0][2]}',
                                colour=discord.Colour.red()
                            ).set_thumbnail(url=str(member.avatar) if member.avatar else str(member.default_avatar))
                        )

        if self.bot.user.id in message.raw_mentions and message.content != '@everyone' and message.content != '@here':
            command_prefix = sql.select(elements=['prefix'], table='prefixes', where=f"guild_id = '{message.guild.id}'")
            embed = discord.Embed(
                description=f'Hi! I am **{self.bot.user.name}**! I was coded by **Dose#7204**. My prefix is **{command_prefix[0][0]}**',
                colour=self.bot.user.colour)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            await message.reply(embed=embed)

        if message.content.lower() == 'vibe':
            gif = random.choice(
                [
                    'https://tenor.com/view/vibe-gif-21932627',
                    'https://tenor.com/view/cat-vibe-153bpm-gif-18260767',
                    'https://tenor.com/view/vibe-cat-gif-230916650',
                    'https://cdn.discordapp.com/emojis/781962404161388584.gif?v=1&size=40',
                    'https://tenor.com/view/indian-gif-5336861',
                    'https://tenor.com/view/dance-kid-kid-dance-india-indian-gif-20780888',
                    'https://tenor.com/view/fat-guy-dancing-moves-gif-14156580',
                    'https://tenor.com/view/disco-disco-time-munna-indian-cricistan-gif-19206126'
                ]
            )
            await message.reply(gif)

        if message.content.lower() == 'sus':
            gif = random.choice([
                'https://tenor.com/view/the-rock-the-rock-sus-the-rock-meme-tthe-rock-sus-meme-dwayne-johnson-gif-23805584',
                'https://tenor.com/view/amogus-spin-gif-22146300'])
            await message.reply(gif)

        with contextlib.suppress(IndexError):
            if sql.select(elements=['guild_id'], table='message_responses',
                          where=f"message = '{message.content.lower()}'")[0][0] == "default":
                await message.reply(
                    sql.select(elements=['response'], table='message_responses',
                               where=f"message = '{message.content.lower()}'")[0][0]
                )

            if response := sql.select(elements=['response'], table='message_responses',
                                      where=f"message = '{message.content.lower()}' AND guild_id = '{message.guild.id}'")[0][0]:
                await message.reply(response)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        sql = SQL('b0ssbot')
        sql.insert(table='prefixes', columns=['guild_id', 'prefix'], values=[f'\'{guild.id}\'', '\'-\''])
        sql.insert(table='modlogs', columns=['guild_id', 'mode', 'channel_id'],
                   values=[f"'{guild.id}'", '\'0\'', '\'None\''])

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        sql = SQL('b0ssbot')
        sql.delete(table='prefixes', where=f'guild_id = \'{guild.id}\'')
        sql.delete(table='modlogs', where=f'guild_id = \'{guild.id}\'')

    @tasks.loop(minutes=60)
    async def check_for_videos(self):
        sql = SQL('b0ssbot')
        print('Checking for videos...')
        channel = sql.select(elements=['channel_id', 'latest_video_id', 'guild_id', 'text_channel_id', 'channel_name'],
                             table='youtube')
        youtube = build('youtube', 'v3', developerKey=os.getenv('youtube_api_key'))
        for data in channel:
            c = youtube.channels().list(part='contentDetails', id=data[0]).execute()
            latest_video_id = \
                youtube.playlistItems().list(playlistId=c['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
                                             part='contentDetails').execute()['items'][0]['contentDetails']['videoId']
            if data[1] != latest_video_id:
                guild = discord.utils.get(self.bot.guilds, id=int(data[2]))
                text_channel = discord.utils.get(guild.text_channels, id=int(data[3]))

                webhooks = await guild.webhooks()
                webhook = discord.utils.get(webhooks, name=f'{self.bot.user.name} YouTube Notifier')
                if webhook is None:
                    webhook = await text_channel.create_webhook(name=f'{self.bot.user.name} YouTube Notifier')
                await webhook.send(
                    f'New video uploaded by **[{data[4]}](https://youtube.com/channel/{data[0]})**!\nhttps://youtube.com/watch?v={latest_video_id}',
                    username=f'{self.bot.user.name} YouTube Notifier',
                    avatar_url=self.bot.user.avatar)

                sql.update(table='youtube', column='latest_video_id', value=f"'{latest_video_id}'",
                           where=f'channel_id = \'{data[0]}\'')


# Setup
def setup(bot):
    bot.add_cog(Events(bot))

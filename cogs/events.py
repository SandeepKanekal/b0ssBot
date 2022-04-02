# Contains all bot events
import contextlib
import random
import discord
from sql_tools import SQL
from discord.ext import commands
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
        await self.bot.change_presence(activity=discord.Game(name='Game Of b0sses'))

    # Bot activity on receiving a message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:  # sourcery no-metrics
        sql = SQL('b0ssbot')
        if message.author.bot:
            return

        afk_user = sql.select(
            elements=['member_id', 'guild_id', 'reason'],
            table='afks',
            where=f'member_id = \'{str(message.author.id)}\' and guild_id = \'{str(message.guild.id)}\'',
        )

        if afk_user and message.author.id == int(afk_user[0][0]):  # Remove AFK if the user is the author
            sql.delete(table='afks', where=f'member_id = \'{str(message.author.id)}\' and guild_id = \'{str(message.guild.id)}\'')
            with contextlib.suppress(discord.Forbidden):
                await message.author.edit(nick=remove(message.author.display_name))
            await message.reply(
                embed = discord.Embed(
                    description=f'Welcome back {message.author.mention}, I removed your AFK!', 
                    colour=discord.Colour.green()
                    )
            )

        # If an AFK user is mentioned, inform the author
        if message.mentions:
            for mention in message.mentions:
                afk_user = sql.select(elements=['member_id', 'guild_id', 'reason'], table='afks', where=f'member_id = \'{mention.id}\' and guild_id = \'{message.guild.id}\'')
                member = get(message.guild.members, id=int(afk_user[0][0]))
                if member in message.mentions and message.guild.id == int(afk_user[0][1]):
                    await message.reply(
                        embed = discord.Embed(
                            description=f'{message.author.mention}, {member.mention} is AFK!\nAFK note: {afk_user[0][2]}', 
                            colour=discord.Colour.red()
                            ).set_thumbnail(url=str(member.avatar) if member.avatar else str(member.default_avatar))
                    )           

        if message.content.lower() == 'ghanta':
            await message.reply('https://tenor.com/view/adclinic-sino-gif-19344591')

        if message.content.lower() == 'no one cares':
            await message.reply('https://tenor.com/view/no-one-cares-i-dont-care-idc-nobody-cares-gif-8737514')

        if message.content.lower() in ['no u', 'nou']:
            await message.reply('https://tenor.com/view/no-u-reverse-card-anti-orders-gif-19358543')

        if self.bot.user.id in message.raw_mentions and message.content != '@everyone' and message.content != '@here':
            embed = discord.Embed(
                description=f'Hi! I am **{self.bot.user.name}**! I was coded by **Dose#7204**. My prefix is **{self.bot.command_prefix}**',
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

        if message.content.lower() in ['amogus', 'amongus', 'amog us', 'among us']:
            await message.reply('https://tenor.com/view/amogus-spin-gif-22146300')

        if message.content.lower() == 'rickroll':
            await message.reply('https://tenor.com/view/rickroll-roll-rick-never-gonna-give-you-up-never-gonna-gif'
                                '-22954713')

        if message.content.lower() == '69':
            await message.reply('NICE!!')

        if message.content.lower() == 'yes!':
            await message.reply('https://tenor.com/view/yes-baby-goal-funny-face-gif-13347383')

        if message.content.lower() == 'sus':
            gif = random.choice([
                'https://tenor.com/view/the-rock-the-rock-sus-the-rock-meme-tthe-rock-sus-meme-dwayne-johnson-gif-23805584',
                'https://tenor.com/view/amogus-spin-gif-22146300'])
            await message.reply(gif)

        if message.content.lower() in ['zucc', 'zuck', 'zuckerberg']:
            await message.reply('https://tenor.com/view/mark-zuckerberg-facebook-ok-this-is-gif-11614677')

        if message.content.lower() in ['urmom', 'ur mom', 'your mom', 'yourmom']:
            gif = random.choice([
                'https://tenor.com/view/your-mother-great-argument-however-megamind-your-mom-yo-mama-gif-22994712',
                'https://tenor.com/view/gul-ur-mom-gold-gul-ur-mom-gold-gif-19890779'
            ])
            await message.reply(gif)

        if message.content.lower() in ['horny', 'horni']:
            await message.reply('https://tenor.com/view/vorzek-vorzneck-oglg-og-lol-gang-gif-24901093')
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        sql = SQL('b0ssbot')
        sql.insert(table='prefixes', columns=['guild_id', 'prefix'], values=[f'\'{guild.id}\'', '\'-\''])


# Setup
def setup(bot):
    bot.add_cog(Events(bot))

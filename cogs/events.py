# Contains all bot events
import random
import discord
from discord.ext import commands
from discord.utils import get
from afks import afks


def remove(nick_name):
    return " ".join(nick_name.split()[1:]) if '[AFK]' in nick_name.split() else nick_name


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Bot activity on starting
    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot is ready')
        await self.bot.change_presence(activity=discord.Game(name=f'Prefix is {self.bot.command_prefix}'))

    # Bot activity on receiving a message
    @commands.Cog.listener()
    async def on_message(self, message):  # sourcery no-metrics
        afk_index = 0
        if message.author.bot:
            return

        for item in afks:
            if item['member_id'] == message.author.id and item['guild_id'] == message.guild.id:
                afks.pop(afk_index)
                try:
                    await message.author.edit(nick=remove(message.author.display_name))
                except discord.Forbidden:
                    pass
                await message.channel.send(f'Welcome back {message.author.name}, I removed your AFK')
                break
            afk_index += 1

        for item in afks:
            member = get(message.guild.members, id=item['member_id'])
            if (message.reference and
                member == (await message.channel.fetch_message(message.reference.message_id)).author) \
                    or member.id in message.raw_mentions \
                    and item['guild_id'] == message.guild.id:
                await message.reply(f'{member.name} is AFK ; AFK note: {item["reason"]}')

        if message.content.lower() == 'ghanta':
            await message.reply('https://tenor.com/view/adclinic-sino-gif-19344591')

        if message.content.lower() == 'no one cares':
            await message.reply('https://tenor.com/view/no-one-cares-i-dont-care-idc-nobody-cares-gif-8737514')

        if message.content.lower() == 'no u' or message.content.lower() == 'nou':
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

        if (message.content.lower() == 'amogus' or
                message.content.lower() == 'amongus' or
                message.content.lower() == 'amog us' or
                message.content.lower() == 'among us'):
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

        if message.content.lower() == 'zucc' or message.content.lower() == 'zuck' or message.content.lower() == 'zuckerberg':
            await message.reply('https://tenor.com/view/mark-zuckerberg-facebook-ok-this-is-gif-11614677')


# Setup
def setup(bot):
    bot.add_cog(Events(bot))

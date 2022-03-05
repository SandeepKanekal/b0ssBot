# Contains all bot events
import random
import discord
from discord.ext import commands
from discord.utils import get
from afks import afks


def remove(afk):
    if '[AFK]' in afk.split():
        return " ".join(afk.split()[1:])
    else:
        return afk


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
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.author.id in afks.keys():
            afks.pop(message.author.id)
            try:
                await message.author.edit(nick=remove(message.author.display_name))
            except discord.Forbidden:
                await message.channel.send('Removed AFK, but could not change the nickname')
            await message.channel.send(f'Welcome back {message.author.name}, I removed your AFK')

        for member_id, reason in afks.items():
            member = get(message.guild.members, id=member_id)
            if (message.reference and member == (await message.channel.fetch_message(
                    message.reference.message_id)).author) or member.id in message.raw_mentions:
                await message.reply(f'{member.name} is AFK ; AFK note: {reason}')

        if message.content.lower() == 'ghanta':
            await message.reply('https://tenor.com/view/adclinic-sino-gif-19344591')

        if message.content.lower() == 'no one cares':
            await message.reply('https://tenor.com/view/no-one-cares-i-dont-care-idc-nobody-cares-gif-8737514')

        if message.content.lower() == 'no u' or message.content.lower() == 'nou':
            await message.reply('https://tenor.com/view/no-u-reverse-card-anti-orders-gif-19358543')

        if self.bot.user.id in message.raw_mentions and message.content != '@everyone' and message.content != '@here':
            embed = discord.Embed(colour=self.bot.user.colour)
            embed.add_field(name='b0ssBot',
                            value=f'Hi! I am **{self.bot.user.name}**! I was coded by **Dose#7204**. My prefix is **{self.bot.command_prefix}**')
            await message.reply(embed=embed)

        if message.content.lower() == 'music':
            await message.reply('https://tenor.com/view/vibe-gif-21932627')

        if message.content.lower() == 'vibe':
            await message.reply('https://tenor.com/view/cat-vibe-153bpm-gif-18260767')

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


# Setup
def setup(bot):
    bot.add_cog(Events(bot))

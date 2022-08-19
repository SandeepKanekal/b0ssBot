# Copyright (c) 2022 Sandeep Kanekal
# Main module
import discord
import keep_alive
import os
from discord.ext import commands
from sql_tools import SQL


# noinspection PyShadowingNames,PyUnusedLocal
def get_prefix(bot: commands.Bot, message: discord.Message) -> str:
    return sql.select(elements=['prefix'], table='prefixes', where=f'guild_id = \'{message.guild.id}\'')[0][0]


# Pre-run requirements
sql = SQL('b0ssbot')
bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, intents=discord.Intents.all())
bot.remove_command('help')

# Loads the cog
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

keep_alive.keep_alive()  # Keep alive
bot.run(os.getenv('TOKEN'))  # Starts the bot

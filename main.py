# Main module
import discord
import keep_alive
import os
from discord.ext import commands

from sql_tools import SQL


def get_prefix(bot, message):
    return sql.select(elements=['prefix'], table='prefixes', where=f'guild_id = \'{message.guild.id}\'')[0][0]


# Pre-run requirements
intents = discord.Intents.all()
sql = SQL('b0ssbot')
discord.Intents.members = True
discord.Intents.webhooks = True
bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, intents=intents)
bot.remove_command('help')
cogs = ['events', 'help', 'fun', 'info', 'misc', 'music', 'moderation', 'util', 'internet']


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description: str) -> None:
    # Response embed
    embed = discord.Embed(description=description, colour=discord.Colour.red())
    await ctx.send(embed=embed)


# Loadcog command
@bot.command(hidden=True)
@commands.is_owner()
async def loadcog(ctx, cog):
    if cog not in cogs:
        await ctx.send(f'cogs.{cog} not found')
        return
    try:
        bot.load_extension(f'cogs.{cog}')
        await ctx.send(f'cogs.{cog} has been loaded')
    except discord.ExtensionAlreadyLoaded:
        await ctx.send(f'cogs.{cog} is loaded already')


# Only the owner can access these commands, if accessed otherwise, a response will be sent
@loadcog.error
async def loadcog_error(ctx, error):
    await send_error_embed(ctx, description=f'Error: {error}')


# Unloadcog command
@bot.command(hidden=True)
@commands.is_owner()
async def unloadcog(ctx, cog):
    if cog not in cogs:
        await ctx.send(f'cogs.{cog} not found')
        return
    try:
        bot.unload_extension(f"cogs.{cog}")
        await ctx.send(f'cogs.{cog} has been unloaded')
    except discord.ExtensionNotLoaded:
        await ctx.send(f"cogs.{cog} not loaded")


# Only the owner can access these commands, if accessed otherwise, a response will be sent
@unloadcog.error
async def unloadcog_error(ctx, error):
    await send_error_embed(ctx, description=f'Error: {error}')


@bot.command(hidden=True)
@commands.is_owner()
async def reloadcog(ctx, cog):
    if cog == 'all':
        for cog in bot.cogs:
            bot.reload_extension(f'cogs.{cog}')
        await ctx.send('All cogs have been reloaded')
        return
    if cog not in cogs:
        await ctx.send(f'cogs.{cog} not found')
        return
    try:
        bot.reload_extension(f'cogs.{cog}')
        await ctx.send(f'cogs.{cog} has been reloaded')
    except discord.ExtensionFailed as e:
        await ctx.send(e)


# Only the owner can access these commands, if accessed otherwise, a response will be sent
@reloadcog.error
async def reloadcog_error(ctx, error):
    await send_error_embed(ctx, description=f'Error: {error}')


@bot.command(hidden=True)
@commands.is_owner()
async def guildlist(ctx):
    await ctx.send(bot.guilds)


@guildlist.error
async def guildlist_error(ctx, error):
    await send_error_embed(ctx, description=f'Error: {error}')


# Loads the cog
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

keep_alive.keep_alive()  # Keep alive
bot.run(os.getenv('TOKEN'))  # Starts the bot

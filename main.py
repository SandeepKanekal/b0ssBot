# Main module
import discord
import os
import keep_alive
from discord.ext import commands

# Pre-run requirements
intents = discord.Intents.all()
discord.Intents.members = True
discord.Intents.webhooks = True
bot = commands.Bot(command_prefix='-', case_insensitive=True, intents=intents)
bot.remove_command('help')
cogs = ['events', 'help', 'fun', 'info', 'misc', 'music', 'moderation', 'util']


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


# Loads the cog
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

keep_alive.keep_alive()  # Keep alive
bot.run(os.getenv('TOKEN'))  # Starts the bot

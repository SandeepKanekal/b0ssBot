import discord
import os
import contextlib
from sql_tools import SQL
from discord.ext import commands


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, cog: str):
        """Loads a cog"""
        try:
            self.bot.load_extension(f'cogs.{cog}')
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @load.error
    async def load_error(self, ctx, e):
        await ctx.send(embed=discord.Embed(description=str(e)))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, cog: str):
        """Unloads a cog"""
        try:
            self.bot.unload_extension(f'cogs.{cog}')
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @unload.error
    async def unload_error(self, ctx, e):
        await ctx.send(embed=discord.Embed(description=str(e)))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, cog: str):
        """Reloads a cog"""
        try:
            self.bot.unload_extension(f'cogs.{cog}')
            self.bot.load_extension(f'cogs.{cog}')
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @reload.error
    async def reload_error(self, ctx, e):
        await ctx.send(embed=discord.Embed(description=str(e)))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def query(self, ctx, *, query):
        sql = SQL('b0ssbot')
        results = sql.query(query)
        try:
            await ctx.send(results)
        except discord.HTTPException:
            if results:
                with open('query.txt', 'w') as f:
                    f.write(str(results))
                await ctx.send(file=discord.File('query.txt'))
                os.remove('query.txt')
            else:
                await ctx.send('Query provided returns None')

    @query.error
    async def query_error(self, ctx, e):
        await ctx.send(embed=discord.Embed(description=str(e)))

    @commands.command(aliases=['gl'], hidden=True)
    @commands.is_owner()
    async def guildlist(self, ctx):
        """Lists all guilds the bot is in"""
        await ctx.send(
            embed=discord.Embed(description='\n'.join([guild.name for guild in self.bot.guilds]))
        )

    @guildlist.error
    async def guildlist_error(self, ctx, e):
        await ctx.send(embed=discord.Embed(description=str(e)))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def eval(self, ctx, *, code: str):
        """Evaluates code"""
        with contextlib.suppress(discord.HTTPException):
            await eval(code) if 'ctx' in code else await ctx.send(eval(code))

    @eval.error
    async def eval_error(self, ctx, e):
        await ctx.send(embed=discord.Embed(description=str(e)))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Restarts the bot"""
        await ctx.send('Shutting down...')
        await self.bot.close()
        self.bot.run(os.getenv('TOKEN'))

    @shutdown.error
    async def shutdown_error(self, ctx, e):
        await ctx.send(embed=discord.Embed(description=str(e)))


def setup(bot):
    bot.add_cog(Owner(bot))

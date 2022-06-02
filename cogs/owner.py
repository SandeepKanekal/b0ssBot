import discord
import os
from sql_tools import SQL
from discord.ext import commands


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['loadcog'], hidden=True)
    @commands.is_owner()
    async def load(self, ctx, cog: str):
        """
        Loads a cog
        
        :param ctx: The context of where the command was used
        :param cog: The name of the cog to load
        
        :type ctx: commands.Context
        :type cog: str
        
        :return: None
        :rtype: None
        """
        try:
            self.bot.load_extension(f'cogs.{cog}')
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @load.error
    async def load_error(self, ctx, e):
        """
        Handles errors for the load command
        
        :param ctx: The context of where the command was used
        :param e: The error that was raised
        
        :type ctx: commands.Context
        :type e: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await ctx.send(embed=discord.Embed(description=str(e)))

    @commands.command(aliases=['unloadcog'], hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, cog: str):
        """
        Unloads a cog
        
        :param ctx: The context of where the command was used
        :param cog: The name of the cog to unload
        
        :type ctx: commands.Context
        :type cog: str
        
        :return: None
        :rtype: None
        """
        try:
            self.bot.unload_extension(f'cogs.{cog}')
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @unload.error
    async def unload_error(self, ctx, e):
        """
        Handles errors for the unload command
        
        :param ctx: The context of where the command was used
        :param e: The error that was raised
        
        :type ctx: commands.Context
        :type e: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await ctx.send(embed=discord.Embed(description=str(e)))

    @commands.command(aliases=['reloadcog'], hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, cog: str):
        """
        Reloads a cog
        
        :param ctx: The context of where the command was used
        :param cog: The name of the cog to reload
        
        :type ctx: commands.Context
        :type cog: str
        
        :return: None
        :rtype: None
        """
        try:
            self.bot.unload_extension(f'cogs.{cog}')
            self.bot.load_extension(f'cogs.{cog}')
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @reload.error
    async def reload_error(self, ctx, e):
        """
        Handles errors for the reload command
        
        :param ctx: The context of where the command was used
        :param e: The error that was raised
        
        :type ctx: commands.Context
        :type e: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await ctx.send(embed=discord.Embed(description=str(e)))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def query(self, ctx, *, query):
        """
        Runs a query on the database
        
        :param ctx: The context of where the command was used
        :param query: The query to run
        
        :type ctx: commands.Context
        :type query: str
        
        :return: None
        :rtype: None
        """
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
        """
        Handles errors for the query command
        
        :param ctx: The context of where the command was used
        :param e: The error that was raised
        
        :type ctx: commands.Context
        :type e: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await ctx.send(embed=discord.Embed(description=str(e)))

    @commands.command(aliases=['gl'], hidden=True)
    @commands.is_owner()
    async def guildlist(self, ctx):
        """
        Lists all guilds the bot is in
        
        :param ctx: The context of where the command was used
        
        :type ctx: commands.Context
        
        :return: None
        :rtype: None
        """
        await ctx.send(
            embed=discord.Embed(description='\n'.join([guild.name for guild in self.bot.guilds]))
        )

    @guildlist.error
    async def guildlist_error(self, ctx, e):
        """
        Handles errors for the guildlist command
        
        :param ctx: The context of where the command was used
        :param e: The error that was raised
        
        :type ctx: commands.Context
        :type e: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await ctx.send(embed=discord.Embed(description=str(e)))

    @commands.command(name='eval', hidden=True)
    @commands.is_owner()
    async def eval_(self, ctx, *, code: str):
        """
        Evaluates code
        
        :param ctx: The context of where the command was used
        :param code: The code to evaluate
        
        :type ctx: commands.Context
        :type code: str
        
        :return: None
        :rtype: None
        """
        try:
            if 'os.getenv' in code or 'os.environ' in code or 'os.system' in code or 'os.chdir' in code:
                raise discord.Forbidden('os is not allowed')
            else:
                await eval(code.strip('await')) if 'await' in code else eval(code)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
    
    @eval_.error
    async def eval_error(self, ctx, e):
        """
        Handles errors for the reload command
        
        :param ctx: The context of where the command was used
        :param e: The error that was raised
        
        :type ctx: commands.Context
        :type e: commands.CommandError
        
        :return: None
        :rtype: None
        """
        await ctx.send(embed=discord.Embed(description=str(e)))


def setup(bot):
    bot.add_cog(Owner(bot))

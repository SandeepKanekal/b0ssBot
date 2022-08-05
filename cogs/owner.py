# Copyright (c) 2022 Sandeep Kanekal
import discord
import os
from sql_tools import SQL
from discord.ext import commands
from discord.commands import Option
from discord.ui import Modal, InputText


class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['loadcog'], hidden=True)
    @commands.is_owner()
    async def load(self, ctx: commands.Context, cog: str):
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
    async def load_error(self, ctx: commands.Context, e: commands.CommandError):
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
    async def unload(self, ctx: commands.Context, cog: str):
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
    async def unload_error(self, ctx: commands.Context, e: commands.CommandError):
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
    async def reload(self, ctx: commands.Context, cog: str):
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
    async def reload_error(self, ctx: commands.Context, e: commands.CommandError):
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
    async def query(self, ctx: commands.Context, *, query):
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
    async def query_error(self, ctx: commands.Context, e: commands.CommandError):
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
    async def guildlist(self, ctx: commands.Context):
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
    async def guildlist_error(self, ctx: commands.Context, e: commands.CommandError):
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

    @commands.slash_command(name='eval', guild_ids=[930715526441885696], hidden=True)
    @commands.is_owner()
    async def eval_(self, ctx: discord.ApplicationContext, *, mode: Option(str, description='The mode to run the code in', required=True, choices=['single', 'file']), code: Option(str, description='Code for single line', required=False, default=None)):
        """
        Evaluates code
        
        :param ctx: The context of where the command was used
        :param mode: The mode to run the code in
        :param code: The code to evaluate

        :type ctx: discord.ApplicationContext
        :type mode: str
        :type code: str
        
        :return: None
        :rtype: None
        """
        if mode == 'single':
            try:
                await eval(code.strip('await')) if 'await' in code else eval(code)
            except Exception as e:
                await ctx.respond(f'**`ERROR:`** {type(e).__name__} - {e}')
            else:
                await ctx.respond('**`SUCCESS`**')

        elif mode == 'file':
            modal = Modal(title='Eval')
            modal.add_item(
                InputText(
                    label='Code',
                    placeholder='Code to evaluate',
                    style=discord.InputTextStyle.long,
                )
            )
            await ctx.response.send_modal(modal=modal)

            async def callback(interaction):
                with open('cogs/eval.py', 'w') as f:
                    f.write(modal.children[0].value)
                
                try:
                    self.bot.load_extension('cogs.eval')
                except Exception as er:
                    await interaction.response.send_message(f'**`ERROR:`** {type(er).__name__} - {er}')
                    return

                await interaction.response.send_message('File created!')
        
            modal.callback = callback

    @eval_.error
    async def eval_error(self, ctx: discord.ApplicationContext, e: discord.ApplicationCommandInvokeError):
        """
        Handles errors for the reload command
        
        :param ctx: The context of where the command was used
        :param e: The error that was raised
        
        :type ctx: discord.ApplicationContext
        :type e: discord.ApplicationCommandInvokeError
        
        :return: None
        :rtype: None
        """
        await ctx.respond(f'**`ERROR:`** {type(e).__name__} - {e}', ephemeral=True)

    @commands.command(name='vc', hidden=True)
    @commands.is_owner()
    async def vc(self, ctx: commands.Context):
        """
        Sends the length of voice clients

        :param ctx: The context of the command

        :type ctx: commands.Context

        :return: None
        :rtype: None
        """
        await ctx.reply(len(self.bot.voice_clients))

    @vc.error
    async def vc_error(self, ctx: commands.Context, e: commands.CommandError):
        """
        Handles errors for the vc command

        :param ctx: The context of the command
        :param e: The error raised

        :type ctx: commands.Context
        :type e: commands.CommandError

        :return: None
        :rtype: None
        """
        await ctx.send(embed=discord.Embed(description=str(e)))


def setup(bot: commands.Bot):
    bot.add_cog(Owner(bot))

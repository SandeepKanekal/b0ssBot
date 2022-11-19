# Copyright (c) 2022 Sandeep Kanekal
# Contains the help commands
import discord
import datetime
import os
from sql_tools import SQL
from discord.ext import commands
from ui_components import HelpView


# Help command
class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """
        Initializes the help command
        
        :param bot: The bot object
        
        :type bot: commands.Bot
        
        :returns: None
        :rtype: None
        """
        self.bot = bot

    @commands.command(name='help',
                      description='Shows the list of all commands or the information about one command if specified',
                      usage='help <command>',
                      hidden=True)
    async def help(self, ctx: commands.Context, *, command: str = None):
        # sourcery skip: low-code-quality
        """
        Shows the list of all commands or the information about one command if specified
        
        :param ctx: The context of the command
        :param command: The command to get the information about
        
        :type ctx: commands.Context
        :type command: str
        
        :return: None
        :rtype: None
        """
        sql = SQL(os.getenv('sql_db_name'))
        prefix = sql.select(elements=['prefix'], table='prefixes', where=f'guild_id = \'{ctx.guild.id}\'')[0][0]

        if command is None:
            # Create embed
            embed = discord.Embed(
                title='Help Page', 
                description=f'Shows the list of all commands\nUse `{prefix}help <command>` to get more information about a command', 
                colour=discord.Colour.blurple(),
                timestamp=datetime.datetime.now()
            ).set_footer(text='Help Page', icon_url=self.bot.user.avatar.url)

            # Add fields
            for cog in sorted(self.bot.cogs):
                if cog in ['Eval', 'Help', 'Events', 'Owner']:
                    continue

                commands_str = ''.join(f'`{command.name}` ' for command in self.bot.cogs[cog].get_commands())
                embed.add_field(name=cog, value=commands_str[:-1], inline=False)

        else:
            # Get command
            cmd = self.bot.get_command(command) or self.bot.get_application_command(command, type=discord.ApplicationCommand)

            # Checks
            if cmd is None:
                await ctx.reply(f'Command {command} not found')
                return

            if 'hidden' in cmd.__dict__['__original_kwargs__']:
                await ctx.reply('This command is only for the owner!')
                return

            if self.bot.get_command(command) and self.bot.get_application_command(command, type=discord.ApplicationCommand):
                await ctx.reply('There are 2 instances of this command. Choose the command you want to get information about', view=HelpView(command, self.bot, prefix, timeout=None))
                return

            # Create embed
            embed = discord.Embed(
                title=f'Help - {cmd}',
                description=cmd.description,
                colour=discord.Colour.blurple(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f'Help for {cmd}', icon_url=self.bot.user.avatar.url)

            # Add fields
            if isinstance(cmd, commands.Command):
                embed.add_field(name='Aliases', value=f"`{', '.join(cmd.aliases)}`", inline=False) if cmd.aliases else embed.add_field(name='Aliases', value='`None`', inline=False)
                param_str = ''.join(f'`{param}` ' for param in cmd.clean_params)
                param_str = param_str[:-1]
                embed.add_field(name='Parameters', value=param_str or '`None`', inline=False)
                embed.add_field(name='Usage', value=f'`{prefix}{cmd.usage}`', inline=False)
            elif isinstance(cmd, discord.SlashCommand):
                param_str = ''.join(f'`{param.name}` ' for param in cmd.options)
                param_str = param_str[:-1]
                embed.add_field(name='Parameters', value=param_str, inline=False)
                embed.add_field(name='Usage', value=cmd.mention, inline=False)
            elif isinstance(cmd, discord.SlashCommandGroup):
                embed.add_field(name='Subcommands', value=f'{" ".join(subcmd.mention for subcmd in cmd.walk_commands())}', inline=False)
                embed.add_field(name='Usage', value=f'This is a Slash Command Group. Type /{cmd.name} to get the subcommands')
            else:
                embed.add_field(name='Usage', value='This is an application command. Right click on a message/user to get the command', inline=False)

        await ctx.reply(embed=embed)


# Setup
def setup(bot: commands.Bot):
    """
    Adds the help command to the bot
    
    :param bot: The bot object
    
    :type bot: commands.Bot
    
    :return: None
    :rtype: None
    """
    bot.add_cog(Help(bot))

import discord
import datetime
from sql_tools import SQL
from discord.ext import commands


# Help command
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help',
                      description='Shows the list of all commands or the information about one command if specified',
                      usage='help <command>',
                      hidden=True)
    async def help(self, ctx, *, command: str = None):
        """
        Shows the list of all commands or the information about one command if specified
        
        :param ctx: The context of the command
        :param command: The command to get the information about
        
        :type ctx: commands.Context
        :type command: str
        
        :return: None
        :rtype: None
        """
        sql = SQL('b0ssbot')
        prefix = sql.select(elements=['prefix'], table='prefixes', where=f'guild_id = \'{ctx.guild.id}\'')[0][0]

        if command is None:
            embed = discord.Embed(
                title='Help Page', 
                description=f'Shows the list of all commands\nUse `{prefix}help <command>` to get more information about a command', 
                colour=discord.Colour.blurple(),
                timestamp=datetime.datetime.now()
            ).set_footer(text='Help Page', icon_url=self.bot.user.avatar)

            for cog in sorted(self.bot.cogs):
                if cog in ['Eval', 'Help', 'Events', 'Owner']:
                    continue

                commands_str = ''.join(f'`{command.name}` ' for command in self.bot.cogs[cog].get_commands())
                embed.add_field(name=cog, value=commands_str[:-1], inline=False)

        else:
            cmd = self.bot.get_command(command) or self.bot.get_application_command(command, type=discord.ApplicationCommand)
            if cmd is None:
                await ctx.reply(f'Command {command} not found')
                return

            embed = discord.Embed(
                title=f'Help - {cmd}',
                description=cmd.description,
                colour=discord.Colour.blurple(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f'Help for {cmd}', icon_url=self.bot.user.avatar)

            if not isinstance(cmd, discord.ApplicationCommand):
                embed.add_field(name='Aliases', value=f"`{', '.join(cmd.aliases)}`", inline=False) if cmd.aliases else embed.add_field(name='Aliases', value='`None`', inline=False)
                param_str = ''.join(f'`{param}` ' for param in cmd.clean_params)
                param_str = param_str[:-1]
                embed.add_field(name='Parameters', value=param_str or '`None`', inline=False)
                embed.add_field(name='Usage', value=f'`{prefix}{cmd.usage}`', inline=False)
            elif isinstance(cmd, discord.SlashCommand):
                param_str = ''.join(f'`{param.name}` ' for param in cmd.options)
                param_str = param_str[:-1]
                embed.add_field(name='Parameters', value=param_str, inline=False)
                embed.add_field(name='Usage', value='This is a slash command. Type / to get the command', inline=False)
            else:
                embed.add_field(name='Usage', value='This is an application command. Right click on a message/user to get the command', inline=False)

        await ctx.reply(embed=embed)


# Setup
def setup(bot):
    bot.add_cog(Help(bot))

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
                    hidden=True)
    async def help(self, ctx, command=None):  # sourcery no-metrics
        sql = SQL('b0ssbot')
        command_prefix = sql.select(elements=['prefix'], table='prefixes', where=f'guild_id = \'{ctx.guild.id}\'')[0][0]
        if command is not None:
            for cmd in self.bot.commands:
                if (command.lower() == cmd.name.lower() or command.lower() in cmd.aliases) and not cmd.hidden:
                    aliases = f'{cmd.name}, '
                    for alias in cmd.aliases:
                        aliases += f'{alias}, '
                    aliases = aliases[:-2]
                    param_string = ""  # Parameter string
                    param_string_embed = ''  # Parameter string for the command usage field
                    if len(cmd.clean_params) == 0:
                        param_string = 'None'
                    else:
                        for param in cmd.clean_params:
                            param_string += f'{param}, '
                            param_string_embed += f'<{param}> '
                        param_string = param_string[:-2]
                        param_string_embed = param_string_embed[:-1]

                    # Response embed
                    embed = discord.Embed(title=f'Help - {cmd.name}', description=cmd.description,
                                          colour=discord.Colour.blue())
                    embed.add_field(name='Aliases', value=f'`{aliases}`', inline=False)
                    embed.add_field(name='Parameters', value=f'`{param_string}`', inline=False)
                    if param_string != 'None':
                        embed.add_field(name='Command Usage',
                                        value=f'`{command_prefix}{cmd.name} {param_string_embed}`',
                                        inline=False)
                    else:
                        embed.add_field(name='Command Usage', value=f'`{command_prefix}{cmd.name}`',
                                        inline=False)
                    await ctx.reply(embed=embed)
        else:
            # Command string
            cmds = ''
            # Response embed
            embed = discord.Embed(title='Help Page', description=f'Shows the list of all commands\nUse `{command_prefix}help <command>` to get more information about a command',
                                  colour=discord.Colour.blue())
            for cog in self.bot.cogs:
                if cog in ['Help', 'Events']:
                    continue
                for cmd in self.bot.commands:
                    if cmd.cog and cmd.cog.qualified_name == cog and not cmd.hidden:
                        cmds += f'`{str(cmd)}` '
                cmds = cmds[:-1]
                embed.add_field(name=cog.upper(), value=cmds, inline=False)
                cmds = ''
            embed.set_footer(text=f'Requested by {ctx.author}', icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(ctx.author.default_avatar))
            embed.timestamp = datetime.datetime.now()
            await ctx.reply(embed=embed)


# Setup
def setup(bot):
    bot.add_cog(Help(bot))

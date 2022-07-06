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
    async def help(self, ctx, command: str = None):  # sourcery skip: low-code-quality
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
        command_prefix = sql.select(elements=['prefix'], table='prefixes', where=f'guild_id = \'{ctx.guild.id}\'')[0][0]
        if command is not None:
            for cmd in self.bot.commands:
                if (command.lower() == cmd.name.lower() or command.lower() in cmd.aliases) and not cmd.hidden:
                    aliases = f'{cmd.name}, '
                    for alias in cmd.aliases:
                        aliases += f'{alias}, '
                    aliases = aliases[:-2]
                    param_string: str = ""  # Parameter string
                    if len(cmd.clean_params) == 0:
                        param_string = 'None'
                    else:
                        for param in cmd.clean_params:
                            param_string += f'`{param}`, '
                        param_string = param_string[:-2]
                    embed = discord.Embed(title=f'Help - {cmd.name}',
                                          description=cmd.description,
                                          colour=discord.Colour.blue())
                    embed.add_field(name='Aliases', value=f'`{aliases}`', inline=False)
                    embed.add_field(name='Parameters', value=param_string, inline=False)
                    embed.add_field(name='Usage', value=f'`{command_prefix}{cmd.usage}`', inline=False)
                    await ctx.reply(embed=embed)
        else:
            # Command string
            cmds: str = ''
            # Response embed
            embed = discord.Embed(title='Help Page',
                                  description=f'Shows the list of all commands\nUse `{command_prefix}help <command>` to get more information about a command',
                                  colour=discord.Colour.blue(), timestamp=datetime.datetime.now())
            for cog in self.bot.cogs:
                if cog in ['Help', 'Events', 'Owner', 'Slash', 'Context']:
                    continue
                for cmd in self.bot.commands:
                    if cmd.cog and cmd.cog.qualified_name == cog and not cmd.hidden:
                        cmds += f'`{str(cmd)}` '
                cmds = cmds[:-1]
                embed.add_field(name=cog.upper(), value=cmds, inline=False)
                cmds = ''
            embed.add_field(name='Slash Commands',
                            value='`avatar` `userinfo` `youtubenotification` `prefix` `warn` `mute` `unmute` `timeout` `code` `roleinfo` `invert` `embed` `datetime`',
                            inline=False)
            embed.add_field(name='Application Context Commands', value='`Generate QR Code` `Scan QR Codes` `User Information`')
            embed.set_footer(text=f'Requested by {ctx.author}',
                             icon_url=str(ctx.author.avatar) if ctx.author.avatar else str(ctx.author.default_avatar))
            await ctx.reply(embed=embed)


# Setup
def setup(bot):
    bot.add_cog(Help(bot))

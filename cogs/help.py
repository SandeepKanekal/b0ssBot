import discord
import datetime
from discord.ext import commands


# Help command
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='help',
                    description='Shows the list of all commands or the information about one command if specified',
                    hidden=True)
    async def help(self, ctx, command_sent=None):
        if command_sent is not None:
            for command in self.bot.commands:
                if command_sent.lower() == command.name.lower():
                    aliases = command.name + ' '
                    for alias in command.aliases:
                        aliases += alias + ' '
                    aliases = aliases[:-1]
                    param_string = ""  # Parameter string
                    if len(command.clean_params) == 0:
                        param_string = 'None'
                    else:
                        for param in command.clean_params:
                            param_string += f'<{param}> '
                        param_string = param_string[:-1]

                    # Response embed
                    embed = discord.Embed(title=f'Help - {command.name}', description=command.description,
                                          colour=discord.Colour.blue())
                    embed.add_field(name='Aliases', value='`' + aliases + '`', inline=False)
                    embed.add_field(name='Parameters', value=f'`{param_string}`', inline=False)
                    if param_string != 'None':
                        embed.add_field(name='Command Usage',
                                        value=f'`{self.bot.command_prefix}{command.name} {param_string}`', inline=False)
                    else:
                        embed.add_field(name='Command Usage', value=f'`{self.bot.command_prefix}{command.name}`',
                                        inline=False)
                    await ctx.reply(embed=embed)
        else:
            # Command string
            cmds = ''
            # Response embed
            embed = discord.Embed(title='Help Page', description='Shows the list of all commands',
                                  colour=discord.Colour.blue())
            for cog in self.bot.cogs:
                if cog == 'Help' or cog == 'Events':
                    continue
                for command in self.bot.commands:
                    if command.cog and command.cog.qualified_name == cog and not command.hidden:
                        cmds += '`' + str(command) + '` '
                cmds = cmds[:-1]
                embed.add_field(name=cog.upper(), value=cmds, inline=False)
                cmds = ''
            embed.set_footer(text=f'Requested by {ctx.author}', icon_url=str(ctx.author.avatar))
            embed.timestamp = datetime.datetime.now()
            await ctx.reply(embed=embed)


# Setup
def setup(bot):
    bot.add_cog(Help(bot))

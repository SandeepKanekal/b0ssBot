# Contains all application context commands.
import discord
import os
import qrcode
import requests
import datetime
from PIL import Image
from pyzbar.pyzbar import decode
from discord.ext import commands
from tools import convert_to_unix_time


class Context(commands.Cog):
    def __init__(self, bot):
        """
        Initializes the context class.
        
        :param bot: The bot object.
        :type bot: commands.Bot
        
        :return: None
        :rtype: None
        """
        self.bot = bot
    
    @commands.message_command(name='Generate QR Code')
    async def generate_qr(self, ctx, message: discord.Message):
        """
        Generates a QR code from a message

        :param ctx: The context of where the message was sent
        :param message: The message to generate a QR code from

        :type ctx: discord.ApplicationContext
        :type message: discord.Message

        :return: None
        :rtype: None
        """
        if not message.content:
            await ctx.respond(content='There is no content in the message provided', ephemeral=True)
            return
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(message.content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        img.save(f'QR_{message.id}.png')
        await ctx.respond(file=discord.File(f'QR_{message.id}.png', 'QR.png'))
        os.remove(f'QR_{message.id}.png')
    
    @generate_qr.error
    async def generate_qr_error(self, ctx, error):
        """
        Error handler for the generate_qr command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: discord.ApplicationContext
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        await ctx.respond(f'Error: `{error}`')

    @commands.message_command(name='Scan QR codes')
    async def scan_qr(self, ctx, message: discord.Message):
        """
        Scans a QR code and returns the result

        :param ctx: The context of where the message was sent
        :param message: The message to scan

        :type ctx: discord.ApplicationContext
        :type message: discord.Message

        :return: None
        :rtype: None
        """
        if message.attachments:
            embed = discord.Embed(title='QR Scan results', colour=0x848585).set_footer(text='QR Scanner', icon_url=self.bot.user.avatar)
            await ctx.interaction.response.defer()

            for index, attachment in enumerate(message.attachments):
                with open(f'{attachment.filename}_{message.id}', 'wb') as f:
                    f.write(requests.get(attachment.url).content)
                try:
                    data = decode(Image.open(f'{attachment.filename}_{message.id}').convert('RGB'))
                    for code in data:
                        embed.add_field(name=f'In Attachment {index + 1}', value=f'```{code.data.decode("utf-8")}```' if code.data else "No data present in the QR Code", inline=False)
                except Exception as e:
                    embed.add_field(name=f'In Attachment {index + 1}', value=f'```{e}```', inline=False)
                os.remove(f'{attachment.filename}_{message.id}')
                    
            if embed.fields:
                await ctx.respond(embed=embed)
            else:
                await ctx.respond('No QR codes found')
            return
            
        await ctx.respond('No attachment found')

    @scan_qr.error
    async def scan_qr_error(self, ctx, error):
        """
        Error handler for the scan_qr command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: discord.ApplicationContext
        :type error: commands.CommandError

        :return: None
        :rtype: None
        """
        await ctx.respond(f'Error: `{error}`')
    
    @commands.user_command(name='User Information')
    async def userinfo(self, ctx, member: discord.Member):
        """
        Get the user's information

        :param ctx: The context of where the message was sent
        :param member: The member to get the information from

        :type ctx: discord.ApplicationContext
        :type member: discord.Member

        :return: None
        :rtype: None
        """
        # Getting the dates
        joined_at = member.joined_at.strftime('%Y-%m-%d %H:%M:%S:%f')  # type: str
        registered_at = member.created_at.strftime('%Y-%m-%d %H:%M:%S:%f')  # type: str

        joined_at = convert_to_unix_time(joined_at)  # type: str
        registered_at = convert_to_unix_time(registered_at)  # type: str

        embed = discord.Embed(colour=member.colour, timestamp=datetime.datetime.now())
        embed.set_author(name=str(member), icon_url=str(member.avatar)) if member.avatar else embed.set_author(
            name=str(member), icon_url=str(member.default_avatar))
        embed.add_field(name='Display Name', value=member.mention, inline=True)
        embed.add_field(name='Top Role', value=member.top_role.mention, inline=True)

        if len(member.roles) > 1:
            role_string = ' '.join([r.mention for r in member.roles][1:])
            embed.add_field(name=f'Roles[{len(member.roles) - 1}]', value=role_string, inline=False)
        else:
            embed.add_field(name='Roles[1]', value=member.top_role.mention, inline=False)

        embed.set_thumbnail(url=str(member.avatar)) if member.avatar else embed.set_thumbnail(
            url=str(member.default_avatar))
        embed.add_field(name='Joined', value=joined_at, inline=True)
        embed.add_field(name='Registered', value=registered_at, inline=True)
        embed.set_footer(text=f'ID: {member.id}')

        await ctx.respond(embed=embed)
    

def setup(bot):
    """
    Sets up the context cog.
    
    :param bot: The bot object.
    
    :type bot: commands.Bot
    
    :return: None
    :rtype: None
    """
    bot.add_cog(Context(bot))

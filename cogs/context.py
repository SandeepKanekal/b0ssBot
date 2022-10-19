# Copyright (c) 2022 Sandeep Kanekal
# Contains all application context commands.
import discord
import os
import qrcode
import requests
import datetime
from PIL import Image, ImageChops
from discord.ext import commands
from tools import convert_to_unix_time, inform_owner


class Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """
        Initializes the context class.
        
        :param bot: The bot object.
        :type bot: commands.Bot
        
        :return: None
        :rtype: None
        """
        self.bot = bot
    
    @commands.message_command(name='Generate QR Code')
    async def generate_qr(self, ctx: discord.ApplicationContext, message: discord.Message):
        """
        Generates a QR code from a message

        :param ctx: The context of where the message was sent
        :param message: The message to generate a QR code from

        :type ctx: discord.ApplicationContext
        :type message: discord.Message

        :return: None
        :rtype: None
        """
        # Inform the user if there is no content in the message
        if not message.content:
            await ctx.respond(content='There is no content in the message provided', ephemeral=True)
            return
        
        # Create a QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(message.content)
        qr.make(fit=True)

        # Save the image
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        img.save(f'QR_{message.id}.png')

        # Send the image
        await ctx.respond(content=f'Message: {message.jump_url}', file=discord.File(f'QR_{message.id}.png', 'QR.png'))

        # Delete the saved image
        os.remove(f'QR_{message.id}.png')
    
    @generate_qr.error
    async def generate_qr_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the generate_qr command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError

        :return: None
        :rtype: None
        """
        await ctx.respond('There was an error generating the QR code! The owner has been informed', ephemeral=True)
        await inform_owner(self.bot, error)

    @commands.message_command(name='Scan QR codes')
    async def scan_qr(self, ctx: discord.ApplicationContext, message: discord.Message):
        """
        Scans a QR code and returns the result

        :param ctx: The context of where the message was sent
        :param message: The message to scan

        :type ctx: discord.ApplicationContext
        :type message: discord.Message

        :return: None
        :rtype: None
        """
        if not message.attachments:
            await ctx.respond('No attachment in the message!', ephemeral=True)
            return

        await ctx.defer()

        # Create embed
        embed = discord.Embed(
            title='QR Scan results', 
            description=f'[Jump to message]({message.jump_url})', 
            colour=0x848585
        ).set_footer(text='QR Scanner', icon_url=self.bot.user.avatar)

        url = 'https://api.qrserver.com/v1/read-qr-code/?fileurl='

        for index, attachment in enumerate(message.attachments):
            if qr_data := requests.get(f'{url}{attachment.url}').json()[0]['symbol'][0]['data']:

                qr_data = qr_data.split('\nQR-Code:')

                for qrd in qr_data:
                    embed.add_field(name=f'In attachement {index+1}', value=f'```{qrd}```', inline=False)
        
        if not embed.fields:
            await ctx.respond('No QR codes found', ephemeral=True)
        else:
            await ctx.respond(embed=embed)

    @scan_qr.error
    async def scan_qr_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the scan_qr command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError

        :return: None
        :rtype: None
        """
        await ctx.respond('There was an error scanning the QR code! The owner has been informed', ephemeral=True)
        await inform_owner(self.bot, error)
    
    @commands.user_command(name='User Information')
    async def userinfo(self, ctx: discord.ApplicationContext, member: discord.Member):
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

        # Converting to unix timestamps
        joined_at = convert_to_unix_time(joined_at)  # type: str
        registered_at = convert_to_unix_time(registered_at)  # type: str

        # Creating the embed
        embed = discord.Embed(colour=member.colour, timestamp=datetime.datetime.now())
        embed.set_author(name=str(member), icon_url=member.display_avatar)
        embed.set_footer(text=f'ID: {member.id}')
        embed.set_thumbnail(url=member.display_avatar)

        # Adding the fields
        embed.add_field(name='Display Name', value=member.mention, inline=True)
        embed.add_field(name='Top Role', value=member.top_role.mention, inline=True)

        if len(member.roles) > 1:
            role_string = ' '.join([r.mention for r in member.roles][1:])
            embed.add_field(name=f'Roles[{len(member.roles) - 1}]', value=role_string, inline=False)
        else:
            embed.add_field(name='Roles[1]', value=member.top_role.mention, inline=False)
        
        embed.add_field(name='Permissions', value=', '.join([p[0].replace('_', ' ').title() for p in member.guild_permissions if p[1]]), inline=False)

        embed.add_field(name='Joined', value=joined_at, inline=True)
        embed.add_field(name='Registered', value=registered_at, inline=True)

        await ctx.respond(embed=embed)

    # noinspection PyUnusedLocal
    @commands.message_command(name='Invert Attachments')
    async def invert_attachments(self, ctx: discord.ApplicationContext, message: discord.Message):
        """
        Inverts the colors of the attachments of a message

        :param ctx: The context of where the message was sent
        :param message: The message to invert the attachments of

        :type ctx: discord.ApplicationContext
        :type message: discord.Message

        :return: None
        :rtype: None
        """
        # Inform the user if there is no attachment in the message.
        if not message.attachments:
            await ctx.respond('No attachment found', ephemeral=True)
            return
        
        # Defer the response
        await ctx.interaction.response.defer()

        content = ''
        files = []

        for index, image in enumerate(message.attachments):
            # Save the image
            with open(f'{index}_{message.id}.png', 'wb') as f:
                f.write(requests.get(image.url).content)
            
            # Check if the size is larger than 8MB
            if os.path.getsize(f'{index}_{message.id}.png') > 8000000:
                content += f'Image {index + 1} is larger than 8 megabytes.'
                os.remove(f'{index}_{message.id}.png')
                continue
            
            # Invert the image
            img = Image.open(f'{index}_{message.id}.png')
            invert = ImageChops.invert(img.convert('RGB'))
            invert.save(f'{index}_{message.id}_inverted.png')

            # Add the file to the list
            files.append(discord.File(f'{index}_{message.id}_inverted.png', filename='invert.png'))

        await ctx.respond(f'Message: {message.jump_url}{content}', files=files)

        files = None  # Raises PermissionError if not set to None before deletion of files.

        # Delete the saved images
        for index in range(len(message.attachments)):
            os.remove(f'{index}_{message.id}.png')
            os.remove(f'{index}_{message.id}_inverted.png')
    
    @invert_attachments.error
    async def invert_attachments_error(self, ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
        """
        Error handler for the invert_attachments command

        :param ctx: The context of where the message was sent
        :param error: The error that occurred

        :type ctx: discord.ApplicationContext
        :type error: discord.ApplicationCommandInvokeError

        :return: None
        :rtype: None
        """
        await ctx.respond('There was an error inverting the attachments! The owner has been informed', ephemeral=True)
        await inform_owner(self.bot, error)


def setup(bot: commands.Bot):
    """
    Sets up the context cog.
    
    :param bot: The bot object.
    
    :type bot: commands.Bot
    
    :return: None
    :rtype: None
    """
    bot.add_cog(Context(bot))

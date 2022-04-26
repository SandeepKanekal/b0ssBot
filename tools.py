import discord
import datetime
import time


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description: str) -> None:
    # Response embed
    embed = discord.Embed(description=description, colour=discord.Colour.red())
    await ctx.send(embed=embed)


# A function to convert datetime to unix time for dynamic date-time displays
def convert_to_unix_time(date_time: str, fmt: str = 'R') -> str:
    date_time = date_time.split(' ')
    date_time1 = date_time[0].split('-')
    date_time2 = date_time[1].split(':')
    date_time1 = [int(x) for x in date_time1]
    date_time2 = [int(x) for x in date_time2]
    datetime_tuple = tuple(date_time1 + date_time2)
    date_time = datetime.datetime(*datetime_tuple)
    return f'<t:{int(time.mktime(date_time.timetuple()))}:{fmt}>'

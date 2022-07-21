# Copyright (c) 2022 Sandeep Kanekal
# Tools for making complex tasks easier
import discord
import datetime
import time
import asyncpraw
import requests
import os
from asyncpraw.reddit import Submission
from typing import List, Dict
from googleapiclient.discovery import build
from sql_tools import SQL


# A function to send embeds when there are false calls or errors
async def send_error_embed(ctx, description: str) -> None:
    """
    Sends an error embed

    Parameters
    ----------
    ctx : commands.Context
        The context of the command
    description : str
        The description of the error

    Returns
    -------
    None
    """
    embed = discord.Embed(description=description, colour=discord.Colour.red())
    await ctx.send(embed=embed)


# A function to convert datetime to unix time for dynamic date-time displays
def convert_to_unix_time(date_time: str, fmt: str = 'R') -> str:
    """
    Converts a datetime to unix time

    Parameters
    ----------
    date_time : str
        The datetime to convert
    fmt : str
        The format of the datetime

    Returns
    -------
    str
    """
    date_time = date_time.split(' ')
    date_time1 = date_time[0].split('-')
    date_time2 = date_time[1].split(':')
    date_time1 = [int(x) for x in date_time1]
    date_time2 = [int(x) for x in date_time2]
    datetime_tuple = tuple(date_time1 + date_time2)
    date_time = datetime.datetime(*datetime_tuple)
    return f'<t:{int(time.mktime(date_time.timetuple()))}:{fmt}>'


# Gets post from the specified subreddit
async def get_posts(subreddit: str) -> List[Submission]:
    """
    Gets the post from the specified subreddit

    Parameters
    ----------
    subreddit : str
        The subreddit to get the post from

    Returns
    -------
    List[Submission]
    """
    reddit = asyncpraw.Reddit('bot', user_agent='bot user agent')
    subreddit = await reddit.subreddit(subreddit)
    return [post async for post in subreddit.hot()]


# Get a random post from the specified subreddit
async def get_random_post(subreddit: str) -> Submission:
    """
    Gets a random post from the specified subreddit

    Parameters
    ----------
    subreddit : str
        The subreddit to get the post from

    Returns
    -------
    Submission
    """
    reddit = asyncpraw.Reddit('bot', user_agent='bot user agent')
    subreddit = await reddit.subreddit(subreddit)
    return await subreddit.random()


# Gets quote from https://zenquotes.io api
def get_quote() -> List[Dict[str, str]]:
    """
    Gets a quote from https://zenquotes.io api

    Returns
    -------
    List[Dict[str, str]]
    """
    return requests.get('https://zenquotes.io/api/random').json()


# Get the video stats for the required track
def get_video_stats(url: str) -> dict:
    """
    Gets the video stats from the url

    Parameters
    ----------
    url : str
        The url of the video

    Returns
    -------
    dict
    """
    youtube = build('youtube', 'v3', developerKey=os.environ.get('youtube_api_key'))
    video_id = url.split('v=')[1]
    response = youtube.videos().list(id=video_id, part='snippet,statistics,contentDetails').execute()
    return response['items'][0]


def format_time(seconds: int) -> str:
    """
    Formats the time

    Parameters
    ----------
    seconds : int
        The time in seconds

    Returns
    -------
    str
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f'{hours}H{minutes}M{seconds}S'
    elif minutes:
        return f'{minutes}M{seconds}S'
    else:
        return f'{seconds}S'


def log_history(member_id: int, query: str, type_: str, timestamp: int, guild_id: int) -> None:
    """
    Logs the history of the internet search

    Parameters
    ----------
    member_id : int
        The member id
    query : str
        The query
    type_ : str
        The type of the query
    timestamp : int
        The timestamp of the query
    guild_id : int
        The guild id
    
    Returns
    -------
    None
    """
    sql = SQL('b0ssbot')
    query = query.replace("'", "''")
    sql.insert('history', ['member_id', 'query', 'type', 'timestamp', 'guild_id'], [f"'{member_id}'", f"'{query}'", f"'{type_}'", f"'{timestamp}'", f"'{guild_id}'"])

    history = sql.select(['*'], 'history', f"member_id = '{member_id}' AND guild_id = '{guild_id}'")
    if len(history) > 50:
        timestamp = history[0][4]
        for index, _ in enumerate(range(len(history) - 50)):
            sql.delete('history', f"timestamp = {timestamp}")
            timestamp = history[index][4]

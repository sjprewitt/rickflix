import gspread
from google.oauth2 import service_account
import pandas as pd
import random
import discord
from discord.ext import commands
from discord import Embed
import requests
import re

#admin discord username here
creator = ''

def is_allowed_user(ctx):
    return ctx.author.id == ALLOWED_USER_ID

# Discord bot token
# I do not have the money or ambition to certify this bot with discord or have it run persistently publicly
# you will have to follow the instructions for creating your own discord bot and create a token that way
TOKEN = ''

# YouTube Data API key
# If you need help attaining a YouTube API key, read the YouTube API guide page here:
# https://developers.google.com/youtube/registering_an_application
# or search for "YouTube API key"

#Alternatively, you can remove/disable this altogether, as the chat output is clunky and buggy.

YOUTUBE_API_KEY = ''

# Establishes the bot's permissions within your channel. Some shaky security stuff here, buyer beware.
intents = discord.Intents.all()
client = discord.Client(intents=intents)

def extract_video_id(url):
    """
    Extracts the YouTube video ID from the given URL.
    """
    video_id = None
    video_id_patterns = [
        r"(?:youtube(?:-nocookie)?\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})",
        r"(?:https?:\/\/)?(?:www\.)?(?:m\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})(?:\S+)?"
    ]
    for pattern in video_id_patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    return video_id


@client.event
async def on_ready():
    print('Bot is ready.') # Confirms bot is running without errors. Someone smarter than me can figure out error flags.


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!hello') or message.content.startswith('!rickflix'):
        channel = message.channel
        msg = "Hey {0.author.mention}, I'm Rickflix! Type !rickhelp for a list of commands!".format(message)
        await channel.send(msg)

    if message.content.startswith('!rickhelp'):
        channel = message.channel
        header_msg = 'Type:'
        firstline_msg = "!ricklist to generate three random movies from this group's movie list."
        secondline_msg = "!rickadd [title] to add a film to the list. SPELLING MATTERS."
        await channel.send(header_msg)
        await channel.send(firstline_msg)
        await channel.send(secondline_msg)

    if message.content.startswith('!ricklist'):
        channel = message.channel
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        # I'm certain there is a safer and more effective method of this. I do not know that method and this has been for personal use.
        #  Insert 'google credentials' for json file w/ movie titles
        credentials = service_account.Credentials.from_service_account_file('', scopes=scope)

        gc = gspread.authorize(credentials)
        # url to google speadsheet w/ movie names
        spreadsheet_url = ''
        spreadsheet = gc.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.sheet1
        data = worksheet.get_all_values()
        header = data.pop(0)
        df = pd.DataFrame(data, columns=header)
        num = len(df)

        def fetch_trailer_link(movie_title, api_key):
            base_url = 'https://www.googleapis.com/youtube/v3/search'
            params = {
                'part': 'snippet',
                'q': movie_title + ' trailer',
                'maxResults': 1,
                'type': 'video',
                'key': api_key
            }
            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                json_data = response.json()
                if 'items' in json_data and len(json_data['items']) > 0:
                    video_id = json_data['items'][0]['id']['videoId']
                    trailer_link = f'https://www.youtube.com/watch?v={video_id}'
                    embedded_player = f'https://www.youtube.com/embed/{video_id}'
                    return trailer_link, embedded_player

            return None, None

        for _ in range(3):
            picked = random.randrange(2, num)
            movie = df.iloc[picked]['Movie']
            trailer_link, embedded_player = fetch_trailer_link(movie, YOUTUBE_API_KEY)
            if trailer_link and embedded_player:
                # Create an embedded message
                embed = Embed(title="Movie Recommendation", color=0x00ff00)
                embed.add_field(name="Movie", value=movie, inline=False)

                await channel.send(embed=embed)
                await channel.send(embedded_player)  # Send the video URL as a separate message


    if message.content.startswith('!rickadd'):
        channel = message.channel
        user = message.author
        msg = message.content.split(' ', 1)[1].strip()  # Extract the movie title from the message content

        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        

        # Insert 'google credentials' here as described above
        credentials = service_account.Credentials.from_service_account_file('', scopes=scope)

        gc = gspread.authorize(credentials)
        # Insert URL to movie list Google spreadsheet here
        spreadsheet_url = ''
        spreadsheet = gc.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.sheet1
        worksheet.append_row([msg])

        response_msg = f"{user.mention}, the movie '{msg}' has been added to the movie list!"
        await channel.send(response_msg)
        
client.run(TOKEN)

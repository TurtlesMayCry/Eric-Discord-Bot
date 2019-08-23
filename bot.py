import discord
import requests
import requests.auth
import json
import asyncio
import time
import giphy_client
import numpy as np
import random
import pprint
import os

from discord.ext import commands
from bs4 import BeautifulSoup
from giphy_client.rest import ApiException

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_KEY')

description = '''
                ---            Eric's bot v0.1.            ---
                --- Use the prefix "~" before each command ---
              '''

bot = commands.Bot(command_prefix='~', description=description)

bot_extentions = (
    'cogs.casino',
    'cogs.reddit',
    'cogs.gifs'
)

for ext in bot_extentions:
    bot.load_extension(ext)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def hello(ctx):
    """Says world"""
    await ctx.send("world")


@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)


@bot.command()
async def bitcoin(ctx):
    """Returns current BTC price from coinmarketcap.com"""
    url = 'https://coinmarketcap.com/currencies/bitcoin/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    mySpan = soup.find('span', class_='h2 text-semi-bold details-panel-item--price__value')
    btcScrape = float(mySpan.text)
    try:
        btcFile = open('btc.txt', 'r')
        btcPrice = float(btcFile.readline().strip())
        if btcScrape < btcPrice:
            await ctx.send('```ini\nThe current price of BTC is [below] $' + str(btcPrice) + '\nPrice: [$' + str(btcScrape) + ']```')
        else:
            await ctx.send('```ini\nThe current price of BTC is [above] $' + str(btcPrice) + '\nPrice: [$' + str(btcScrape) + ']```')
    except ValueError:
        await ctx.send('```The input price is invalid. Please use the "changebtc" command to fix it.```')


@bot.command()
async def changebtc(ctx, price: str):
    '''Change the comparison price for bitcoin command'''
    btcFile = open('btc.txt', 'w')
    btcFile.write(price)
    btcFile.close()


@bot.command(hidden=True)
async def reload(ctx):
    for ext in bot_extentions:
        bot.reload_extension(ext)
        print('extensions reloaded')


@bot.event
async def on_message(message):
    if message.content.startswith('~thumb'):
        channel = message.channel
        await channel.send('Send me that 🍏 reaction, mate')

        def check(reaction, user):
            return user == message.author and str(reaction.emoji) == '🍏'

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await channel.send('👎')
        else:
            await channel.send('🍏')

    await bot.process_commands(message)


bot.run(TOKEN)

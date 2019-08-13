import discord
import requests
import requests.auth
import json
import asyncio
import time
import giphy_client
import numpy as np
import random
import gspread
import pprint
import os

from discord.ext import commands
from bs4 import BeautifulSoup
from giphy_client.rest import ApiException
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_KEY')

description = '''
                ---            Eric's bot v0.1.            ---
                --- Use the prefix "~" before each command ---
              '''

bot = commands.Bot(command_prefix='~', description=description)

# database
# open "User Info" Google Spreadsheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('userinfo.json', scope)
client = gspread.authorize(creds)
sheet = client.open('User Info').sheet1
timestart = time.time()


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


@bot.command()
async def subtop(ctx, subreddit):
    '''Returns the top 5 hottest posts for a specific subreddit'''
    app_id = os.getenv('REDDIT_ID')
    app_secret = os.getenv('REDDIT_APP')
    app_ua = 'Eric\'s Discord Bot v0.1'

    client_auth = requests.auth.HTTPBasicAuth(app_id, app_secret)
    post_data = {'grant_type': 'password', 'username': os.getenv('REDDIT_USER'), 'password': os.getenv('DISCORD_KEY')}
    headers = {'User-Agent': app_ua}
    post = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)

    access_token = 'bearer' + post.json()['access_token']
    headers = {"Authorization": access_token, 'User-Agent': app_ua}

    url = 'https://oauth.reddit.com/r/' + subreddit + '/hot.json?sort=top&t=day&limit=5'
    response = requests.get(url, headers=headers)
    jsondata = json.loads(response.text)

    for i in jsondata['data']['children']:
        score = i['data']['score']
        title = i['data']['title']
        permalink = 'https://www.reddit.com' + i['data']['permalink']
        await ctx.send('```Score:{0}\nTitle:{1}\n```{2}'.format(score, title, permalink))


@bot.command()
async def gif(ctx, keyword):
    '''Returns a gif related to the keyword entered'''
    # create an instance of the API class
    api_instance = giphy_client.DefaultApi()
    api_key = os.getenv('GIPHY')  # str | Giphy API Key.
    tag = keyword  # str | Filters results by specified tag. (optional)
    rating = 'g'  # str | Filters results by specified rating. (optional)
    fmt = 'json'  # str | Used to indicate the expected response format. Default is Json. (optional) (default to json)
    try:
        # Search Endpoint
        api_response = api_instance.gifs_random_get(api_key, tag=tag, fmt=fmt)
        await ctx.send(api_response.data.image_original_url)
    except ApiException as e:
        print("Exception when calling DefaultApi->gifs_search_get: %s\n" % e)


@bot.command()
async def tgif(ctx, keyword):
    apikey = os.getenv('TENOR')
    lmt = 1
    search_term = keyword
    response = requests.get('https://api.tenor.com/v1/random?q={0}&key={1}&limit={2}'.format(search_term, apikey, lmt))
    print(response.content)
    if response.status_code == 200:
        gif = json.loads(response.content)
        await ctx.send(gif['results'][0]['url'])
    else:
        gif = None


@bot.command()
async def tokens(ctx):
    discord_full_user = ctx.message.author.name + '#' + ctx.message.author.discriminator
    users = sheet.get_all_records()
    for userinfo in users:
        if userinfo['ID'] == ctx.message.author.id and userinfo['Username'] == discord_full_user:
            await ctx.send('{0} You currently have {1} tokens.'.format(ctx.message.author.mention, userinfo['Tokens']))
            break
    else:
        await ctx.send('You are not registered into the system. Do you want to initialize your account? (y/n)')

        def check(m):
            return m.content.upper() == 'Y' or m.channel == ctx.message.channel

        userresponse = await bot.wait_for('message', check=check)
        if userresponse.content.upper() != 'Y':
            await ctx.send('Ok, bye.')
        else:
            await ctx.send('I have given you 1000 tokens to start out with. Use the "tokens" command again to see your tokens.')
            row = [str(ctx.message.author.id), discord_full_user, 10000, time.time()]
            sheet.append_row(row)


@bot.command()
async def redeem(ctx):
    '''Allows users to redeem 10000 tokens for the casino. Refreshes 24 hours after use.'''
    usercell = sheet.find(str(ctx.message.author.id))
    redeemcell = sheet.cell(usercell.row, usercell.col + 3)

    gettime = time.time()
    if gettime - float(redeemcell.value) >= 60*60*24:
        tokenscell = sheet.cell(usercell.row, usercell.col + 2)
        tokens = int(tokenscell.value)
        sheet.update_cell(tokenscell.row, tokenscell.col, tokens + 10000)
        sheet.update_cell(redeemcell.row, redeemcell.col, time.time())
        await ctx.send(ctx.message.author.mention + ' You have redeemed your daily 10000 tokens.')
    else:
        await ctx.send('This command is still on cooldown for {} seconds.'.format((60*60*24) - (gettime - float(redeemcell.value))))


@bot.command()
async def slots(ctx, bet: int):
    # global timestart
    # gettime = time.time()
    # print(gettime - timestart)
    # if timestart - gettime >= 60*59:
    #     client = gspread.authorize(creds)
    #     timestart = time.time()

    client.login()
    usercell = sheet.find(str(ctx.message.author.id))
    tokenscell = sheet.cell(usercell.row, usercell.col + 2)
    tokens = int(tokenscell.value)
    bet = abs(bet)
    if bet <= tokens:
        emotes = {'0': ':green_apple:', '1': ':apple:', '2': ':pear:'}
        arr = np.array([['', '', ''], ['', '', ''], ['', '', '']], dtype='object')
        isWin = False
        sheet.update_cell(tokenscell.row, tokenscell.col, str(tokens - bet))
        tokenscell = sheet.cell(usercell.row, usercell.col + 2)
        tokens = int(tokenscell.value)

        def checkEqual(a):
            v = a[0]
            for i in range(0, 3):
                if a[i] != v:
                    return False

            return True

        for i in range(len(arr[0])):
            for x in range(len(arr[0])):
                arr[i][x] = emotes[str(random.randint(0, 2))]

        output = ''
        for row in range(arr[0].size):
            for col in range(arr[0].size):
                output += arr[row][col]
            output += '\n'

        arr2 = arr.transpose()
        for i in range(0, 3):
            if checkEqual(arr[i]) or checkEqual(arr2[i]):
                isWin = True
                sheet.update_cell(tokenscell.row, tokenscell.col, str(tokens + bet*2))

        await ctx.send(output + ('```You won!```' if isWin else '```You lost!```'))
    else:
        await ctx.send('You don\'t have enough tokens to make this bet!')


@bot.command()
async def coin(ctx, bet: int):
    # remember to create a game? class
    message = ctx.message
    bet = abs(bet)
    coin = random.randint(0, 1)
    print(coin)
    usercell = sheet.find(str(ctx.message.author.id))
    tokenscell = sheet.cell(usercell.row, usercell.col + 2)
    tokens = int(tokenscell.value)
    # asyncio to sleep for 2 secs
    if bet <= tokens:
        sheet.update_cell(tokenscell.row, tokenscell.col, str(tokens - bet))
        msg = await ctx.send(message.author.mention + ' Heads or Tails?')
        await msg.add_reaction('1F609')

        def check(m):
            return (m.content.lower() == 'heads' or m.content.lower() == 'tails')

        reply = await bot.wait_for('message', check=check)

        if reply.content.lower() == 'heads' and coin == 0:
            await ctx.send('The coin landed on heads! You win!')
            sheet.update_cell(tokenscell.row, tokenscell.col, str(tokens + bet*2))
        elif reply.content.lower() == 'tails' and coin == 1:
            await ctx.send('The coin landed on tails! You win!')
            sheet.update_cell(tokenscell.row, tokenscell.col, str(tokens + bet*2))
        else:
            await ctx.send('Sorry, the coin landed on ' + ('heads.' if coin == 0 and reply.content.lower() == 'tails' else 'tails.'))
    else:
        await ctx.send('You don\'t have enough tokens to make this bet!')


# @bot.command()
# async def testing(ctx):
#     msg = await ctx.send('test')
#     await msg.add_reaction('1\u20E3')
#     print(str(msg.reaction))
#
#     def check(reaction, user):
#         return user == m.author and


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
    # elif message.content.startswith('~testing'):
    #     channel = message.channel
    #     msg = await ctx.send('test')
    #     await msg.add_reaction('1\u20E3')
    #
    #     def check(reaction, user):
    #         return user == m.author and str(reaction.emoji) == '1\u20E3'
    #
    #     try:
    #         reaction, user = await bot.wait_for('reaction_add')

    await bot.process_commands(message)


# @bot.event
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.MissingRequiredArgument):
#         await ctx.send('{} The slots command is used like this: ~slots <bet_amount>'.format(ctx.message.author.mention))
#
#     await bot.process_commands(ctx.message)


bot.run(TOKEN)

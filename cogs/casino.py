import asyncio
import gspread
import random
import time

from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials

# database
# open "User Info" Google Spreadsheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('info/userinfo.json', scope)
client = gspread.authorize(creds)
sheet = client.open('User Info').sheet1
timestart = time.time()


def retrieveTokens(userID):
    usercell = sheet.find(str(userID))
    tokenscell = sheet.cell(usercell.row, usercell.col + 2)
    tokens = int(tokenscell.value)
    tokensDict = {"cell": tokenscell, "token": tokens}

    return tokensDict


def processBet(winCondition: bool, bet: int, tokensDict):
    if winCondition:
        sheet.update_cell(tokensDict['cell'].row, tokensDict['cell'].col, str(tokensDict['token'] + bet*2))
    else:
        sheet.update_cell(tokensDict['cell'].row, tokensDict['cell'].col, str(tokensDict['token'] - bet))


class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tokens(self, ctx):
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

    @commands.command()
    async def redeem(self, ctx):
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

    @commands.command()
    async def slots(self, ctx, bet: int):
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

    @commands.command()
    async def coin(self, ctx, bet: int):
        # remember to create a game? class
        client.login()
        channel = ctx.message.channel
        bet = abs(bet)
        tokens = retrieveTokens(ctx.message.author.id)
        # asyncio to sleep for 2 secs
        if bet <= tokens['token']:
            coin = random.randint(0, 1)
            msg = await channel.send('Heads or Tails? Click "1" for heads and "2" for tails.')
            await msg.add_reaction('1\u20E3')
            await msg.add_reaction('2\u20E3')

            def check(reaction, user):
                return user == ctx.message.author and (str(reaction.emoji) == '1\u20E3' or str(reaction.emoji) == '2\u20E3')

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                await msg.delete()
            except asyncio.TimeoutError:
                await channel.send('👎')
            else:
                if str(reaction.emoji) == '1\u20E3' and coin == 0:
                    await channel.send('The coin landed on heads! You won!')
                    processBet(True, bet, tokens)
                elif str(reaction.emoji) == '2\u20E3' and coin == 1:
                    await channel.send('The coin landed on tails You won!')
                    processBet(True, bet, tokens)
                else:
                    await channel.send('You lost!')
                    processBet(False, bet, tokens)
        else:
            await ctx.send('You don\'t have enough tokens to make this bet!')


def setup(bot):
    bot.add_cog(Casino(bot))


if __name__ == '__main__':
    print('ok')

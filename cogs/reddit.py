import requests
import json

from discord.ext import commands


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def subtop(self, ctx, subreddit):
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


def setup(bot):
    bot.add_cog(Reddit(bot))

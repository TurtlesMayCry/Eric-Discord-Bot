from discord.ext import commands

class Gifs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def gif(self, ctx, keyword):
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


    @commands.command()
    async def tgif(self, ctx, keyword):
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


def setup(bot):
    bot.add_cog(Gifs(bot))

import discord
import youtube_dl
import asyncio
import queue
import youtube_dl.utils
import os.path

from discord.ext import commands


class Audio(discord.PCMVolumeTransformer):
    def __init__(self, title, duration, url, volume, original):
        self.title = title
        self.duration = duration
        self.link = url
        super(Audio, self).__init__(original, volume)

    def allo(self):
        print(isinstance(self, discord.PCMVolumeTransformer))


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


class Music(commands.Cog):
    def __init__(self, bot, vol=0.3, song_queue=queue.Queue()):
        self.bot = bot
        self.vol = vol
        self.song_queue = song_queue
        self.voice_client = None # take the channel from bot?

    def fileCleanUp(self, name):
        '''Cleans up the file name so that the it matches up'''
        while True:
            index = name.find('/')
            if index == -1:
                return name
            else:
                name = name.replace('/', '_', 1)
                return self.fileCleanUp(name)

    def playNext(self):
        if not self.song_queue.empty():
            current = self.song_queue.get()
            self.voice_client.play(current, after=lambda x: self.playNext())

    @commands.command()
    async def playlist(self, ctx):
        copy_queue = list(self.song_queue.queue)
        if copy_queue == []:
            await ctx.send('No songs are in the playlist')
        else:
            counter = 1
            playlist_string = ''
            for song in copy_queue:
                playlist_string += '{0}. {1}\n'.format(counter, song)
                counter += 1
            await ctx.send(playlist_string)

    @commands.command()
    async def play(self, ctx, *, search: str):
        '''Plays a song from YouTube'''
        if ctx.message.guild.voice_client is None:
            self.voice_client = await ctx.message.author.voice.channel.connect()

        if search.startswith('https://'):
            outtmpl = 'music/%(title)s.mp3'
            extractor = search
        else:
            outtmpl = 'music/' + search + '.mp3'
            extractor = 'ytsearch1:' + search

        ydl_opts = {
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': outtmpl,
            'logger': MyLogger(),
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(extractor, download=False)
            folder = os.path.join('music')
            if search.startswith('https://'):
                video_title = info_dict.get('title', None) + '.mp3'
                file_to_open = os.path.join(folder, video_title)
            else:
                video_title = info_dict['entries'][0].get('title', None) + '.mp3'
                file_to_open = os.path.join(folder, search + '.mp3')

            # file_name = self.fileCleanUp(video_title)

            ffmpeg_exe = os.path.join('ffmpeg', 'bin', 'ffmpeg.exe')

            print(search, extractor, video_title)

            videoDict = {'title': video_title}
            if not self.voice_client.is_playing():
                try:
                    ydl.download([extractor])
                    source = discord.FFmpegPCMAudio(file_to_open, executable=ffmpeg_exe)
                    transformer = discord.PCMVolumeTransformer(source, self.vol)
                    self.voice_client.play(transformer, after=lambda x: self.playNext())
                except discord.ClientException:
                    print('error')
            else:
                source = discord.FFmpegPCMAudio(file_to_open, executable=ffmpeg_exe)
                transformer = discord.PCMVolumeTransformer(source, self.vol)
                self.song_queue.put(transformer)

    @commands.command()
    async def volume(self, ctx, vol: int):
        if vol > 100:
            await ctx.send('Maximum volume is 100')
        elif vol < 0:
            await ctx.send('Minimum volume is 0')
        else:
            self.vol = vol / 100
            self.voice_client.source.volume = vol / 100
            await ctx.send('Volume set!')

    @commands.command()
    async def join(self, ctx):
        '''Summons the bot to your voice channel'''
        try:
            self.voice_client = await ctx.message.author.voice.channel.connect()
        except discord.errors.ClientException:
            self.voice_client = ctx.message.author.voice.channel.guild.voice_client
            print(self.voice_client)
            await self.voice_client.move_to(ctx.message.author.voice.channel)

    @commands.command()
    async def leave(self, ctx):
        await self.voice_client.disconnect()

    @commands.command()
    async def pause(self, ctx):
        if self.voice_client.is_playing():
            self.voice_client.pause()
        else:
            await ctx.send('No song is currently playing.')

    @commands.command()
    async def resume(self, ctx):
        if self.voice_client.is_paused():
            self.voice_client.resume()
        else:
            await ctx.send('No song is currently playing.')

    @commands.command()
    async def stop(self, ctx):
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.stop()
        else:
            await ctx.send('No song is currently playing.')

    @commands.command()
    async def skip(self, ctx):
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.stop()
            self.playNext()


def setup(bot):
    bot.add_cog(Music(bot))

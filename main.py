bot_version = '20220410-2'

from typing import *
import os, dotenv
import threading, asyncio
import datetime

import disnake
from disnake.ext import commands

if os.name != "nt":
    import uvloop
    uvloop.install()

dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = disnake.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

from music import *
INF = int(1e18)

class MusicBot:
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.player: Player = Player()
        self.ui: UI = UI(bot_version)
        self.ui.InitEmbedFooter(bot)

    def sec_to_hms(self, seconds, format) -> str:
        if format == "symbol":
            return datetime.timedelta(seconds=seconds)
        elif format == "zh":
            return f"{seconds//3600} 小時 {seconds//60%60} 分 {seconds%60} 秒"

    async def join(self, ctx: commands.Context, type=None):
        try:
            isinstance(self.player.voice_client.channel, None)
            notin = False
        except: notin = True
        if isinstance(self.player.voice_client, disnake.VoiceClient) or notin == False:
            if type == None:
                await self.ui.JoinAlready(ctx)
            return
        try:
            await self.player.join(ctx.author.voice.channel)
            if isinstance(ctx.author.voice.channel, disnake.StageChannel):
                await self.ui.JoinStage(ctx)
            else:
                await self.ui.JoinNormal(ctx)
        except:
            await self.ui.JoinFailed(ctx)

    async def leave(self, ctx: commands.Context):
        try:
            await self.player.leave()
            await self.ui.LeaveSucceed(ctx)
        except:
            await self.ui.LeaveFailed(ctx)
    
    async def play(self, ctx: commands.Context, *url):
        url = ' '.join(url)
        await self.join(ctx, "playattempt")
        await self.ui.StartSearch(ctx, url, self.player.playlist)
        self.player.search(url, requester=ctx.message.author)
        await self.ui.Embed_AddedToQueue(ctx, self.player.playlist)
        self.player.voice_client = ctx.guild.voice_client
        self.bot.loop.create_task(self._mainloop(ctx))

    async def _mainloop(self, ctx: commands.Context):
        if (self.player.in_mainloop):
            return
        self.player.in_mainloop = True
        
        while (len(self.player.playlist)):
            if not self.player.isskip:
                await self.ui.StartPlaying(ctx, self.player.playlist, self.player.ismute)
            else:
                self.player.isskip = False
            await self.player.play()
            await self.player.wait()
            self.player.playlist[0].cleanup(self.player.volumelevel)
            self.player.playlist.rule()

        self.player.in_mainloop = False
        await self.ui.DonePlaying(ctx)

    async def pause(self, ctx: commands.Context):
        try:
            self.player.pause()
            await self.ui.PauseSucceed(ctx)
        except:
            await self.ui.PauseFailed(ctx)

    async def resume(self, ctx: commands.Context):
        try:
            self.player.resume()
            await self.ui.ResumeSucceed(ctx)
        except:
            await self.ui.ResumeFailed(ctx)

    async def skip(self, ctx: commands.Context):
        try:
            self.player.skip()
            await self.ui.SkipSucceed(ctx, self.player.playlist, self.player.ismute)
        except:
            await self.ui.SkipFailed(ctx)

    async def stop(self, ctx: commands.Context):
        try:
            self.player.stop()
            await self.ui.StopSucceed(ctx)
        except:
            await self.ui.StopFailed(ctx)

    async def mute(self, ctx):
        if self.ismute: await self.volume(ctx, 100.0, unmute=True)
        else: await self.volume(ctx, 0.0)

    async def volume(self, ctx: commands.Context, percent: Union[float, str]=None, unmute: bool=False):
        if not isinstance(percent, float) and percent is not None:
            await self.ui.VolumeAdjustFailed(ctx)
            return
        self.player.volume(percent / 100)
        if percent == 0 or (percent == 100 and unmute):
            self.player.ismute = await self.ui.MuteorUnMute(ctx, percent, self.player)
        else:
            self.player.ismute = await self.ui.VolumeAdjust(ctx, percent, self.player)

    async def seek(self, ctx: commands.Context, timestamp: Union[float, str]):
        if not isinstance(timestamp, float):
            return await ctx.send('Fail to seek. Maybe you request an invalid timestamp')
        self.player.seek(timestamp)
        await ctx.send('Seek successfully')

    async def restart(self, ctx: commands.Context):
        self.player.seek(0)
        await ctx.send(f'''
        **:repeat: | 重播歌曲**
        歌曲已重新開始播放
        *輸入 **{bot.command_prefix}pause** 以暫停播放*
        ''')

    async def single_loop(self, ctx: commands.Context, times: Union[int, str]=INF):
        print(times)
        print(type(times))
        if not isinstance(times, int):
            return await ctx.send('Fail to loop. Maybe you request an invalid times')
        self.player.playlist.single_loop(times)
        await ctx.send('Enable single song loop sucessfully')

    async def whole_loop(self, ctx: commands.Context):
        self.player.playlist.whole_loop()
        await ctx.send('Enable whole queue loop successfully')

    async def show(self, ctx: commands.Context):
        pass

    async def remove(self, ctx: commands.Context, idx: Union[int, str]):
        try:
            self.player.playlist.pop(idx)
            await ctx.send('Remove successfully')
        except (IndexError, TypeError):
            await ctx.send('Fail to remove. Maybe you request an invalid index')
    
    async def swap(self, ctx: commands.Context, idx1: Union[int, str], idx2: Union[int, str]):
        try:
            self.player.playlist.swap(idx1, idx2)
            await ctx.send('Swap successfully')
        except (IndexError, TypeError):
            await ctx.send('Fail to swap. Maybe you request an invalid index')

    async def move_to(self, ctx: commands.Context, origin: Union[int, str], new: Union[int, str]):
        try:
            self.player.playlist.move_to(origin, new)
            await ctx.send('Move successfully')
        except (IndexError, TypeError):
            await ctx.send('Fail to move. Maybe you request an invalid index')


class Router(commands.Cog):
    '''a router to fetch the right musicbot token from a guild request'''
 
    bot: commands.Bot
    router: Dict[int, MusicBot]
    ui: UI

    def __init__(self, bot):
        commands.Cog.__init__(self)
        self.bot: commands.Bot = bot
        self.router: Dict[int, MusicBot] = {}
        self.ui = UI(bot_version)
    
    @commands.command(name='join')
    async def join(self, ctx: commands.Context, jointype=None):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].join(ctx, jointype)

    @commands.command(name='leave')
    async def leave(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].leave(ctx)

    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx: commands.Context, *url):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].play(ctx, *url)

    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].pause(ctx)

    @commands.command(name='resume')
    async def resume(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].resume(ctx)

    @commands.command(name='skip')
    async def skip(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].skip(ctx)

    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].stop(ctx)

    @commands.command(name="mute")
    async def mute(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].mute(ctx)

    @commands.command(name='volume')
    async def volume(self, ctx: commands.Context, percent: Union[float, str]=None, unmute: bool=False):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].volume(ctx, percent, unmute)

    @commands.command(name='seek')
    async def seek(self, ctx: commands.Context, timestamp: Union[float, str]):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].seek(ctx, timestamp)

    @commands.command(name='restart', aliases=['replay'])
    async def restart(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].restart(ctx)

    @commands.command(name='loop', aliases=['songloop'])
    async def single_loop(self, ctx: commands.Context, times: Union[int, str]=INF):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].single_loop(ctx, times)

    @commands.command(name='wholeloop', aliases=['queueloop', 'qloop'])
    async def whole_loop(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].whole_loop(ctx)

    @commands.command(name='show', aliases=['queuelist', 'queue'])
    async def show(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].show(ctx)

    @commands.command(name='remove', aliases=['queuedel'])
    async def remove(self, ctx: commands.Context, idx: Union[int, str]):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].remove(ctx, idx)
    
    @commands.command(name='swap')
    async def swap(self, ctx: commands.Context, idx1: Union[int, str], idx2: Union[int, str]):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].swap(ctx, idx1, idx2)

    @commands.command(name='move_to', aliases=['insert_to'])
    async def move_to(self, ctx: commands.Context, origin: Union[int, str], new: Union[int, str]):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].move_to(ctx, origin, new)

    # Error handler
    # @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        else:
            print(error)
            await ctx.send(f'''
            **:no_entry: | 失敗 | UNKNOWNERROR**
            執行指令時發生了一點未知問題，請稍候再嘗試一次
            --------
            技術資訊:
            {error}
            --------
            *若您覺得有Bug或錯誤，請參照上方資訊及代碼回報至 Github*
            ''') 

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'''
    =========================================
    Codename TKablent | Version Alpha
    Copyright 2022-present @ TK Entertainment
    Shared under CC-NC-SS-4.0 license
    =========================================
    
    Discord Bot TOKEN | {TOKEN}

    If there is any problem, open an Issue with log
    else no any response or answer

    If there isn't any exception under this message,
    That means bot is online without any problem.
    若此訊息下方沒有任何錯誤訊息
    即代表此機器人已成功開機
    ''')
        self.ui.InitEmbedFooter(bot)


bot.add_cog(Router(bot))

try:
    bot.run(TOKEN)
except AttributeError:
    print(f'''
    =========================================
    Codename TKablent | Version Alpha
    Copyright 2022-present @ TK Entertainment
    Shared under CC-NC-SS-4.0 license
    =========================================
    
    Discord Bot TOKEN | Invaild 無效

    我們在準備您的機器人時發生了一點問題
    We encountered some problem when the bot is getting ready
    
    似乎您提供在 .env 檔案中的 TOKEN 是無效的
    請確認您已在 .env 檔案中輸入有效且完整的 TOKEN
    It looks like your TOKEN is invaild
    Please make sure that your Discord Bot TOKEN is already in .env file
    and it's a VAILD TOKEN.
    ''')
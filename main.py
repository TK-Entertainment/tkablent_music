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

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.player: Player = Player()
        self.ui: UI = UI(bot_version)

    def sec_to_hms(self, seconds, format) -> str:
        if format == "symbol":
            return datetime.timedelta(seconds=seconds)
        elif format == "zh":
            return f"{seconds//3600} 小時 {seconds//60%60} 分 {seconds%60} 秒"

    @commands.command(name='join')
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

    @commands.command(name='leave')
    async def leave(self, ctx: commands.Context):
        try:
            await self.player.leave()
            await self.ui.LeaveSucceed(ctx)
        except:
            await self.ui.LeaveFailed(ctx)

    @commands.command(name='play', aliases=['p'])
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
            await self.ui.StartPlaying(ctx, self.player.playlist, self.player.ismute)
            await self.player.play()
            await self.player.wait()
            self.player.playlist[0].cleanup(self.player.volumelevel)
            self.player.playlist.rule()

        self.player.in_mainloop = False
        await self.ui.DonePlaying(ctx)

    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context):
        try:
            self.player.pause()
            await self.ui.PauseSucceed(ctx)
        except:
            await self.ui.PauseFailed(ctx)

    @commands.command(name='resume')
    async def resume(self, ctx: commands.Context):
        try:
            self.player.resume()
            await self.ui.ResumeSucceed(ctx)
        except:
            await self.ui.ResumeFailed(ctx)

    @commands.command(name='skip')
    async def skip(self, ctx: commands.Context):
        self.player.skip()
        await ctx.send(f'''
        **:fast_forward: | 跳過歌曲**
        歌曲已成功跳過，即將播放下一首歌曲
        *輸入 **{bot.command_prefix}play** 以加入新歌曲*
        ''')

    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context):
        self.player.stop()
        await ctx.send(f'''
        **:stop_button: | 停止播放**
        歌曲已停止播放
        *輸入 **{bot.command_prefix}play** 以重新開始播放*
        ''')

    @commands.command(name="mute")
    async def mute(self, ctx):
        if self.ismute: await self.volume(ctx, 100.0)
        else: await self.volume(ctx, 0.0)

    @commands.command(name='volume')
    async def volume(self, ctx: commands.Context, percent: Union[float, str]=None):
        if percent == None: 
            await ctx.send(f'''
        **:loud_sound: | 音量調整**
            目前音量為 {self.player.volumelevel*100}%
        ''')
            return
        if not isinstance(percent, float):
            return await ctx.send(f'''
            **:no_entry: | 失敗 | SA01**
            你輸入的音量百分比無效，無法調整音量
            請以百分比格式(ex. 100%)執行指令
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{bot.command_prefix}volume** 來調整音量*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
        if (percent / 100) == self.player.volumelevel:
            await ctx.send(f'''
        **:loud_sound: | 音量調整**
            音量沒有變更，仍為 {percent}%
        ''')
        elif self.ismute and percent == 100:
            await ctx.send(f'''
        **:speaker: | 解除靜音**
            音量已設定為 100%，目前已解除靜音模式
        ''')
            self.ismute = False
        elif percent == 0: 
            await ctx.send(f'''
        **:mute: | 靜音**
            音量已設定為 0%，目前處於靜音模式
        ''')
            self.ismute = True
        elif (percent / 100) > self.player.volumelevel:
            await ctx.send(f'''
        **:loud_sound: | 調高音量**
            音量已設定為 {percent}%
        ''')
            self.ismute = False
        elif (percent / 100) < self.player.volumelevel:
            await ctx.send(f'''
        **:sound: | 降低音量**
            音量已設定為 {percent}%
        ''')
            self.ismute = False
        self.player.volume(percent / 100)
        await self.playinfo.edit(content=f'''
            **:arrow_forward: | 正在播放以下歌曲**
            *輸入 **{bot.command_prefix}pause** 以暫停播放*
            ''', embed=self.player.playlist[0].info(embed_op, self.sec_to_hms, bot.command_prefix, currentpl=self.player.playlist, mute=self.ismute))

    @commands.command(name='seek')
    async def seek(self, ctx: commands.Context, timestamp: Union[float, str]):
        if not isinstance(timestamp, float):
            return await ctx.send('Fail to seek. Maybe you request an invalid timestamp')
        self.player.seek(timestamp)
        await ctx.send('Seek successfully')

    @commands.command(name='restart', aliases=['replay'])
    async def restart(self, ctx: commands.Context):
        self.player.seek(0)
        await ctx.send(f'''
        **:repeat: | 重播歌曲**
        歌曲已重新開始播放
        *輸入 **{bot.command_prefix}pause** 以暫停播放*
        ''')

    @commands.command(name='loop', aliases=['songloop'])
    async def single_loop(self, ctx: commands.Context, times: Union[int, str]=INF):
        print(times)
        print(type(times))
        if not isinstance(times, int):
            return await ctx.send('Fail to loop. Maybe you request an invalid times')
        self.player.playlist.single_loop(times)
        await ctx.send('Enable single song loop sucessfully')

    @commands.command(name='wholeloop', aliases=['queueloop', 'qloop'])
    async def whole_loop(self, ctx: commands.Context):
        self.player.playlist.whole_loop()
        await ctx.send('Enable whole queue loop successfully')

    @commands.command(name='show', aliases=['queuelist', 'queue'])
    async def show(self, ctx: commands.Context):
        pass

    @commands.command(name='remove', aliases=['queuedel'])
    async def remove(self, ctx: commands.Context, idx: Union[int, str]):
        try:
            self.player.playlist.pop(idx)
            await ctx.send('Remove successfully')
        except (IndexError, TypeError):
            await ctx.send('Fail to remove. Maybe you request an invalid index')
    
    @commands.command(name='swap')
    async def swap(self, ctx: commands.Context, idx1: Union[int, str], idx2: Union[int, str]):
        try:
            self.player.playlist.swap(idx1, idx2)
            await ctx.send('Swap successfully')
        except (IndexError, TypeError):
            await ctx.send('Fail to swap. Maybe you request an invalid index')

    @commands.command(name='move_to', aliases=['insert_to'])
    async def move_to(self, ctx: commands.Context, origin: Union[int, str], new: Union[int, str]):
        try:
            self.player.playlist.move_to(origin, new)
            await ctx.send('Move successfully')
        except (IndexError, TypeError):
            await ctx.send('Fail to move. Maybe you request an invalid index')

    # Error handler
    @commands.Cog.listener()
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

bot.add_cog(MusicBot(bot))

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
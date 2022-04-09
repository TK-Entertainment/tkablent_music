bot_version = 'Build 20220410-1'

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

@bot.event
async def on_ready():
    global embed_op
    print(f'''
    =========================================
    Codename TKablent | Version Confidential
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
    
    cdt = datetime.datetime.now().date()
    year = cdt.strftime("%Y")
    embed_op = {
        'footer': {'text': f"{bot.user.name} | 版本: {bot_version}\nCopyright @ {year} TK Entertainment", 'icon_url': "https://i.imgur.com/wApgX8J.png"},
    }

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.player = Player()

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
                await ctx.send(f'''
                **:hushed: | 我已經加入頻道囉**
            不需要再把我加入同一個頻道囉
            *若要更換頻道
            輸入 **{bot.command_prefix}leave** 以離開原有頻道
            然後使用 **{bot.command_prefix}join 加入新的頻道***
                ''')
            return
        try:
            await self.player.join(ctx.author.voice.channel)
            if isinstance(ctx.author.voice.channel, disnake.StageChannel):
                await ctx.send(f'''
                **:inbox_tray: | 已加入舞台頻道**
            已成功加入 {ctx.author.voice.channel.name} 舞台頻道
                ''')
            else:
                await ctx.send(f'''
                **:inbox_tray: | 已加入語音頻道**
            已成功加入 {ctx.author.voice.channel.name} 語音頻道
                ''')
        except:
            await ctx.send(f'''
            **:no_entry: | 失敗 | JOINFAIL**
            請確認您是否已加入一個語音頻道
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{bot.command_prefix}join** 來把我加入頻道*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')

    @commands.command(name='leave')
    async def leave(self, ctx: commands.Context):
        try:
            await self.player.leave()
            await ctx.send(f'''
            **:outbox_tray: | 已離開語音/舞台頻道**
            已停止所有音樂並離開目前所在的語音/舞台頻道
            ''')
        except:
            await ctx.send(f'''
            **:no_entry: | 失敗 | LEAVEFAIL**
            請確認您是否已加入一個語音/舞台頻道，或機器人並不在頻道中
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{bot.command_prefix}leave** 來讓我離開頻道*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')

    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx: commands.Context, *url):
        addmes = False
        url = ' '.join(url)
        await self.join(ctx, "playattempt")
        if ("http" not in url) and ("www" not in url):
            await ctx.send(f'''
        **:mag_right: | 開始搜尋 | {url}**
            請稍候... 機器人已開始搜尋歌曲，若搜尋成功即會顯示歌曲資訊並開始自動播放
        ''')
        if len(self.player.playlist) != 0: addmes = True
        self.player.search(url, requester=ctx.message.author)
        # If queue has more than 2 songs, then show message when
        # user use play command
        if addmes == True:
            index = len(self.player.playlist) - 1
            await ctx.send(f'''
        **:white_check_mark: | 成功加入隊列**
            以下歌曲已加入隊列中，為第 **{len(self.player.playlist)}** 首歌
        ''', embed=self.player.playlist[index].info(embed_op, self.sec_to_hms, color="green"))
        #
        self.player.voice_client = ctx.guild.voice_client
        self.bot.loop.create_task(self._mainloop(ctx))

    async def _mainloop(self, ctx: commands.Context):
        if (self.player.in_mainloop):
            return
        self.player.in_mainloop = True
        
        while (len(self.player.playlist)):
            # If queue has more than 2 songs, then show the remain count.
            if len(self.player.playlist) > 1:
                mes = f'''
            **:arrow_forward: | 正在播放以下歌曲 | 隊列中還剩餘 {len(self.player.playlist)} 首歌**
            *輸入 **{bot.command_prefix}pause** 以暫停播放*
                '''
            else:
                mes = f'''
            **:arrow_forward: | 正在播放以下歌曲**
            *輸入 **{bot.command_prefix}pause** 以暫停播放*
                '''
            ####
            await ctx.send(mes, embed=self.player.playlist[0].info(embed_op, self.sec_to_hms, bot.command_prefix))
            await self.player.play()
            await self.player.wait()
            self.player.playlist.rule()

        self.player.in_mainloop = False
        await ctx.send(f'''
        **:clock4: | 播放完畢，等待播放動作**
            候播清單已全數播放完畢，等待使用者送出播放指令
            *輸入 **{bot.command_prefix}play [URL/歌曲名稱]** 即可播放/搜尋*
        ''')

    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context):
        try:
            self.player.pause()
            await ctx.send(f'''
            **:pause_button: | 暫停歌曲**
            歌曲已暫停播放
            *輸入 **{bot.command_prefix}resume** 以繼續播放*
            ''')
        except:
            await ctx.send(f'''
            **:no_entry: | 失敗 | PL01**
            請確認目前有歌曲正在播放，或是當前歌曲並非處於暫停狀態，亦或是候播清單是否為空
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{bot.command_prefix}pause** 來暫停音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')

    @commands.command(name='resume')
    async def resume(self, ctx: commands.Context):
        try:
            self.player.resume()
            await ctx.send(f'''
            **:arrow_forward: | 續播歌曲**
            歌曲已繼續播放
            *輸入 **{bot.command_prefix}pause** 以暫停播放*
            ''')
        except:
            await ctx.send(f'''
            **:no_entry: | 失敗 | PL02**
            請確認目前有處於暫停狀態的歌曲，或是候播清單是否為空
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{bot.command_prefix}resume** 來續播音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')


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

bot.add_cog(MusicBot(bot))

try:
    bot.run(TOKEN)
except:
    print(f'''
    =========================================
    Codename TKablent | Version Confidential
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
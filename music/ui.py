from . import *
from typing import *
from enum import Enum
import disnake
from disnake.ext import commands
import datetime

searchmes: disnake.Message = None
addmes: bool = False
issearch: bool = False

# Variables for two kinds of message
# flag for local server, need to change for multiple server
playinfo: Coroutine[Any, Any, disnake.Message] = None

# Just for fetching current year
cdt = datetime.datetime.now().date()
year = cdt.strftime("%Y")

def sec_to_hms(self, seconds, format) -> str:
    if format == "symbol":
        return datetime.timedelta(seconds=seconds)
    elif format == "zh":
        return f"{seconds//3600} 小時 {seconds//60%60} 分 {seconds%60} 秒"

class UI:
    def __init__(self, bot_version):
        self.__bot_version__: str = bot_version


    def InitEmbedFooter(self, bot) -> None:
        self.__bot__: commands.Bot = bot
        self.__embed_opt__: dict = {
        'footer': {'text': f"{self.__bot__.user.name} | 版本: {self.__bot_version__}\nCopyright @ {year} TK Entertainment", 'icon_url': "https://i.imgur.com/wApgX8J.png"},
        }
    ########
    # Join #
    ########
    async def JoinNormal(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:inbox_tray: | 已加入語音頻道**
            已成功加入 {ctx.author.voice.channel.name} 語音頻道
                ''')
    async def JoinStage(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:inbox_tray: | 已加入舞台頻道**
            已成功加入 {ctx.author.voice.channel.name} 舞台頻道
                ''')
    async def JoinAlready(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:hushed: | 我已經加入頻道囉**
            不需要再把我加入同一個頻道囉
            *若要更換頻道
            輸入 **{self.__bot__.command_prefix}leave** 以離開原有頻道
            然後使用 **{self.__bot__.command_prefix}join 加入新的頻道***
                ''')
    async def JoinFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | JOINFAIL**
            請確認您是否已加入一個語音頻道
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.__bot__.command_prefix}join** 來把我加入頻道*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    #########
    # Leave #
    #########
    async def LeaveSucceed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:outbox_tray: | 已離開語音/舞台頻道**
            已停止所有音樂並離開目前所在的語音/舞台頻道
            ''')
    async def LeaveFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | LEAVEFAIL**
            請確認您是否已加入一個語音/舞台頻道，或機器人並不在頻道中
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.__bot__.command_prefix}leave** 來讓我離開頻道*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    ##########
    # Search #
    ##########
    async def StartSearch(self, ctx: commands.Context, url: str, playlist: Playlist) -> disnake.Message:
        global searchmes, addmes, issearch
        if ("http" not in url) and ("www" not in url):
            searchmes =  await ctx.send(f'''
            **:mag_right: | 開始搜尋 | {url}**
            請稍候... 機器人已開始搜尋歌曲，若搜尋成功即會顯示歌曲資訊並開始自動播放
            ''')
            issearch = True
        addmes = len(playlist) != 0
    
    ########
    # Info #
    ########
    def __SongInfo__(self, color: str=None, playlist: Playlist=None, index: int=0, mute: bool=False):
        if color == "green": colorcode = disnake.Colour.from_rgb(97, 219, 83)
        else: colorcode = disnake.Colour.from_rgb(255, 255, 255)
        embed = disnake.Embed(title=playlist[index].title, url=playlist[index].watch_url, colour=colorcode)
        embed.add_field(name="作者", value=f'[{playlist[index].author}]({playlist[index].channel_url})', inline=True)
        if playlist[index].is_stream: 
            if color == None: embed.add_field(name="結束播放", value=f"輸入 ⏩ {self.__bot__.command_prefix}skip / ⏹️ {self.__bot__.command_prefix}stop\n來結束播放此直播", inline=True)
            if mute: embed.set_author(name=f"這首歌由 {playlist[index].requester.name}#{playlist[index].requester.tag} 點歌 | 🔴 直播 | 🔇 靜音", icon_url=playlist[index].requester.display_avatar)
            else: embed.set_author(name=f"這首歌由 {playlist[index].requester.name}#{playlist[index].requester.tag} 點歌 | 🔴 直播", icon_url=playlist[index].requester.display_avatar)
        else: 
            embed.add_field(name="歌曲時長", value=sec_to_hms(self, playlist[index].length, "zh"), inline=True)
            # The mute notice
            if mute: embed.set_author(name=f"這首歌由 {playlist[index].requester.name}#{playlist[index].requester.tag} 點歌 | 🔇 靜音", icon_url=playlist[index].requester.display_avatar)
            else: embed.set_author(name=f"這首歌由 {playlist[index].requester.name}#{playlist[index].requester.tag} 點歌", icon_url=playlist[index].requester.display_avatar)
        if len(playlist) > 1:
            queuelist: str = ""
            queuelist += f"1." + playlist[1].title + "\n"
            if len(playlist) > 2: queuelist += f"...還有 {len(playlist)-2} 首歌"
            embed.add_field(name=f"待播清單 | {len(playlist)-1} 首歌待播中", value=queuelist, inline=False)
        embed.set_thumbnail(url=playlist[index].thumbnail_url)
        embed = disnake.Embed.from_dict(dict(**embed.to_dict(), **self.__embed_opt__))
        return embed
    ########
    # Play #
    ########
    async def StartPlaying(self, ctx: commands.Context, playlist: Playlist, ismute: bool):
        global playinfo
        playinfo = await ctx.send(f'''
            **:arrow_forward: | 正在播放以下歌曲**
            *輸入 **{self.__bot__.command_prefix}pause** 以暫停播放*
            ''', embed=self.__SongInfo__(playlist=playlist, mute=ismute))
    async def DonePlaying(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:clock4: | 播放完畢，等待播放動作**
            候播清單已全數播放完畢，等待使用者送出播放指令
            *輸入 **{self.__bot__.command_prefix}play [URL/歌曲名稱]** 即可播放/搜尋*
        ''')
    #########
    # Pause #
    ######### 
    async def PauseSucceed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:pause_button: | 暫停歌曲**
            歌曲已暫停播放
            *輸入 **{self.__bot__.command_prefix}resume** 以繼續播放*
            ''')
    async def PauseFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | PL01**
            請確認目前有歌曲正在播放，或是當前歌曲並非處於暫停狀態，亦或是候播清單是否為空
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.__bot__.command_prefix}pause** 來暫停音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    ##########
    # Resume #
    ##########
    async def ResumeSucceed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:arrow_forward: | 續播歌曲**
            歌曲已繼續播放
            *輸入 **{self.__bot__.command_prefix}pause** 以暫停播放*
            ''')
    async def ResumeFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | PL02**
            請確認目前有處於暫停狀態的歌曲，或是候播清單是否為空
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.__bot__.command_prefix}resume** 來續播音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    #########
    # Queue #
    #########
    async def Embed_AddedToQueue(self, ctx: commands.Context, playlist: Playlist) -> None:
        # If queue has more than 2 songs, then show message when
        # user use play command
        if addmes == True:
            index = len(playlist) - 1
            mes = f'''
            **:white_check_mark: | 成功加入隊列**
                以下歌曲已加入隊列中，為第 **{len(playlist)}** 首歌
            '''
            if not issearch: await ctx.send(mes, embed=self.__SongInfo__(self.__embed_opt__, color="green", playlist=playlist, index=index))
            else: await searchmes.edit(content=mes, embed=self.__SongInfo__(self.__embed_opt__, color="green", playlist=playlist, index=index))
        else: 
            if issearch: await searchmes.delete()
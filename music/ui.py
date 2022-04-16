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
    sec = int(seconds%60); min = int(seconds//60%60); hr = int(seconds//3600)
    if format == "symbol":
        if hr == 0:
            return "{}{}:{}{}".format("0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
        else:
            return "{}{}:{}{}:{}{}".format("0" if hr < 10 else "", hr, "0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
    elif format == "zh":
        if seconds//60%60 == 0:
            return f"{sec} 秒"
        elif seconds//3600 == 0:
            return f"{min} 分 {sec} 秒"
        else:
            return f"{hr} 小時 {min} 分 {sec} 秒"
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
        else: issearch = False
        addmes = len(playlist) != 0
    
    ########
    # Info #
    ########
    def __SongInfo__(self, color: str=None, playlist: Playlist=None, index: int=0, mute: bool=False):
        if color == "green": colorcode = disnake.Colour.from_rgb(97, 219, 83)
        elif color == "yellow": colorcode = disnake.Colour.from_rgb(229, 199, 13)
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
    async def __UpdateSongInfo__(self, playlist: Playlist, ismute: bool):
        await playinfo.edit(content=f'''
            **:arrow_forward: | 正在播放以下歌曲**
            *輸入 **{self.__bot__.command_prefix}pause** 以暫停播放*
            ''', embed=self.__SongInfo__(playlist=playlist, mute=ismute))
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
    ########
    # Skip #
    ########
    async def SkipSucceed(self, ctx: commands.Context, playlist: Playlist=None, mute: bool= None) -> None:
        global playinfo
        if len(playlist) > 0:
            playinfo = await ctx.send(f'''
            **:fast_forward: | 跳過歌曲**
            目前歌曲已成功跳過，即將播放下一首歌曲，資訊如下所示
            *輸入 **{self.__bot__.command_prefix}play** 以加入新歌曲*
            ''', embed=self.__SongInfo__(color="yellow", playlist=playlist, index=0, mute=mute))
        else:
            await ctx.send(f'''
            **:fast_forward: | 跳過歌曲**
            目前歌曲已成功跳過，因候播清單已無歌曲，將完成播放
            *輸入 **{self.__bot__.command_prefix}play** 以加入新歌曲*
            ''')   
    async def SkipFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | SK01**
            無法跳過歌曲，請確認目前候播清單是否為空
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.__bot__.command_prefix}skip 來跳過音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    ########
    # Stop #
    ########
    async def StopSucceed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:stop_button: | 停止播放**
            歌曲已停止播放
            *輸入 **{self.__bot__.command_prefix}play** 以重新開始播放*
            ''')
    async def StopFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | ST01**
            無法停止播放歌曲，請確認目前是否有歌曲播放，或候播清單是否為空
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.__bot__.command_prefix}stop 來停止播放音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    ##########
    # Volume #
    ##########
    async def VolumeAdjust(self, ctx: commands.Context, percent: Union[float, str], player: Player):
        mute = player.ismute
        # If percent = None, show current volume
        if percent == None: 
            await ctx.send(f'''
            **:loud_sound: | 音量調整**
            目前音量為 {player.volumelevel*100}%
        ''')
            return mute
        # Volume unchanged
        if (percent / 100) == player.volumelevel:
            await ctx.send(f'''
            **:loud_sound: | 音量調整**
            音量沒有變更，仍為 {percent}%
        ''')
        # Volume up
        elif (percent / 100) > player.volumelevel:
            await ctx.send(f'''
            **:loud_sound: | 調高音量**
            音量已設定為 {percent}%
        ''')
            mute = False
        # Volume down
        elif (percent / 100) < player.volumelevel:
            await ctx.send(f'''
            **:sound: | 降低音量**
            音量已設定為 {percent}%
        ''')
            mute = False
        await self.__UpdateSongInfo__(player.playlist, mute)
        return mute
    async def MuteorUnMute(self, ctx: commands.Context, percent: Union[float, str], player: Player) -> bool:
        mute = player.ismute
        if mute and percent == 100:
            await ctx.send(f'''
            **:speaker: | 解除靜音**
            音量已設定為 100%，目前已解除靜音模式
        ''')
            mute = False
        elif percent == 0: 
            await ctx.send(f'''
            **:mute: | 靜音**
            音量已設定為 0%，目前處於靜音模式
        ''')
            mute = True
        await self.__UpdateSongInfo__(player.playlist, mute)
        return mute
    async def VolumeAdjustFailed(self, ctx) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | SA01**
            無法調整音量，請確認您輸入的音量百分比是否有效
            請以百分比格式(ex. 100%)執行指令
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.__bot__.command_prefix}volume** 來調整音量*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    ########
    # Seek #
    ########
    def __ProgressBar__(self, timestamp: int, duration: int, amount: int=15) -> str:
        bar = ''
        persent = timestamp / duration
        bar += "**"
        for i in range(round(persent*amount)):
            bar += '⎯'
        bar += "**⬤**"
        for i in range(round(persent*amount)+1, amount+1):
            bar += '⎯'
        bar += "**"
        return bar
    async def SeekSucceed(self, ctx: commands.Context, timestamp: int, player: Player) -> None:
        seektime = sec_to_hms(self, timestamp, "symbol"); duration = sec_to_hms(self, player.playlist[0].length, "symbol")
        bar = self.__ProgressBar__(timestamp, player.playlist[0].length)
        await ctx.send(f'''
            **:timer: | 跳轉歌曲**
            已成功跳轉至指定時間
            **{seektime}** {bar} **{duration}**
            *輸入 **{self.__bot__.command_prefix}pause** 以暫停播放*
        ''')
    async def SeekFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | SE01**
            無法跳轉歌曲，請確認您輸入的跳轉時間有效
            或目前是否有歌曲播放，亦或候播清單是否為空
            請以秒數格式(ex. 70)或時間戳格式(ex. 01:10)執行指令
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.__bot__.command_prefix}volume** 來調整音量*
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
            if not issearch: await ctx.send(mes, embed=self.__SongInfo__(color="green", playlist=playlist, index=index))
            else: await searchmes.edit(content=mes, embed=self.__SongInfo__(color="green", playlist=playlist, index=index))
        else: 
            if issearch: await searchmes.delete()
    def __QueueEmbed__(self, playlist: Playlist, page: int=1) -> disnake.Embed:
        embed = disnake.Embed(title=":information_source: | 候播清單", description=f"以下清單為歌曲候播列表，目前為第 {page+1} 頁", colour=0xF2F3EE)
        for i in range(1, 4):
            index = page*3+i
            if (index == len(playlist)): break
            length = sec_to_hms(self, playlist[index].length, "symbol")
            embed.add_field(
                name="第 {} 順位\n{}\n{}{} 點歌".format(index, playlist[index].title, "🔴 直播 | " if playlist[index].is_stream else "", playlist[index].requester),
                value=f"作者: {playlist[index].author} / 歌曲時長: {length}",
                inline=False,
            )
        return embed
    async def ShowQueue(self, ctx: commands.Context, playlist: Playlist) -> None:
        class Button(disnake.ui.Button):
            def __init__(self, mode, playlist: Playlist, QueueEmbed, embed_opt):
                self.mode = mode
                self.playlist: Playlist = playlist
                self.queueembed = QueueEmbed
                self.embed_opt = embed_opt
                super().__init__(style=disnake.ButtonStyle.blurple)
                if self.mode == 'backward': self.label = '⬅️'; self.disabled = True
                if self.mode == 'forward': self.label = '➡️'
                if self.mode == 'done': self.label = '❎'

            async def callback(self, interaction: disnake.Interaction):
                # view.children[0] = 上一頁; view.children[1] = 下一頁
                view = self.view
                if self.mode == 'backward':
                    view.page -= 1
                    if view.page == 0: view.children[0].disabled = True
                    if view.page != (len(self.playlist)-1)//3: view.children[1].disabled = False
                if self.mode == 'forward':
                    view.page += 1
                    if view.page == (len(self.playlist)-1)//3: view.children[1].disabled = True
                    if view.page != 0: view.children[0].disabled = False
                if self.mode == 'done': view.clear_items()
                embed = self.queueembed(self.playlist, view.page)
                embed = disnake.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)
                if self.mode == 'done': 
                    editedmes = await interaction.original_message()
                    await editedmes.add_reaction('✅')
        class QueuePage(disnake.ui.View):
            def __init__(self, playlist: Playlist, QueueEmbed, embed_opt, *, timeout=300):
                self.page = 0
                super().__init__(timeout=timeout)
                self.leftbutton = self.add_item(Button('backward', playlist, QueueEmbed, embed_opt))
                self.rightbutton = self.add_item(Button('forward', playlist, QueueEmbed, embed_opt))
                self.donebutton = self.add_item(Button('done', playlist, QueueEmbed, embed_opt))
            def set_mes(self, mes):
                self.mes: disnake.Message = mes
            async def on_timeout(self):
                self.clear_items()
                await self.mes.edit(view=view)
        if (len(playlist) < 2):
            await ctx.send(f'''
            **:information_source: | 待播歌曲**
            目前沒有任何歌曲待播中
            *輸入 ** '{self.__bot__.command_prefix}play 關鍵字或網址' **可繼續點歌*
            ''')
            return
        embed = self.__QueueEmbed__(playlist, 0)
        embed = disnake.Embed.from_dict(dict(**embed.to_dict(), **self.__embed_opt__))
        if not (len(playlist)) <= 4:
            view = QueuePage(playlist, self.__QueueEmbed__, self.__embed_opt__)
            mes = await ctx.send(embed=embed, view=view)
            view.set_mes(mes)
        else:
            await ctx.send(embed=embed)
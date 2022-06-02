from typing import *
import disnake
from disnake.ext import commands
import datetime
import copy

from pytube import exceptions as PytubeExceptions
from yt_dlp import utils as YTDLPExceptions

# Just for fetching current year
cdt = datetime.datetime.now().date()
year = cdt.strftime("%Y")

def _sec_to_hms(seconds, format) -> str:
    sec = int(seconds%60); min = int(seconds//60%60); hr = int(seconds//60//60%24); day = int(seconds//86400)
    if format == "symbol":
        if day != 0:
            return "{}{}:{}{}:{}{}:{}{}".format("0" if day < 10 else "", day, "0" if hr < 10 else "", hr, "0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
        if hr != 0:
            return "{}{}:{}{}:{}{}".format("0" if hr < 10 else "", hr, "0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
        else:
            return "{}{}:{}{}".format("0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
    elif format == "zh":
        if day != 0:
            return f"{day} 天 {hr} 小時 {min} 分 {sec} 秒"
        elif hr != 0: 
            return f"{hr} 小時 {min} 分 {sec} 秒"
        elif min != 0:
            return f"{min} 分 {sec} 秒"
        elif sec != 0:
            return f"{sec} 秒"

from .player import MusicBot, Player
from .playlist import Playlist, LoopState, PlaylistBase

class GuildUIInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.auto_stage_available: bool = True
        self.skip: bool = False
        self.mute: bool = False
        self.search: bool = False
        self.searchmsg: disnake.Message = None
        self.playinfo: Coroutine[Any, Any, disnake.Message] = None

class UI:
    def __init__(self, musicbot, bot_version):
        self.__bot_version__: str = bot_version

        self.musicbot: MusicBot = musicbot
        self.bot: commands.Bot = musicbot.bot
        self._guild_ui_info = dict()

        self.__embed_opt__: dict = {
            'footer': {
                'text': f"{self.bot.user.name} | 版本: {self.__bot_version__}\nCopyright @ {year} TK Entertainment",
                'icon_url': "https://i.imgur.com/wApgX8J.png"
            },
        }

    def __getitem__(self, guild_id) -> GuildUIInfo:
        if self._guild_ui_info.get(guild_id) is None:
            self._guild_ui_info[guild_id] = GuildUIInfo(guild_id)
        return self._guild_ui_info[guild_id]

    def auto_stage_available(self, guild_id: int):
        return self[guild_id].auto_stage_available
    ########
    # Help #
    ########
    def _HelpEmbedBasic(self) -> disnake.Embed:
        return disnake.Embed(title=":regional_indicator_q: | 指令說明 | 基本指令", description=f'''
        {self.bot.command_prefix}help | 顯示此提示框，列出指令說明
        {self.bot.command_prefix}join | 將機器人加入到您目前所在的語音頻道
        {self.bot.command_prefix}leave | 使機器人離開其所在的語音頻道
        ''', colour=0xF2F3EE)
    def _HelpEmbedPlayback(self) -> disnake.Embed:
        return disnake.Embed(title=":regional_indicator_q: | 指令說明 | 播放相關指令", description=f'''
        {self.bot.command_prefix}play [URL/名稱] | 開始播放指定歌曲(輸入名稱會啟動搜尋)
        {self.bot.command_prefix}pause | 暫停歌曲播放
        {self.bot.command_prefix}resume | 續播歌曲
        {self.bot.command_prefix}skip | 跳過目前歌曲
        {self.bot.command_prefix}stop | 停止歌曲並清除所有隊列
        {self.bot.command_prefix}mute | 切換靜音狀態
        {self.bot.command_prefix}volume [音量] | 顯示機器人目前音量/更改音量(加上指定 [音量])
        {self.bot.command_prefix}seek [秒/時間戳] | 快轉至指定時間 (時間戳格式 ex.00:04)
        {self.bot.command_prefix}restart | 重新播放目前歌曲
        {self.bot.command_prefix}loop | 切換單曲循環開關
        {self.bot.command_prefix}wholeloop | 切換全隊列循環開關
        ''', colour=0xF2F3EE)
    def _HelpEmbedQueue(self) -> disnake.Embed:
        return disnake.Embed(title=":regional_indicator_q: | 指令說明 | 隊列相關指令", description=f'''
        {self.bot.command_prefix}queue | 顯示待播歌曲列表
        {self.bot.command_prefix}remove [順位數] | 移除指定待播歌曲
        {self.bot.command_prefix}swap [順位數1] [順位數2] | 交換指定待播歌曲順序
        {self.bot.command_prefix}move [原順位數] [目標順位數] | 移動指定待播歌曲至指定順序
        ''', colour=0xF2F3EE)
    
    async def Help(self, ctx: commands.Context) -> None:

        class Help(disnake.ui.View):

            HelpEmbedBasic = self._HelpEmbedBasic
            HelpEmbedPlayback = self._HelpEmbedPlayback
            HelpEmbedQueue = self._HelpEmbedQueue
            embed_opt = self.__embed_opt__

            def __init__(self, *, timeout=60):
                super().__init__(timeout=timeout)
                self.last: disnake.ui.Button = self.children[0]

            def toggle(self, button: disnake.ui.Button):
                self.last.disabled = False
                self.last.style = disnake.ButtonStyle.blurple
                button.disabled = True
                button.style = disnake.ButtonStyle.gray
                self.last = button

            @disnake.ui.button(label='基本指令', style=disnake.ButtonStyle.gray, disabled=True)
            async def basic(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                self.toggle(button)
                embed = self.HelpEmbedBasic()
                embed = disnake.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)
            
            @disnake.ui.button(label='播放相關', style=disnake.ButtonStyle.blurple)
            async def playback(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                self.toggle(button)
                embed = self.HelpEmbedPlayback()
                embed = disnake.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)

            @disnake.ui.button(label='隊列相關', style=disnake.ButtonStyle.blurple)
            async def queue(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                self.toggle(button)
                embed = self.HelpEmbedQueue()
                embed = disnake.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)

            @disnake.ui.button(label='❎', style=disnake.ButtonStyle.danger)
            async def done(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                self.clear_items()
                await interaction.response.edit_message(embed=embed, view=view)
                original_message = await interaction.original_message()
                await original_message.add_reaction('✅')
                self.stop()

            async def on_timeout(self):
                self.clear_items()
                await msg.edit(view=self)
                await msg.add_reaction('🛑')

        embed = self._HelpEmbedBasic()
        embed = disnake.Embed.from_dict(dict(**embed.to_dict(), **self.__embed_opt__))
        view = Help()
        msg = await ctx.send(embed=embed, view=view)
        
    ########
    # Join #
    ########
    async def RejoinNormal(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
        **:inbox_tray: | 已更換語音頻道**
        已更換至 {ctx.author.voice.channel.name} 語音頻道
            ''')
    
    async def JoinNormal(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:inbox_tray: | 已加入語音頻道**
            已成功加入 {ctx.author.voice.channel.name} 語音頻道
                ''')
    
    async def JoinStage(self, ctx: commands.Context, guild_id: int) -> None:
        botitself: disnake.Member = await ctx.guild.fetch_member(self.bot.user.id)
        if botitself not in ctx.author.voice.channel.moderators and self[guild_id].auto_stage_available == True:
            if not botitself.guild_permissions.manage_channels or not botitself.guild_permissions.administrator:
                await ctx.send(f'''
            **:inbox_tray: | 已加入舞台頻道**
            已成功加入 {ctx.author.voice.channel.name} 舞台頻道
            -----------
            *已偵測到此機器人沒有* `管理頻道` *或* `管理員` *權限*
            *亦非該語音頻道之* `舞台版主`*，自動化舞台音樂播放功能將受到限制*
            *請啟用以上兩點其中一種權限(建議啟用 `舞台版主` 即可)以獲得最佳體驗*
            *此警告僅會出現一次*
                    ''')
                self[guild_id].auto_stage_available = False
                return
            else:
                self[guild_id].auto_stage_available = True
                await ctx.send(f'''
            **:inbox_tray: | 已加入舞台頻道**
            已成功加入 {ctx.author.voice.channel.name} 舞台頻道
                ''')
                return
        else:
            await ctx.send(f'''
            **:inbox_tray: | 已加入舞台頻道**
            已成功加入 {ctx.author.voice.channel.name} 舞台頻道
                ''')
            self[guild_id].auto_stage_available = True
            return
    
    async def JoinAlready(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:hushed: | 我已經加入頻道囉**
            不需要再把我加入同一個頻道囉
            *若要更換頻道
            輸入 **{self.bot.command_prefix}leave** 以離開原有頻道
            然後使用 **{self.bot.command_prefix}join 加入新的頻道***
                ''')
        return
    
    async def JoinFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | JOINFAIL**
            請確認您是否已加入一個語音頻道
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}join** 來把我加入頻道*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
        return
    
    #########
    # Stage #
    #########
    async def CreateStageInstance(self, ctx: commands.Context, guild_id: int) -> None:
        if isinstance(ctx.author.voice.channel.instance, disnake.StageInstance) or self[guild_id].auto_stage_available == False:
            return
        channel: disnake.StageChannel = ctx.author.voice.channel
        await channel.create_instance(topic='🕓 目前無歌曲播放 | 等待指令')
    
    async def EndStage(self, guild_id: int) -> None:
        if not self[guild_id].auto_stage_available: 
            return
        if not isinstance(self.bot.get_guild(guild_id).voice_client.channel.instance, disnake.StageInstance):
            return
        instance: disnake.StageInstance = self.bot.get_guild(guild_id).voice_client.channel.instance
        await instance.delete()
    
    async def _UpdateStageTopic(self, guild_id: int, mode: str='update') -> None:
        playlist = self.musicbot._playlist[guild_id]
        if self[guild_id].auto_stage_available == False \
            or isinstance(self.bot.get_guild(guild_id).voice_client.channel, disnake.VoiceChannel):
            return
        instance: disnake.StageInstance = self.bot.get_guild(guild_id).voice_client.channel.instance
        if mode == "done":
            await instance.edit(topic='🕓 目前無歌曲播放 | 等待指令')
        elif mode == "pause":
                await instance.edit(topic='⏸️{} {}{} / {} 點歌'.format(
                    "|🔴" if playlist[0].info['stream'] else "",
                    playlist[0].info['title'][:30] if len(playlist[0].info['title']) >= 30 else playlist[0].info['title'],
                    "..." if len(playlist[0].info['title']) >= 30 else "",
                    playlist[0].requester))
        else:
            await instance.edit(topic='▶️{} {}{} / {} 點歌'.format(
                    "|🔴" if playlist[0].info['stream'] else "",
                    playlist[0].info['title'][:30] if len(playlist[0].info['title']) >= 30 else playlist[0].info['title'],
                    "..." if len(playlist[0].info['title']) >= 30 else "",
                    playlist[0].requester))

    #########
    # Leave #
    #########
    async def LeaveSucceed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:outbox_tray: | 已離開語音/舞台頻道**
            已停止所有音樂並離開目前所在的語音/舞台頻道
            ''')
    
    async def LeaveOnTimeout(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:outbox_tray: | 等待超時**
            機器人已閒置超過 10 分鐘
            已停止所有音樂並離開目前所在的語音/舞台頻道
            ''')
    
    async def LeaveFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | LEAVEFAIL**
            請確認您是否已加入一個語音/舞台頻道，或機器人並不在頻道中
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}leave** 來讓我離開頻道*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    
    ##########
    # Search #
    ##########
    async def StartSearch(self, ctx: commands.Context, url: str) -> disnake.Message:
        if ("http" not in url) and ("www" not in url):
            self[ctx.guild.id].searchmsg =  await ctx.send(f'''
            **:mag_right: | 開始搜尋 | {url}**
            請稍候... 機器人已開始搜尋歌曲，若搜尋成功即會顯示歌曲資訊並開始自動播放
            ''')
            self[ctx.guild.id].search = True
        else: self[ctx.guild.id].search = False

    async def SearchFailed(self, ctx: commands.Context, url: str, exception: Union[YTDLPExceptions.DownloadError, Exception]) -> None:
        if isinstance(exception, PytubeExceptions.VideoPrivate) \
                or (isinstance(exception, YTDLPExceptions.DownloadError) and "Private Video" in exception.msg):
            reason = ['VIDPRIVATE', '私人影片']
        elif isinstance(exception, PytubeExceptions.MembersOnly):
            await self.ui.SearchFailed(ctx, url, 'MembersOnly')
            reason = ['FORMEMBERS', '會員限定影片']
        else:
            reason = ['UNAVAILIBLE', '無法存取的影片']
        await ctx.send(f'''
            **:no_entry: | 失敗 | {reason[0]}**
            您所指定的音樂 {url}
            為 **{reason[1]}**，機器人無法存取
            請更換其他音樂播放
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}play** 來播放音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')

    ########
    # Info #
    ########
    def _SongInfo(self, guild_id: int, color_code: str = None, index: int = 0):
        playlist = self.musicbot._playlist[guild_id]
        song = playlist[index]

        if color_code == "green": # Green means adding to queue
            color = disnake.Colour.from_rgb(97, 219, 83)
        elif color_code == "red": # Red means deleted
            color = disnake.Colour.from_rgb(255, 0, 0)
        else: 
            color = disnake.Colour.from_rgb(255, 255, 255)

        # Generate Loop Icon
        if color_code != "red" and playlist.loop_state != LoopState.NOTHING:
            loopstate: LoopState = playlist.loop_state
            loopicon = ''
            if loopstate == LoopState.SINGLE:
                loopicon = f' | 🔂 🕗 {playlist.times} 次'
            elif loopstate == LoopState.SINGLEINF:
                loopicon = ' | 🔂'
            elif loopstate == LoopState.PLAYLIST:
                loopicon = ' | 🔁'
        else:
            loopstate = None
            loopicon = ''

        # Generate Embed Body
        embed = disnake.Embed(title=song.info['title'], url=song.info['watch_url'], colour=color)
        embed.add_field(name="作者", value=f"[{song.info['author']}]({song.info['channel_url']})", inline=True)
        embed.set_author(name=f"這首歌由 {song.requester.name}#{song.requester.tag} 點歌", icon_url=song.requester.display_avatar)
        
        if song.info['stream']: 
            embed._author['name'] += " | 🔴 直播"
            if color_code == None: 
               embed.add_field(name="結束播放", value=f"輸入 ⏩ {self.bot.command_prefix}skip / ⏹️ {self.bot.command_prefix}stop\n來結束播放此直播", inline=True)
        else: 
            embed.add_field(name="歌曲時長", value=_sec_to_hms(song.info['length'], "zh"), inline=True)
        
        if self.musicbot[guild_id]._volume_level == 0: 
            embed._author['name'] += " | 🔇 靜音"
        
        if loopstate != LoopState.NOTHING: 
            embed._author['name'] += f"{loopicon}"
        
        
        if len(playlist.order) > 1 and color_code != 'red':
            queuelist: str = ""
            queuelist += f"1." + playlist[1].info['title'] + "\n"
            if len(playlist.order) > 2: 
                queuelist += f"...還有 {len(playlist.order)-2} 首歌"
        
            embed.add_field(name=f"待播清單 | {len(playlist.order)-1} 首歌待播中", value=queuelist, inline=False)
        embed.set_thumbnail(url=song.info['thumbnail_url'])
        embed = disnake.Embed.from_dict(dict(**embed.to_dict(), **self.__embed_opt__))
        return embed

    async def _UpdateSongInfo(self, guild_id: int):
        message = f'''
            **:arrow_forward: | 正在播放以下歌曲**
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*'''
        if not self[guild_id].auto_stage_available:
            message += '\n            *可能需要手動對機器人*` 邀請發言` *才能正常播放歌曲*'
        await self[guild_id].playinfo.edit(content=message, embed=self._SongInfo(guild_id))
    
    ########
    # Play #
    ########
    async def PlayingMsg(self, channel: disnake.TextChannel):
        playlist = self.musicbot._playlist[channel.guild.id]
        if self[channel.guild.id].skip:
            if len(playlist.order) > 1:
                msg = f'''
            **:fast_forward: | 跳過歌曲**
            目前歌曲已成功跳過，即將播放下一首歌曲，資訊如下所示
            *輸入 **{self.bot.command_prefix}play** 以加入新歌曲*
                '''
            else:
                msg = f'''
            **:fast_forward: | 跳過歌曲**
            目前歌曲已成功跳過，候播清單已無歌曲
            即將播放最後一首歌曲，資訊如下所示
            *輸入 **{self.bot.command_prefix}play** 以加入新歌曲*
                '''
            self[channel.guild.id].skip = False
            if playlist.loop_state != LoopState.SINGLEINF:
                playlist.loop_state = LoopState.NOTHING
                playlist.times = 0
        else:
            msg = f'''
            **:arrow_forward: | 正在播放以下歌曲**
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*'''
        if not self[channel.guild.id].auto_stage_available:
            msg += '\n            *可能需要手動對機器人*` 邀請發言` *才能正常播放歌曲*'
        self[channel.guild.id].playinfo = await channel.send(msg, embed=self._SongInfo(guild_id=channel.guild.id))
        try: 
            await self._UpdateStageTopic(channel.guild.id)
        except: 
            pass
    
    async def DonePlaying(self, channel: disnake.TextChannel) -> None:
        await channel.send(f'''
            **:clock4: | 播放完畢，等待播放動作**
            候播清單已全數播放完畢，等待使用者送出播放指令
            *輸入 **{self.bot.command_prefix}play [URL/歌曲名稱]** 即可播放/搜尋*
        ''')
        try: 
            await self._UpdateStageTopic(channel.guild.id, 'done')
        except: 
            pass
    #########
    # Pause #
    ######### 
    async def PauseSucceed(self, ctx: commands.Context, guild_id: int) -> None:
        await ctx.send(f'''
            **:pause_button: | 暫停歌曲**
            歌曲已暫停播放
            *輸入 **{self.bot.command_prefix}resume** 以繼續播放*
            ''')
        try: 
            await self._UpdateStageTopic(guild_id, 'pause')
        except: 
            pass
    
    async def PauseOnAllMemberLeave(self, channel: disnake.TextChannel, guild_id: int) -> None:
        await channel.send(f'''
            **:pause_button: | 暫停歌曲**
            所有人皆已退出語音頻道，歌曲已暫停播放
            *輸入 **{self.bot.command_prefix}resume** 以繼續播放*
            ''')
        try: 
            await self._UpdateStageTopic(guild_id, 'pause')
        except: 
            pass
    
    async def PauseFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | PL01**
            請確認目前有歌曲正在播放，或是當前歌曲並非處於暫停狀態，亦或是候播清單是否為空
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}pause** 來暫停音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    
    ##########
    # Resume #
    ##########
    async def ResumeSucceed(self, ctx: commands.Context, guild_id: int) -> None:
        await ctx.send(f'''
            **:arrow_forward: | 續播歌曲**
            歌曲已繼續播放
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
            ''')
        try: 
            await self._UpdateStageTopic(guild_id, 'resume')
        except: 
            pass
    
    async def ResumeFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | PL02**
            請確認目前有處於暫停狀態的歌曲，或是候播清單是否為空
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}resume** 來續播音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    
    ########
    # Skip #
    ########
    def SkipProceed(self, guild_id: int):
        self[guild_id].skip = True

    async def SkipFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | SK01**
            無法跳過歌曲，請確認目前候播清單是否為空
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}skip 來跳過音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    
    ########
    # Stop #
    ########
    async def StopSucceed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:stop_button: | 停止播放**
            歌曲已停止播放
            *輸入 **{self.bot.command_prefix}play** 以重新開始播放*
            ''')
    
    async def StopFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | ST01**
            無法停止播放歌曲，請確認目前是否有歌曲播放，或候播清單是否為空
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}stop 來停止播放音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    
    ##########
    # Volume #
    ##########
    async def VolumeAdjust(self, ctx: commands.Context, percent: Union[float, str]):
        # If percent = None, show current volume
        if percent == None: 
            await ctx.send(f'''
            **:loud_sound: | 音量調整**
            目前音量為 {self.musicbot[ctx.guild.id].volume_level*100}%
        ''')

        # Volume unchanged
        if (percent / 100) == self.musicbot[ctx.guild.id].volume_level:
            await ctx.send(f'''
            **:loud_sound: | 音量調整**
            音量沒有變更，仍為 {percent}%
        ''')

        # Volume up
        elif (percent / 100) > self.musicbot[ctx.guild.id].volume_level:
            await ctx.send(f'''
            **:loud_sound: | 調高音量**
            音量已設定為 {percent}%
        ''')
            self[ctx.guild.id].mute = False
        # Volume down
        elif (percent / 100) < self.musicbot[ctx.guild.id].volume_level:
            await ctx.send(f'''
            **:sound: | 降低音量**
            音量已設定為 {percent}%
        ''')
            self[ctx.guild.id].mute = False
        await self._UpdateSongInfo(ctx.guild.id)
    
    async def MuteorUnMute(self, ctx: commands.Context, percent: Union[float, str]) -> bool:
        mute = self[ctx.guild.id].mute
        if mute and percent == 100:
            await ctx.send(f'''
            **:speaker: | 解除靜音**
            音量已設定為 100%，目前已解除靜音模式
        ''')
            self[ctx.guild.id].mute = False
        elif percent == 0: 
            await ctx.send(f'''
            **:mute: | 靜音**
            音量已設定為 0%，目前處於靜音模式
        ''')
            self[ctx.guild.id].mute = True
        await self._UpdateSongInfo(ctx.guild.id, mute)

    async def VolumeAdjustFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | SA01**
            無法調整音量，請確認您輸入的音量百分比是否有效
            請以百分比格式(ex. 100%)執行指令
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}volume** 來調整音量*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    ########
    # Seek #
    ########
    def __ProgressBar(self, timestamp: int, duration: int, amount: int=15) -> str:
        bar = ''
        persent = timestamp / duration
        bar += "**"
        for i in range(round(persent*amount)):
            bar += '⎯'
        bar += "⬤"
        for i in range(round(persent*amount)+1, amount+1):
            bar += '⎯'
        bar += "**"
        return bar
    
    async def SeekSucceed(self, ctx: commands.Context, timestamp: int) -> None:
        playlist = self.musicbot._playlist[ctx.guild.id]
        seektime = _sec_to_hms(self, timestamp, "symbol"); duration = _sec_to_hms(self, playlist[ctx.guild.id].info['length'], "symbol")
        bar = self.__ProgressBar(timestamp, playlist[ctx.guild.id].info['length'])
        await ctx.send(f'''
            **:timer: | 跳轉歌曲**
            已成功跳轉至指定時間
            **{seektime}** {bar} **{duration}**
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
        ''')
    
    async def SeekFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | SE01**
            無法跳轉歌曲，請確認您輸入的跳轉時間有效
            或目前是否有歌曲播放，亦或候播清單是否為空
            請以秒數格式(ex. 70)或時間戳格式(ex. 01:10)執行指令
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}seek** 來跳轉音樂*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    
    ##########
    # Replay #
    ##########
    async def ReplaySucceed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:repeat: | 重播歌曲**
            歌曲已重新開始播放
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
            ''')
    
    async def ReplayFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | RP01**
            無法重播歌曲，請確認目前是否有歌曲播放
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}replay** 來重播歌曲*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    
    ########
    # Loop #
    ########
    async def LoopSucceed(self, ctx: commands.Context) -> None:
        playlist = self.musicbot._playlist[ctx.guild.id]
        if playlist.loop_state == LoopState.SINGLEINF:
            await ctx.send(f'''
            **:repeat_one: | 單曲重複播放**
            已啟動單曲重複播放
            ''')
        elif playlist.loop_state == LoopState.SINGLE:
            await ctx.send(f'''
            **:repeat_one: | 單曲重複播放**
            已啟動單曲重播，將重複播放 {playlist.times} 次後關閉單曲重播
            ''')
        elif playlist.loop_state == LoopState.PLAYLIST:
            await ctx.send(f'''
            **:repeat: | 全佇列重複播放**
            已啟動全佇列重複播放
            ''')
        else:
            await ctx.send(f'''
            **:arrow_forward: | 關閉重複播放**
            已關閉重複播放功能
            ''')
        await self._UpdateSongInfo(ctx.guild.id)
    
    async def SingleLoopFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | LP01**
            無法啟動重複播放功能，請確認您輸入的重複次數有效
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}loop / {self.bot.command_prefix}loop [次數]** 來控制重複播放功能*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    
    #########
    # Queue #
    #########
    # Add to queue
    async def Embed_AddedToQueue(self, ctx: commands.Context) -> None:
        # If queue has more than 2 songs, then show message when
        # user use play command
        playlist: PlaylistBase = self.musicbot._playlist[ctx.guild.id]
        if len(playlist.order) > 1:
            index = len(playlist.order) - 1
            mes = f'''
            **:white_check_mark: | 成功加入隊列**
                以下歌曲已加入隊列中，為第 **{len(playlist.order)-1}** 首歌
            '''
            if not self[ctx.guild.id].search: 
                await ctx.send(mes, embed=self._SongInfo(color_code="green", index=index, guild_id=ctx.guild.id))
            else: 
                await self[ctx.guild.id].searchmsg.edit(content=mes, embed=self._SongInfo(color_code="green", index=index))
        else: 
            if self[ctx.guild.id].search: 
                await self[ctx.guild.id].searchmsg.delete()
    
    # Queue Embed Generator
    def _QueueEmbed(self, playlist: PlaylistBase, page: int=0) -> disnake.Embed:
        embed = disnake.Embed(title=":information_source: | 候播清單", description=f"以下清單為歌曲候播列表，共 {len(playlist.order)-1} 首", colour=0xF2F3EE)
        
        for i in range(1, 4):
            index = page*3+i
            if (index == len(playlist.order)): break
            length = _sec_to_hms(playlist[index].info['length'], "symbol")
            embed.add_field(
                name="第 {} 順位\n{}\n{}{} 點歌".format(index, playlist[index].info['title'], "🔴 直播 | " if playlist[index].info['stream'] else "", playlist[index].requester),
                value="作者: {}{}{}".format(playlist[index].info['author'], " / 歌曲時長: " if not playlist[index].info['stream'] else "", length if not playlist[index].info['stream'] else ""),
                inline=False,
            )

        embed_opt = copy.deepcopy(self.__embed_opt__)

        if len(playlist.order) > 4:
            total_pages = ((len(playlist.order) - 1) // 3) + 1
            embed_opt['footer']['text'] = f'第 {page+1} 頁 / 共 {total_pages} 頁\n' + self.__embed_opt__['footer']['text']
        
        embed = disnake.Embed.from_dict(dict(**embed.to_dict(), **embed_opt))
        return embed
    
    # Queue Listing
    async def ShowQueue(self, ctx: commands.Context) -> None:
        playlist: PlaylistBase = self.musicbot._playlist[ctx.guild.id]

        class QueueListing(disnake.ui.View):

            QueueEmbed = self._QueueEmbed
            embed_opt = self.__embed_opt__
            
            def __init__(self, *, timeout=60):
                super().__init__(timeout=timeout)
                self.last: disnake.ui.Button = self.children[0]
                self.page = 0

            @property
            def left_button(self) -> disnake.ui.Button:
                return self.children[0]

            @property
            def right_button(self) -> disnake.ui.Button:
                return self.children[1]

            def update_button(self):
                if self.page == 0:
                    self.left_button.disabled = True
                    self.left_button.style = disnake.ButtonStyle.gray
                else:
                    self.left_button.disabled = False
                    self.left_button.style = disnake.ButtonStyle.blurple
                if self.page == (len(playlist.order) - 2) // 3:
                    self.right_button.disabled = True
                    self.right_button.style = disnake.ButtonStyle.gray
                else:
                    self.right_button.disabled = False
                    self.right_button.style = disnake.ButtonStyle.blurple

            @disnake.ui.button(label='⬅️', style=disnake.ButtonStyle.gray, disabled=True)
            async def lastpage(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                self.page -= 1
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page)
                await interaction.response.edit_message(embed=embed, view=view)

            @disnake.ui.button(label='➡️', style=disnake.ButtonStyle.blurple)
            async def nextpage(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):            
                self.page += 1
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page)
                await interaction.response.edit_message(embed=embed, view=view)

            @disnake.ui.button(label='❎', style=disnake.ButtonStyle.danger)
            async def done(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                self.clear_items()
                await interaction.response.edit_message(embed=embed, view=view)
                original_message = await interaction.original_message()
                await original_message.add_reaction('✅')
                self.stop()
        
            async def on_timeout(self):
                self.clear_items()
                await msg.edit(view=view)
                await msg.add_reaction('🛑')
            
        if (len(playlist.order) < 2):
            await ctx.send(f'''
            **:information_source: | 待播歌曲**
            目前沒有任何歌曲待播中
            *輸入 ** '{self.bot.command_prefix}play 關鍵字或網址' **可繼續點歌*
            ''')
            return
        else:
            embed = self._QueueEmbed(playlist, 0)
            if not (len(playlist.order)) <= 4:
                view = QueueListing()
                msg = await ctx.send(embed=embed, view=view)
            else:
                await ctx.send(embed=embed)
    
    # Remove an entity from queue
    async def RemoveSucceed(self, ctx: commands.Context, idx: int) -> None:
        await ctx.send(f'''
            **:wastebasket: | 已刪除指定歌曲**
            已刪除 **第 {idx} 順位** 的歌曲，詳細資料如下
            ''', embed=self._SongInfo(ctx.guild.id, 'red', idx))
    
    async def RemoveFailed(self, ctx: commands.Context):
        await ctx.send(f'''
            **:no_entry: | 失敗 | RM01**
            無法刪除指定歌曲，請確認您輸入的順位數有效
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}remove [順位數]** 來刪除待播歌曲*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    
    # Swap entities in queue
    async def Embed_SwapSucceed(self, ctx: commands.Context, idx1: int, idx2: int) -> None:
        playlist = self.musicbot._playlist[ctx.guild.id]
        embed = disnake.Embed(title=":arrows_counterclockwise: | 調換歌曲順序", description="已調換歌曲順序，以下為詳細資料", colour=0xF2F3EE)
        
        embed.add_field(name=f"第 ~~{idx2}~~ -> **{idx1}** 順序", value='{}\n{}\n{} 點歌\n'
            .format(
                playlist[idx1].info['title'],
                playlist[idx1].info['author'],
                playlist[idx1].requester
            ), inline=True)
        
        embed.add_field(name=f"第 ~~{idx1}~~ -> **{idx2}** 順序", value='{}\n{}\n{} 點歌\n'
            .format(
                playlist[idx2].info['title'],
                playlist[idx2].info['author'],
                playlist[idx2].requester
            ), inline=True)

        await ctx.send(embed=embed)

    async def SwapFailed(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | SW01**
            無法交換指定歌曲，請確認您輸入的順位數有效
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}swap [順位數1] [順位數2]** 來交換待播歌曲*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
    
    # Move entity to other place in queue
    async def MoveToSucceed(self, ctx: commands.Context, origin: int, new: int) -> None:
        playlist = self.musicbot._playlist[ctx.guild.id]
        embed = disnake.Embed(title=":arrows_counterclockwise: | 移動歌曲順序", description="已移動歌曲順序，以下為詳細資料", colour=0xF2F3EE)
        
        embed.add_field(name=f"第 ~~{origin}~~ -> **{new}** 順序", value='{}\n{}\n{} 點歌\n'
            .format(
                playlist[new].info['title'],
                playlist[new].info['author'],
                playlist[new].requester
            ), inline=True)
        
        await ctx.send(embed=embed)

    async def MoveToFailed(self, ctx) -> None:
        await ctx.send(f'''
            **:no_entry: | 失敗 | MT01**
            無法移動指定歌曲，請確認您輸入的目標順位數有效
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}move [原順位數] [目標順位數]** 來移動待播歌曲*
            *若您覺得有Bug或錯誤，請參照上方代碼回報至 Github*
            ''')
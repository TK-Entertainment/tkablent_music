from typing import *
import discord
from discord.ext import commands
import datetime
import copy

from .player import Command

from pytube import exceptions as PytubeExceptions
from yt_dlp import utils as YTDLPExceptions
import wavelink

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
from .github import GithubIssue

class GuildUIInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.auto_stage_available: bool = True
        self.skip: bool = False
        self.mute: bool = False
        self.search: bool = False
        self.lasterrorinfo: dict = {}
        self.playinfo: Coroutine[Any, Any, discord.Message] = None

class UI:
    def __init__(self, musicbot, bot_version):
        self.__bot_version__: str = bot_version

        self.musicbot: MusicBot = musicbot
        self.bot: commands.Bot = musicbot.bot
        self.github: GithubIssue = GithubIssue()
        self._guild_ui_info = dict()

        self.music_errorcode_to_msg = {
            "VIDPRIVATE": "私人影片",
            "FORMEMBERS": "會員限定影片",
            "NOTSTARTED": "尚未開始的直播",
            "UNAVAILIBLE": "無法存取的影片",
            "PLAYER_FAULT": "機器人遇到了一些問題，故無法正常播放\n            將跳過此歌曲"
        }

        self.errorcode_to_msg = {
            "JOINFAIL": ["請確認您是否已加入一個語音頻道", "join", "來把我加入頻道"],
            "LEAVEFAIL": ["請確認您是否已加入一個語音/舞台頻道，或機器人並不在頻道中", "leave", "來讓我離開頻道"],
            "PAUSEFAIL": ["無法暫停音樂，請確認目前有歌曲正在播放，或是當前歌曲並非處於暫停狀態，亦或是候播清單是否為空", "pause", "來暫停音樂"],
            "RESUMEFAIL": ["無法續播音樂，請確認目前有處於暫停狀態的歌曲，或是候播清單是否為空", "resume", "來續播音樂"],
            "SKIPFAIL": ["無法跳過歌曲，請確認目前候播清單是否為空", "skip", "來跳過音樂"],
            "STOPFAIL": ["無法停止播放歌曲，請確認目前是否有歌曲播放，或候播清單是否為空", "stop", "來停止播放音樂"],
            "VOLUMEADJUSTFAIL": ["無法調整音量，請確認目前機器人有在語音頻道中\n            或是您輸入的音量百分比是否有效\n            請以百分比格式(ex. 100%)執行指令", "volume", "來調整音量"],
            "SEEKFAIL": ["無法跳轉歌曲，請確認您輸入的跳轉時間有效\n            或目前是否有歌曲播放，亦或候播清單是否為空\n            請以秒數格式(ex. 70)或時間戳格式(ex. 01:10)執行指令", "seek", "來跳轉音樂"],
            "REPLAYFAIL": ["無法重播歌曲，請確認目前是否有歌曲播放", "replay", "來重播歌曲"],
            "LOOPFAIL_SIG": ["無法啟動重複播放功能，請確認您輸入的重複次數有效", f"loop / {self.bot.command_prefix}loop [次數]", "來控制重複播放功能"],
            "REMOVEFAIL": ["無法刪除指定歌曲，請確認您輸入的順位數有效", "remove [順位數]", "來刪除待播歌曲"],
            "SWAPFAIL": ["無法交換指定歌曲，請確認您輸入的順位數有效", "swap [順位數1] [順位數2]", "來交換待播歌曲"],
            "MOVEFAIL": ["無法移動指定歌曲，請確認您輸入的目標順位數有效", "move [原順位數] [目標順位數]", "來移動待播歌曲"],
        }

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

    ############################
    # General Warning Messages #
    ############################
    async def _MusicExceptionHandler(self, message, errorcode: str, trackinfo: wavelink.YouTubeTrack=None, exception=None):
        if 'PLAY' not in errorcode:
            part_content = f'''
            **:no_entry: | 失敗 | {errorcode}**
            您所指定的音樂 {trackinfo.uri}
            為 **{self.music_errorcode_to_msg[errorcode]}**，機器人無法存取
            請更換其他音樂播放
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}play** 來把我加入頻道*'''
        else:
            if errorcode == "PLAYER_FAULT":
                part_content = f'''
            **:warning: | 警告 | {errorcode}**
            {self.music_errorcode_to_msg[errorcode]}
            --------
            技術資訊:
            {exception}
            --------
            *此錯誤不會影響到播放，僅為提醒訊息*'''
            else:
                part_content = f'''
            **:warning: | 警告 | {errorcode}**
            您所指定的播放清單中之歌曲或單一歌曲(如下面所示)
            為 **{self.music_errorcode_to_msg[errorcode[5:]]}**，機器人無法存取
            將直接跳過此曲目
            --------
            *此錯誤不會影響到播放，僅為提醒訊息*'''
            url = self.musicbot._playlist[message.guild.id].current().info['watch_url']

        done_content = part_content

        content = f'''
            {part_content}
            *若您覺得有Bug或錯誤，請輸入 /reportbug 來回報錯誤*
        '''

        await self._BugReportingMsg(message, content, done_content, errorcode, exception, url)

    async def _CommonExceptionHandler(self, message: Command , errorcode: str, exception=None):
        done_content = f'''
            **:no_entry: | 失敗 | {errorcode}**
            {self.errorcode_to_msg[errorcode][0]}
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}{self.errorcode_to_msg[errorcode][1]}** {self.errorcode_to_msg[errorcode][2]}*
        '''

        content = f'''
            **:no_entry: | 失敗 | {errorcode}**
            {self.errorcode_to_msg[errorcode][0]}
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}{self.errorcode_to_msg[errorcode][1]}** {self.errorcode_to_msg[errorcode][2]}*
            *若您覺得有Bug或錯誤，請輸入 /reportbug 來回報錯誤*
            '''

        await self._BugReportingMsg(message, content, done_content, errorcode, exception)
        
    async def _BugReportingMsg(self, message: Union[Command, discord.TextChannel], content, done_content, errorcode, exception=None, video_url=None):
        cdt = datetime.datetime.now()
        errortime = cdt.strftime("%Y/%m/%d %H:%M:%S")

        if "PLAY" in errorcode:
            embed = self._SongInfo(guild_id=message.guild.id, color_code='red')
            msg = await message.send(content, embed=embed)
        else:
            msg = await message.send(content)

        self[message.guild.id].lasterrorinfo = {
            "errortime": errortime,
            "msg": msg,
            "done_content": done_content,
            "errorcode": errorcode,
            "exception": exception,
            "video_url": video_url
        }

    async def Interaction_BugReportingModal(self, interaction: discord.Interaction, guild: discord.Guild):

        class BugReportingModal(discord.ui.Modal):
            lasterror = self[guild.id].lasterrorinfo
            github = self.github
            guildinfo = guild
            bot = self.bot

            if "errorcode" not in lasterror.keys():
                error_code = ""
            else:
                error_code = lasterror["errorcode"]

            if "errortime" not in lasterror.keys():
                error_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            else:
                error_time = lasterror["errortime"]

            embed_opt = self.__embed_opt__

            def __init__(self):
                self.bot_name = discord.ui.TextInput(
                    custom_id="bot_name",
                    label="機器人名稱 (已自動填入，不需更改)",
                    default=f"{self.bot.user.name}#{self.bot.user.discriminator}"
                )

                self.guild = discord.ui.TextInput(
                    custom_id="guild",
                    label="伺服器名稱 (已自動填入，不需更改)",
                    default=f"{self.guildinfo.name} ({self.guildinfo.id})"
                )

                self.error_code_text = discord.ui.TextInput(
                    custom_id="error_code",
                    label="錯誤代碼 (由上一次錯誤填入，可修改)",
                    default=self.error_code
                )

                self.modaltime_text = discord.ui.TextInput(
                    custom_id="submit_time",
                    label="錯誤發生時間 (已自動填入，不需更改)",
                    default=self.error_time
                )

                self.description = discord.ui.TextInput(
                    custom_id="error_description",
                    label="請簡述錯誤是如何產生的",
                    placeholder="簡述如何重新產生該錯誤，或該錯誤是怎麼產生的。\n如果隨意填寫或更改上方資料，將可能遭到忽略",
                    style=discord.TextStyle.paragraph
                )
                super().__init__(
                    title = "🐛 | 回報蟲蟲",
                    timeout=120
                )

                for item in [
                        self.bot_name,
                        self.guild,
                        self.error_code_text,
                        self.modaltime_text,
                        self.description
                    ]:
                    self.add_item(item)


            def result_embed(self, results: dict):
                embed = discord.Embed(title="🐛 | 錯誤回報簡表 (點我到 Github Issue)", url=self.github.issue_user_url, description="")
                embed.add_field(name="錯誤代碼", value="{}".format(results["errorcode"]))
                embed.add_field(name="錯誤回報時間", value="{}".format(results["timestamp"]))
                embed.add_field(name="造成錯誤之影片連結", value="{}".format(results["video_url"]))
                embed.add_field(name="使用者回報之簡述", value="{}".format(results["description"]))
                embed.add_field(name="參考錯誤代碼", value="{}".format(results["exception"]))
                embed.add_field(name="👏 感謝你的回報", value="⠀")
                embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                return embed

            async def on_submit(self, interaction: discord.Interaction):
                if self.error_code_text.value != self.error_code:
                    exception = "無可參考之錯誤回報，或錯誤代碼被更改"
                    video_url = None
                else:
                    exception = self.lasterror["exception"]
                    video_url = self.lasterror["video_url"]
                submission = self.github.submit_bug(
                    self.bot_name.value,
                    self.guild.value,
                    self.error_code_text.value,
                    self.modaltime_text.value,
                    self.description.value,
                    exception,
                    video_url,
                )
                await interaction.response.send_message(embed=self.result_embed(submission))

            async def on_timeout(self):
                pass

        modal = BugReportingModal()
        await interaction.response.send_modal(modal)

    ########
    # Help #
    ########
    def _HelpEmbedBasic(self) -> discord.Embed:
        return discord.Embed(title=":regional_indicator_q: | 指令說明 | 基本指令", description=f'''
        {self.bot.command_prefix}help | 顯示此提示框，列出指令說明
        {self.bot.command_prefix}join | 將機器人加入到您目前所在的語音頻道
        {self.bot.command_prefix}leave | 使機器人離開其所在的語音頻道
        ''', colour=0xF2F3EE)
    def _HelpEmbedPlayback(self) -> discord.Embed:
        return discord.Embed(title=":regional_indicator_q: | 指令說明 | 播放相關指令", description=f'''
        {self.bot.command_prefix}play [URL/名稱] | 開始播放指定歌曲(輸入名稱會啟動搜尋)
        {self.bot.command_prefix}pause | 暫停歌曲播放
        {self.bot.command_prefix}resume | 續播歌曲
        {self.bot.command_prefix}skip | 跳過目前歌曲
        {self.bot.command_prefix}stop | 停止歌曲並清除所有待播清單中的歌曲
        {self.bot.command_prefix}mute | 切換靜音狀態
        {self.bot.command_prefix}volume [音量] | 顯示機器人目前音量/更改音量(加上指定 [音量])
        {self.bot.command_prefix}seek [秒/時間戳] | 快轉至指定時間 (時間戳格式 ex.00:04)
        {self.bot.command_prefix}restart | 重新播放目前歌曲
        {self.bot.command_prefix}loop | 切換單曲循環開關
        {self.bot.command_prefix}wholeloop | 切換全待播清單循環開關
        ''', colour=0xF2F3EE)
    def _HelpEmbedQueue(self) -> discord.Embed:
        return discord.Embed(title=":regional_indicator_q: | 指令說明 | 待播清單相關指令", description=f'''
        {self.bot.command_prefix}queue | 顯示待播歌曲列表
        {self.bot.command_prefix}remove [順位數] | 移除指定待播歌曲
        {self.bot.command_prefix}swap [順位數1] [順位數2] | 交換指定待播歌曲順序
        {self.bot.command_prefix}move [原順位數] [目標順位數] | 移動指定待播歌曲至指定順序
        ''', colour=0xF2F3EE)

    async def Help(self, command: Union[commands.Context, discord.Interaction]) -> None:

        class Help(discord.ui.View):

            HelpEmbedBasic = self._HelpEmbedBasic
            HelpEmbedPlayback = self._HelpEmbedPlayback
            HelpEmbedQueue = self._HelpEmbedQueue
            embed_opt = self.__embed_opt__

            def __init__(self, *, timeout=60):
                super().__init__(timeout=timeout)
                self.last: discord.ui.Button = self.children[0]

            def toggle(self, button: discord.ui.Button):
                self.last.disabled = False
                self.last.style = discord.ButtonStyle.blurple
                button.disabled = True
                button.style = discord.ButtonStyle.gray
                self.last = button

            @discord.ui.button(label='基本指令', style=discord.ButtonStyle.gray, disabled=True)
            async def basic(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.toggle(button)
                embed = self.HelpEmbedBasic()
                embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)
            
            @discord.ui.button(label='播放相關', style=discord.ButtonStyle.blurple)
            async def playback(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.toggle(button)
                embed = self.HelpEmbedPlayback()
                embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='待播清單相關', style=discord.ButtonStyle.blurple)
            async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.toggle(button)
                embed = self.HelpEmbedQueue()
                embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='❎', style=discord.ButtonStyle.danger)
            async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.__embed_opt__))
        view = Help()
        msg = await command.send(embed=embed, view=view)
        
    ########
    # Join #
    ########
    async def RejoinNormal(self, command: Command) -> None:
        await command.send(f'''
            **:inbox_tray: | 已更換語音頻道**
            已更換至 {command.author.voice.channel.name} 語音頻道
            ''')
    
    async def JoinNormal(self, command: Command) -> None:
        await command.send(f'''
            **:inbox_tray: | 已加入語音頻道**
            已成功加入 {command.author.voice.channel.name} 語音頻道
                ''')
    
    async def JoinStage(self, command: Command, guild_id: int) -> None:
        botitself: discord.Member = await command.guild.fetch_member(self.bot.user.id)
        if botitself not in command.author.voice.channel.moderators and self[guild_id].auto_stage_available == True:
            if not botitself.guild_permissions.manage_channels or not botitself.guild_permissions.administrator:
                await command.send(f'''
            **:inbox_tray: | 已加入舞台頻道**
            已成功加入 {command.author.voice.channel.name} 舞台頻道
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
                await command.send(f'''
            **:inbox_tray: | 已加入舞台頻道**
            已成功加入 {command.author.voice.channel.name} 舞台頻道
                ''')
                return
        else:
            await command.send(f'''
            **:inbox_tray: | 已加入舞台頻道**
            已成功加入 {command.author.voice.channel.name} 舞台頻道
                ''')
            self[guild_id].auto_stage_available = True
            return
    
    async def JoinAlready(self, command: Command) -> None:
        await command.send(f'''
            **:hushed: | 我已經加入頻道囉**
            不需要再把我加入同一個頻道囉
            *若要更換頻道
            輸入 **{self.bot.command_prefix}leave** 以離開原有頻道
            然後使用 **{self.bot.command_prefix}join 加入新的頻道***
                ''')
        return
    
    async def JoinFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "JOINFAIL", exception)
        return
    
    #########
    # Stage #
    #########
    async def CreateStageInstance(self, command: Command, guild_id: int) -> None:
        if isinstance(command.author.voice.channel.instance, discord.StageInstance) or self[guild_id].auto_stage_available == False:
            return
        channel: discord.StageChannel = command.author.voice.channel
        await channel.create_instance(topic='🕓 目前無歌曲播放 | 等待指令')
    
    async def EndStage(self, guild_id: int) -> None:
        if not self[guild_id].auto_stage_available: 
            return
        if not isinstance(self.bot.get_guild(guild_id).voice_client.channel.instance, discord.StageInstance):
            return
        instance: discord.StageInstance = self.bot.get_guild(guild_id).voice_client.channel.instance
        await instance.delete()
    
    async def _UpdateStageTopic(self, guild_id: int, mode: str='update') -> None:
        playlist = self.musicbot._playlist[guild_id]
        if self[guild_id].auto_stage_available == False \
            or isinstance(self.bot.get_guild(guild_id).voice_client.channel, discord.VoiceChannel):
            return
        instance: discord.StageInstance = self.bot.get_guild(guild_id).voice_client.channel.instance
        if mode == "done":
            await instance.edit(topic='🕓 目前無歌曲播放 | 等待指令')
        else:
            await instance.edit(topic='{}{} {}{}'.format(
                "⏸️" if mode == "pause" else "▶️",
                "|🔴" if playlist[0].is_stream() else "",
                playlist[0].title[:40] if len(playlist[0].title) >= 40 else playlist[0].title,
                "..." if len(playlist[0].title) >= 40 else ""))

    #########
    # Leave #
    #########
    async def LeaveSucceed(self, command: Command) -> None:
        await command.send(f'''
            **:outbox_tray: | 已離開語音/舞台頻道**
            已停止所有音樂並離開目前所在的語音/舞台頻道
            ''')
    
    async def LeaveOnTimeout(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:outbox_tray: | 等待超時**
            機器人已閒置超過 10 分鐘
            已停止所有音樂並離開目前所在的語音/舞台頻道
            ''')
    
    async def LeaveFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "LEAVEFAIL", exception)
    
    ##########
    # Search #
    ##########
    async def SearchFailed(self, command: Command, trackinfo, exception: Union[YTDLPExceptions.DownloadError, Exception]) -> None:
        print(exception)
        if isinstance(exception, PytubeExceptions.VideoPrivate) \
                or (isinstance(exception, YTDLPExceptions.DownloadError) and "Private Video" in exception.msg):
            reason = 'VIDPRIVATE'
        elif isinstance(exception, PytubeExceptions.MembersOnly) \
            or (isinstance(exception, YTDLPExceptions.DownloadError) and "members-only" in exception.msg):
            reason = 'FORMEMBERS'
        elif isinstance(exception, PytubeExceptions.LiveStreamError) \
            or (isinstance(exception, YTDLPExceptions.DownloadError) and "This live event will begin in" in exception.msg):
            reason = 'NOTSTARTED'
        else:
            reason = 'UNAVAILIBLE'

        await self._MusicExceptionHandler(command, reason, trackinfo, exception)
        

    ########
    # Info #
    ########
    def _SongInfo(self, guild_id: int, color_code: str = None, index: int = 0):
        playlist = self.musicbot._playlist[guild_id]
        song = playlist[index]

        if color_code == "green": # Green means adding to queue
            color = discord.Colour.from_rgb(97, 219, 83)
        elif color_code == "red": # Red means deleted
            color = discord.Colour.from_rgb(255, 0, 0)
        else: 
            color = discord.Colour.from_rgb(255, 255, 255)

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
        embed = discord.Embed(title=song.title, url=song.uri, colour=color)
        embed.add_field(name="作者", value=f"{song.author}", inline=True)
        embed.set_author(name=f"這首歌由 {song.requester.name}#{song.requester.discriminator} 點播", icon_url=song.requester.display_avatar)
        
        if song.is_stream(): 
            embed._author['name'] += " | 🔴 直播"
            if color_code == None: 
               embed.add_field(name="結束播放", value=f"輸入 ⏩ {self.bot.command_prefix}skip / ⏹️ {self.bot.command_prefix}stop\n來結束播放此直播", inline=True)
        else: 
            embed.add_field(name="歌曲時長", value=_sec_to_hms(song.length, "zh"), inline=True)
        
        if self.musicbot[guild_id]._volume_level == 0: 
            embed._author['name'] += " | 🔇 靜音"
        
        if loopstate != LoopState.NOTHING: 
            embed._author['name'] += f"{loopicon}"
        
        
        if len(playlist.order) > 1 and color_code != 'red':
            queuelist: str = ""
            queuelist += f"1." + playlist[1].title + "\n"
            if len(playlist.order) > 2: 
                queuelist += f"...還有 {len(playlist.order)-2} 首歌"

            embed.add_field(name=f"待播清單 | {len(playlist.order)-1} 首歌待播中", value=queuelist, inline=False)
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.__embed_opt__))
        return embed

    def _PlaylistInfo(self, playlist: wavelink.YouTubePlaylist, requester: discord.User):
        # Generate Embed Body
        color = discord.Colour.from_rgb(97, 219, 83)
        embed = discord.Embed(title=playlist.name, colour=color)
        embed.set_author(name=f"此播放清單由 {requester.name}#{requester.discriminator} 點播", icon_url=requester.display_avatar)

        pllist: str = ""
        for i in range(2):
            pllist += f"{i+1}. {playlist.tracks[i].title}\n"
        if len(playlist.tracks) > 2:
            pllist += f"...還有 {len(playlist.tracks)-2} 首歌"
        
        embed.add_field(name=f"歌曲清單 | 已新增 {len(playlist.tracks)} 首歌", value=pllist, inline=False)

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
    async def PlayingMsg(self, channel: discord.TextChannel):
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
            if playlist.loop_state == LoopState.SINGLE \
                    or playlist.loop_state == LoopState.SINGLEINF:
                return

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

    async def PlayingError(self, channel: discord.TextChannel, exception):
        if isinstance(exception, PytubeExceptions.VideoPrivate) \
                or (isinstance(exception, YTDLPExceptions.DownloadError) and "Private Video" in exception.msg):
            reason = 'PLAY_VIDPRIVATE'
        elif isinstance(exception, PytubeExceptions.MembersOnly) \
            or (isinstance(exception, YTDLPExceptions.DownloadError) and "members-only" in exception.msg):
            reason = 'PLAY_FORMEMBERS'
        elif isinstance(exception, PytubeExceptions.LiveStreamError) \
            or (isinstance(exception, YTDLPExceptions.DownloadError) and "This live event will begin in" in exception.msg):
            reason = 'PLAY_NOTSTARTED'
        elif isinstance(exception, PytubeExceptions or YTDLPExceptions.DownloadError):
            reason = 'PLAY_UNAVAILIBLE'
        else:
            reason = "PLAYER_FAULT"

        await self._MusicExceptionHandler(channel, reason, None, exception)

    async def DonePlaying(self, channel: discord.TextChannel) -> None:
        await channel.send(f'''
            **:clock4: | 播放完畢，等待播放動作**
            候播清單已全數播放完畢，等待使用者送出播放指令
            *輸入 **{self.bot.command_prefix}play [URL/歌曲名稱]** 即可播放/搜尋*
        ''')
        self[channel.guild.id].skip = False
        try: 
            await self._UpdateStageTopic(channel.guild.id, 'done')
        except: 
            pass
    #########
    # Pause #
    ######### 
    async def PauseSucceed(self, command: Command, guild_id: int) -> None:
        await command.send(f'''
            **:pause_button: | 暫停歌曲**
            歌曲已暫停播放
            *輸入 **{self.bot.command_prefix}resume** 以繼續播放*
            ''')
        try: 
            await self._UpdateStageTopic(guild_id, 'pause')
        except: 
            pass
    
    async def PauseOnAllMemberLeave(self, channel: discord.TextChannel, guild_id: int) -> None:
        await channel.send(f'''
            **:pause_button: | 暫停歌曲**
            所有人皆已退出語音頻道，歌曲已暫停播放
            *輸入 **{self.bot.command_prefix}resume** 以繼續播放*
            ''')
        try: 
            await self._UpdateStageTopic(guild_id, 'pause')
        except: 
            pass
    
    async def PauseFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "PAUSEFAIL", exception)
    
    ##########
    # Resume #
    ##########
    async def ResumeSucceed(self, command: Command, guild_id: int) -> None:
        await command.send(f'''
            **:arrow_forward: | 續播歌曲**
            歌曲已繼續播放
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
            ''')
        try: 
            await self._UpdateStageTopic(guild_id, 'resume')
        except: 
            pass
    
    async def ResumeFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "RESUMEFAIL", exception)
    
    ########
    # Skip #
    ########
    def SkipProceed(self, guild_id: int):
        self[guild_id].skip = True

    async def SkipFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "SKIPFAIL", exception)
    
    ########
    # Stop #
    ########
    async def StopSucceed(self, command: Command) -> None:
        await command.send(f'''
            **:stop_button: | 停止播放**
            歌曲已停止播放
            *輸入 **{self.bot.command_prefix}play** 以重新開始播放*
            ''')
    
    async def StopFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "STOPFAIL", exception)
    
    ##########
    # Volume #
    ##########
    async def VolumeAdjust(self, command: Command, percent: Union[float, str]):
        if percent == 0:
            return
        # If percent = None, show current volume
        if percent == None: 
            await command.send(f'''
            **:loud_sound: | 音量調整**
            目前音量為 {self.musicbot[command.guild.id].volume_level}%
        ''')

        # Volume unchanged
        if (percent) == self.musicbot[command.guild.id].volume_level:
            await command.send(f'''
            **:loud_sound: | 音量調整**
            音量沒有變更，仍為 {percent}%
        ''')

        # Volume up
        elif (percent) > self.musicbot[command.guild.id].volume_level:
            await command.send(f'''
            **:loud_sound: | 調高音量**
            音量已設定為 {percent}%
        ''')
            self[command.guild.id].mute = False
        # Volume down
        elif (percent) < self.musicbot[command.guild.id].volume_level:
            await command.send(f'''
            **:sound: | 降低音量**
            音量已設定為 {percent}%
        ''')
            self[command.guild.id].mute = False

        if self[command.guild.id].playinfo is not None:
            await self._UpdateSongInfo(command.guild.id)
    
    async def Mute(self, command: Command, percent: Union[float, str]) -> bool:
        mute = self[command.guild.id].mute
        if mute and percent != 0:
            await command.send(f'''
            **:speaker: | 解除靜音**
            音量已設定為 {percent}%，目前已解除靜音模式
        ''')
        elif percent == 0: 
            await command.send(f'''
            **:mute: | 靜音**
            音量已設定為 0%，目前處於靜音模式
        ''')
        if self[command.guild.id].playinfo is not None:
            await self._UpdateSongInfo(command.guild.id)
        self[command.guild.id].mute = percent == 0

    async def VolumeAdjustFailed(self, command: Command) -> None:
        await self._CommonExceptionHandler(command, "VOLUMEADJUSTFAIL")
        
    ########
    # Seek #
    ########
    def _ProgressBar(self, timestamp: int, duration: int, amount: int=15) -> str:
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
    
    async def SeekSucceed(self, command: Command, timestamp: int) -> None:
        playlist = self.musicbot._playlist[command.guild.id]
        if timestamp >= playlist[0].length:
            return
        seektime = _sec_to_hms(timestamp, "symbol")
        duration = _sec_to_hms(playlist[0].length, "symbol")
        bar = self._ProgressBar(timestamp, playlist[0].length)
        await command.send(f'''
            **:timer: | 跳轉歌曲**
            已成功跳轉至指定時間
            **{seektime}** {bar} **{duration}**
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
        ''')
    
    async def SeekFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "SEEKFAIL", exception)
    
    ##########
    # Replay #
    ##########
    async def ReplaySucceed(self, command: Command) -> None:
        await command.send(f'''
            **:repeat: | 重播歌曲**
            歌曲已重新開始播放
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
            ''')
    
    async def ReplayFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "REPLAYFAIL", exception)
    
    ########
    # Loop #
    ########
    async def LoopSucceed(self, command: Command) -> None:
        if command.command_type == 'Interaction' or self[command.guild.id].playinfo is None:
            loopstate = self.musicbot._playlist[command.guild.id].loop_state
            looptimes = self.musicbot._playlist[command.guild.id].times
            if loopstate == LoopState.SINGLEINF:
                msg = '''
            **:repeat_one: | 循環播放**
            已啟動單曲循環播放
            '''
            elif loopstate == LoopState.SINGLE:
                msg = f'''
            **:repeat_one: | 循環播放**
            已啟動單曲循環播放，將會循環 {looptimes} 次
            '''
            elif loopstate == LoopState.PLAYLIST:
                msg = '''
            **:repeat: | 循環播放**
            已啟動待播清單循環播放
            '''
            else:
                msg = '''
            **:repeat: | 循環播放**
            已關閉循環播放功能
            '''
            await command.send(msg)
        if self[command.guild.id].playinfo is not None:
            await self._UpdateSongInfo(command.guild.id)

    async def SingleLoopFailed(self, command: Command) -> None:
        await self._CommonExceptionHandler(command, "LOOPFAIL_SIG")
    
    #########
    # Queue #
    #########
    # Add to queue
    async def Embed_AddedToQueue(self, command: Command, trackinfo: Union[wavelink.Track, wavelink.YouTubePlaylist], requester: Optional[discord.User]) -> None:
        # If queue has more than 2 songs, then show message when
        # user use play command
        playlist: PlaylistBase = self.musicbot._playlist[command.guild.id]
        if len(playlist.order) > 1 or (isinstance(trackinfo, wavelink.YouTubePlaylist)):
            if isinstance(trackinfo, wavelink.YouTubePlaylist):
                msg = '''
                **:white_check_mark: | 成功加入待播清單**
                以下播放清單已加入待播清單中
                '''

                embed = self._PlaylistInfo(trackinfo, requester)
            else:
                index = len(playlist.order) - 1

                msg = f'''
                **:white_check_mark: | 成功加入待播清單**
                以下歌曲已加入待播清單中，為第 **{len(playlist.order)-1}** 首歌
                '''

                embed = self._SongInfo(color_code="green", index=index, guild_id=command.guild.id)

            await command.send(msg, embed=embed)

    # Queue Embed Generator
    def _QueueEmbed(self, playlist: PlaylistBase, page: int=0) -> discord.Embed:
        embed = discord.Embed(title=":information_source: | 候播清單", description=f"以下清單為歌曲候播列表\n共 {len(playlist.order)-1} 首", colour=0xF2F3EE)
        
        for i in range(1, 4):
            index = page*3+i
            if (index == len(playlist.order)): break
            length = _sec_to_hms(playlist[index].length, "symbol")
            embed.add_field(
                name="第 {} 順位\n{}\n{}{} 點歌".format(index, playlist[index].title, "🔴 直播 | " if playlist[index].is_stream() else "", playlist[index].requester),
                value="作者: {}{}{}".format(playlist[index].author, " / 歌曲時長: " if not playlist[index].is_stream() else "", length if not playlist[index].is_stream() else ""),
                inline=False,
            )

        embed_opt = copy.deepcopy(self.__embed_opt__)

        if len(playlist.order) > 4:
            total_pages = (len(playlist.order)-1) // 3
            if (len(playlist.order)-1) % 3 != 0:
                total_pages += 1
            embed_opt['footer']['text'] = f'第 {page+1} 頁 / 共 {total_pages} 頁\n' + self.__embed_opt__['footer']['text']
        
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **embed_opt))
        return embed
    
    # Queue Listing
    async def ShowQueue(self, command: Command) -> None:
        playlist: PlaylistBase = self.musicbot._playlist[command.guild.id]

        class QueueListing(discord.ui.View):

            QueueEmbed = self._QueueEmbed
            embed_opt = self.__embed_opt__

            def __init__(self, *, timeout=60):
                super().__init__(timeout=timeout)
                self.last: discord.ui.Button = self.children[0]
                self.page = 0

            @property
            def first_page_button(self) -> discord.ui.Button:
                return self.children[0]

            @property
            def left_button(self) -> discord.ui.Button:
                return self.children[1]

            @property
            def right_button(self) -> discord.ui.Button:
                return self.children[2]

            @property
            def last_page_button(self) -> discord.ui.Button:
                return self.children[3]

            @property
            def total_pages(self) -> int:
                total_pages = (len(playlist.order)-1) // 3  
                return total_pages

            def update_button(self):
                if self.page == 0:
                    self.left_button.disabled = self.first_page_button.disabled = True
                    self.left_button.style = self.first_page_button.style = discord.ButtonStyle.gray
                else:
                    self.left_button.disabled = self.first_page_button.disabled = False
                    self.left_button.style = self.first_page_button.style = discord.ButtonStyle.blurple
                if self.page == self.total_pages:
                    self.right_button.disabled = self.last_page_button.disabled = True
                    self.right_button.style = self.last_page_button.style = discord.ButtonStyle.gray
                else:
                    self.right_button.disabled = self.last_page_button.disabled = False
                    self.right_button.style = self.last_page_button.style = discord.ButtonStyle.blurple

            @discord.ui.button(label='⏪', style=discord.ButtonStyle.gray, disabled=True)
            async def firstpage(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.page = 0
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='⬅️', style=discord.ButtonStyle.gray, disabled=True)
            async def prevpage(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.page -= 1
                if self.page < 0:
                    self.page = 0
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='➡️', style=discord.ButtonStyle.blurple)
            async def nextpage(self, interaction: discord.Interaction, button: discord.ui.Button):            
                self.page += 1
                if self.page > self.total_pages:
                    self.page = self.total_pages
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='⏩', style=discord.ButtonStyle.blurple)
            async def lastpage(self, interaction: discord.Interaction, button: discord.ui.Button):            
                self.page = self.total_pages
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='❎', style=discord.ButtonStyle.danger)
            async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.message.delete()
                await interaction.response.pong()
                self.stop()

            async def on_timeout(self):
                await msg.delete()
            
        if (len(playlist.order) < 2):
            await command.send(f'''
            **:information_source: | 待播歌曲**
            目前沒有任何歌曲待播中
            *輸入 ** '{self.bot.command_prefix}play 關鍵字或網址' **可繼續點歌*
            ''')
            return
        else:
            embed = self._QueueEmbed(playlist, 0)
            if not (len(playlist.order)) <= 4:
                view = QueueListing()
                msg = await command.send(embed=embed, view=view)
            else:
                await command.send(embed=embed)
    
    # Remove an entity from queue
    async def RemoveSucceed(self, command: Command, idx: int) -> None:
        await command.send(f'''
            **:wastebasket: | 已刪除指定歌曲**
            已刪除 **第 {idx} 順位** 的歌曲，詳細資料如下
            ''', embed=self._SongInfo(command.guild.id, 'red', idx))
    
    async def RemoveFailed(self, command: Command, exception):
        await self._CommonExceptionHandler(command, "REMOVEFAIL", exception)
    
    # Swap entities in queue
    async def Embed_SwapSucceed(self, command: Command, idx1: int, idx2: int) -> None:
        playlist = self.musicbot._playlist[command.guild.id]
        embed = discord.Embed(title=":arrows_counterclockwise: | 調換歌曲順序", description="已調換歌曲順序，以下為詳細資料", colour=0xF2F3EE)
        
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

        await command.send(embed=embed)

    async def SwapFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "SWAPFAIL", exception)
    
    # Move entity to other place in queue
    async def MoveToSucceed(self, command: Command, origin: int, new: int) -> None:
        playlist = self.musicbot._playlist[command.guild.id]
        embed = discord.Embed(title=":arrows_counterclockwise: | 移動歌曲順序", description="已移動歌曲順序，以下為詳細資料", colour=0xF2F3EE)
        
        embed.add_field(name=f"第 ~~{origin}~~ -> **{new}** 順序", value='{}\n{}\n{} 點歌\n'
            .format(
                playlist[new].info['title'],
                playlist[new].info['author'],
                playlist[new].requester
            ), inline=True)
        
        await command.send(embed=embed)

    async def MoveToFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "MOVEFAIL", exception)
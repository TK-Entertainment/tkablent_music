from typing import *
import discord
import random

from ..player import Command
from ..playlist import LoopState
from .info import InfoGenerator
from .stage import Stage
from .exception_handler import ExceptionHandler

class PlayerControl:
    def __init__(self, exception_handler, info_generator, stage):
        from ..ui import bot, musicbot, guild_info, auto_stage_available, _sec_to_hms

        self.info_generator: InfoGenerator = info_generator
        self.exception_handler: ExceptionHandler = exception_handler
        self.bot = bot
        self.stage: Stage = stage
        self.musicbot = musicbot
        self.guild_info = guild_info
        self.auto_stage_available = auto_stage_available
        self._sec_to_hms = _sec_to_hms

    ############################################################
    # Play #####################################################

    async def MultiTypeSetup(self, command: Command):
        content = f'''
        **:bell: | 混合連結預設動作設定**
        部分連結會同時包含歌曲和播放清單
        如 https://www.youtube.com/watch?v=xxxx&list=xxxx
        預設情況下系統會詢問要播放的種類
        但若您已經記住選項，或想要先手動設定，都可以在這邊重新設定

        請選擇以後的預設選項，或清除已記住的選項。
        '''

        class MultiType(discord.ui.View):

            bot = self.bot
            musicbot = self.musicbot
            
            def __init__(self, *, timeout=60):
                self.choice = ""
                super().__init__(timeout=timeout)

            async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button, choice: str):
                view.clear_items()
                if choice == "clear_remember":
                    self.musicbot[command.guild.id].multitype_remembered = False
                    self.musicbot[command.guild.id].multitype_choice = ""
                    await interaction.response.edit_message(
                        content='''
        **:white_check_mark: | 已清除混合連結預設動作設定**
        已清除混合連結預設動作設定，之後將會重新詢問預設動作
                        ''', view=view
                    )
                else:
                    self.musicbot[command.guild.id].multitype_remembered = True
                    self.musicbot[command.guild.id].multitype_choice = choice
                    choice_translated = {"videoonly": "只播放影片", "playlist": "播放整個播放清單"}
                    await interaction.response.edit_message(
                        content=f'''
        **:white_check_mark: | 已設定混合連結預設動作設定**
        已設定混合連結預設動作為 **{choice_translated[choice]}**
                        ''', view=view)
                self.stop()
                    
            @discord.ui.button(label='影片', style=discord.ButtonStyle.blurple)
            async def videoonly(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.toggle(interaction, button, 'videoonly')

            @discord.ui.button(label='播放清單', style=discord.ButtonStyle.blurple)
            async def playlist(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.toggle(interaction, button, 'playlist')

            @discord.ui.button(
                label='清除記住的選擇',
                style=discord.ButtonStyle.danger if musicbot[command.guild.id].multitype_remembered else discord.ButtonStyle.gray,
                disabled = not musicbot[command.guild.id].multitype_remembered)
            async def clear(self, interaction: discord.Interaction, button: discord.ui.Button):            
                await self.toggle(interaction, button, 'clear_remember')

            @discord.ui.button(label='❎', style=discord.ButtonStyle.danger)
            async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.pong()
                await interaction.message.delete()
                self.stop()

            async def on_timeout(self):
                self.clear_items()
                await msg.edit(view=self)
                await msg.add_reaction('🛑')

        view = MultiType()
        msg = await command.send(content, view=view)

    async def MultiTypeNotify(self, command: Command, search):
        content = f'''
        **:bell: | 你所提供的連結有點特別**
        你的連結似乎同時包含歌曲和播放清單，請選擇你想要加入的那一種
        *(如果有選擇困難，你也可以交給機器人決定(#)*
        *"你開心就好" 選項不會被儲存，即使勾選了 "記住我的選擇"*
        *如果記住選擇後想要更改，可以輸入 /playwith 或 *{self.bot.command_prefix}playwith 來重新選擇*'''

        class MultiType(discord.ui.View):

            bot = self.bot
            get_track = self.musicbot._get_track
            musicbot = self.musicbot
            
            def __init__(self, *, timeout=60):
                self.choice = ""
                super().__init__(timeout=timeout)

            async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button, choice: str):
                if choice != 'remember_choice':
                    if choice == 'whatever':
                        self.choice = random.choice(['videoonly', 'playlist'])
                    else:
                        self.choice = choice
                    if self.musicbot[command.guild.id].multitype_remembered and choice != 'whatever':
                        self.musicbot[command.guild.id].multitype_choice = choice
                    await interaction.response.pong()
                    await interaction.message.delete()
                    await self.get_track(command, search, self.choice)
                    self.stop()
                else:
                    if button.label == '⬜ 記住我的選擇':
                        button.label = '✅ 記住我的選擇'
                        button.style = discord.ButtonStyle.success
                        self.musicbot[command.guild.id].multitype_remembered = True
                    else:
                        button.label = '⬜ 記住我的選擇'
                        button.style = discord.ButtonStyle.danger
                        self.musicbot[command.guild.id].multitype_remembered = False
                    await interaction.response.edit_message(view=view)
                    
            @discord.ui.button(label='影片', style=discord.ButtonStyle.blurple)
            async def videoonly(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.toggle(interaction, button, 'videoonly')

            @discord.ui.button(label='播放清單', style=discord.ButtonStyle.blurple)
            async def playlist(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.toggle(interaction, button, 'playlist')

            @discord.ui.button(label='你開心就好', style=discord.ButtonStyle.blurple)
            async def whatever(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.toggle(interaction, button, 'whatever')

            @discord.ui.button(
                label='⬜ 記住我的選擇' if not musicbot[command.guild.id].multitype_remembered else "✅ 記住我的選擇", 
                style=discord.ButtonStyle.danger if not musicbot[command.guild.id].multitype_remembered else discord.ButtonStyle.success)
            async def remember(self, interaction: discord.Interaction, button: discord.ui.Button):            
                await self.toggle(interaction, button, 'remember_choice')

            @discord.ui.button(label='❎', style=discord.ButtonStyle.danger)
            async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.pong()
                await interaction.message.delete()
                self.stop()

            async def on_timeout(self):
                self.clear_items()
                await msg.edit(view=self)
                await msg.add_reaction('🛑')

        view = MultiType()
        msg = await command.send(content, view=view)

    async def PlayingMsg(self, channel: discord.TextChannel):
        playlist = self.musicbot._playlist[channel.guild.id]
        if self.guild_info(channel.guild.id).skip:
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
            self.guild_info(channel.guild.id).skip = False
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
            
        if not self.auto_stage_available(channel.guild.id):
            msg += '\n            *可能需要手動對機器人*` 邀請發言` *才能正常播放歌曲*'
        self.guild_info(channel.guild.id).playinfo = await channel.send(msg, embed=self.info_generator._SongInfo(guild_id=channel.guild.id))
        try: 
            await self.stage._UpdateStageTopic(channel.guild.id)
        except: 
            pass

    # async def PlayingError(self, channel: discord.TextChannel, exception):
    #     if isinstance(exception, PytubeExceptions.VideoPrivate) \
    #             or (isinstance(exception, YTDLPExceptions.DownloadError) and "Private Video" in exception.msg):
    #         reason = 'PLAY_VIDPRIVATE'
    #     elif isinstance(exception, PytubeExceptions.MembersOnly) \
    #         or (isinstance(exception, YTDLPExceptions.DownloadError) and "members-only" in exception.msg):
    #         reason = 'PLAY_FORMEMBERS'
    #     elif isinstance(exception, PytubeExceptions.LiveStreamError) \
    #         or (isinstance(exception, YTDLPExceptions.DownloadError) and "This live event will begin in" in exception.msg):
    #         reason = 'PLAY_NOTSTARTED'
    #     elif isinstance(exception, PytubeExceptions or YTDLPExceptions.DownloadError):
    #         reason = 'PLAY_UNAVAILIBLE'
    #     else:
    #         reason = "PLAYER_FAULT"

    #     await self._MusicExceptionHandler(channel, reason, None, exception)

    async def DonePlaying(self, channel: discord.TextChannel) -> None:
        await channel.send(f'''
            **:clock4: | 播放完畢，等待播放動作**
            候播清單已全數播放完畢，等待使用者送出播放指令
            *輸入 **{self.bot.command_prefix}play [URL/歌曲名稱]** 即可播放/搜尋*
        ''')
        self.guild_info(channel.guild.id).skip = False
        try: 
            await self.stage._UpdateStageTopic(channel.guild.id, 'done')
        except: 
            pass

    ############################################################
    # Pause ####################################################

    async def PauseSucceed(self, command: Command, guild_id: int) -> None:
        await command.send(f'''
            **:pause_button: | 暫停歌曲**
            歌曲已暫停播放
            *輸入 **{self.bot.command_prefix}resume** 以繼續播放*
            ''')
        try: 
            await self.stage._UpdateStageTopic(guild_id, 'pause')
        except: 
            pass
    
    async def PauseOnAllMemberLeave(self, channel: discord.TextChannel, guild_id: int) -> None:
        await channel.send(f'''
            **:pause_button: | 暫停歌曲**
            所有人皆已退出語音頻道，歌曲已暫停播放
            *輸入 **{self.bot.command_prefix}resume** 以繼續播放*
            ''')
        try: 
            await self.stage._UpdateStageTopic(guild_id, 'pause')
        except: 
            pass
    
    async def PauseFailed(self, command: Command, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(command, "PAUSEFAIL", exception)

    ############################################################
    # Resume ###################################################

    async def ResumeSucceed(self, command: Command, guild_id: int) -> None:
        await command.send(f'''
            **:arrow_forward: | 續播歌曲**
            歌曲已繼續播放
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
            ''')
        try: 
            await self.stage._UpdateStageTopic(guild_id, 'resume')
        except: 
            pass
    
    async def ResumeFailed(self, command: Command, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(command, "RESUMEFAIL", exception)

    ############################################################
    # Skip #####################################################

    def SkipProceed(self, guild_id: int):
        self.guild_info(guild_id).skip = True

    async def SkipFailed(self, command: Command, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(command, "SKIPFAIL", exception)

    ############################################################
    # Stop #####################################################

    async def StopSucceed(self, command: Command) -> None:
        await command.send(f'''
            **:stop_button: | 停止播放**
            歌曲已停止播放
            *輸入 **{self.bot.command_prefix}play** 以重新開始播放*
            ''')
    
    async def StopFailed(self, command: Command, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(command, "STOPFAIL", exception)

    ############################################################
    # Seek #####################################################

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
        seektime = self._sec_to_hms(timestamp, "symbol")
        duration = self._sec_to_hms(playlist[0].length, "symbol")
        bar = self._ProgressBar(timestamp, playlist[0].length)
        await command.send(f'''
            **:timer: | 跳轉歌曲**
            已成功跳轉至指定時間
            **{seektime}** {bar} **{duration}**
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
        ''')
    
    async def SeekFailed(self, command: Command, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(command, "SEEKFAIL", exception)

    ############################################################
    # Replay ###################################################

    async def ReplaySucceed(self, command: Command) -> None:
        await command.send(f'''
            **:repeat: | 重播歌曲**
            歌曲已重新開始播放
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
            ''')
    
    async def ReplayFailed(self, command: Command, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(command, "REPLAYFAIL", exception)

    ############################################################
    # Loop #####################################################

    async def LoopSucceed(self, command: Command) -> None:
        if command.command_type == 'Interaction' or self.guild_info(command.guild.id).playinfo is None:
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
            await self.info_generator._UpdateSongInfo(command.guild.id)

    async def SingleLoopFailed(self, command: Command) -> None:
        await self.exception_handler._CommonExceptionHandler(command, "LOOPFAIL_SIG")
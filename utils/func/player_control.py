from typing import *
import discord
import random
import wavelink
import threading
import asyncio

from ..player import Command
from ..playlist import LoopState
from .info import InfoGenerator
from .stage import Stage
from .exception_handler import ExceptionHandler
from .queue import Queue
from .leave import Leave
from ..ui import pause_emoji, play_emoji, stop_emoji, skip_emoji, leave_emoji \
            , repeat_emoji, repeat_sing_emoji, bulb_emoji, queue_emoji, end_emoji

class PlayerControl:
    def __init__(self, exception_handler, info_generator, stage, queue, leave):
        from ..ui import bot, musicbot, guild_info, auto_stage_available, _sec_to_hms

        self.info_generator: InfoGenerator = info_generator
        self.exception_handler: ExceptionHandler = exception_handler
        self.bot = bot
        self.stage: Stage = stage
        self.queue: Queue = queue
        self.leave: Leave = leave
        self.musicbot = musicbot
        self.guild_info = guild_info
        self.auto_stage_available = auto_stage_available
        self._sec_to_hms = _sec_to_hms

    ############################################################
    # Now Playing ##############################################

    async def NowPlaying(self, command: Command):
        if len(self.musicbot._playlist[command.guild.id].order) == 0:
            await command.send(f'''
            **:arrow_forward: | 目前沒有歌曲正在播放**
            *輸入 **{self.bot.command_prefix}play** 來開始播放歌曲*''')
        else:
            if command.command_type == 'Interaction' and command.is_response is not None and not command.is_response():
                await command.send("⠀")
            await self.PlayingMsg(command.channel)

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

            @discord.ui.button(emoji=end_emoji, style=discord.ButtonStyle.danger)
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
        if command.command_type == 'Interaction':
            msg = await command.original_response()

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

            @discord.ui.button(emoji=end_emoji, style=discord.ButtonStyle.danger)
            async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.musicbot[command.guild.id].multitype_remembered and \
                    self.musicbot[command.guild.id].multitype_choice == "":
                    self.musicbot[command.guild.id].multitype_remembered = False
                await interaction.response.pong()
                await interaction.message.delete()
                self.stop()

            async def on_timeout(self):
                if self.musicbot[command.guild.id].multitype_remembered and \
                    self.musicbot[command.guild.id].multitype_choice == "":
                    self.musicbot[command.guild.id].multitype_remembered = False
                self.clear_items()
                await msg.edit(view=self)
                await msg.add_reaction('🛑')

        view = MultiType()
        msg = await command.send(content, view=view)
        if command.command_type == 'Interaction':
            msg = await command.original_response()

    async def PlayingMsg(self, channel: Union[discord.TextChannel, Command]):
        playlist = self.musicbot._playlist[channel.guild.id]
        if self.guild_info(channel.guild.id).playinfo_view is not None \
            and not ((playlist.loop_state == LoopState.SINGLE \
                    or playlist.loop_state == LoopState.SINGLEINF) \
                        and not playlist.current().suggested):
            self.guild_info(channel.guild.id).playinfo_view.clear_items()
            await self.guild_info(channel.guild.id).playinfo.edit(view=self.guild_info(channel.guild.id).playinfo_view)
            self.guild_info(channel.guild.id).playinfo_view.stop()
        
        class PlaybackControl(discord.ui.View):

            bot = self.bot
            voice_client: wavelink.Player = channel.guild.voice_client
            musicbot = self.musicbot
            info_generator = self.info_generator
            queue = self.queue
            leave = self.leave
            guild_info = self.guild_info

            def __init__(self, *, timeout=60):
                super().__init__(timeout=None)
                
            async def restore_skip(self):
                await asyncio.sleep(6)
                self.skip.emoji = skip_emoji
                if len(self.musicbot._playlist[channel.guild.id].order) != 1:
                    self.skip.disabled = False
                    self.skip.style = discord.ButtonStyle.blurple
                await self.guild_info(channel.guild.id).playinfo.edit(view=view)

            async def suggestion_control(self, interaction, button):
                if self.guild_info(channel.guild.id).music_suggestion:
                    button.label = '⬜ 推薦音樂'
                    button.style = discord.ButtonStyle.danger
                    print(f'[Suggestion] {channel.guild.id} disabled auto suggestion')
                    self.guild_info(channel.guild.id).music_suggestion = False
                    if len(self.musicbot._playlist[channel.guild.id].order) == 2 \
                        and self.musicbot._playlist[channel.guild.id].order[1].suggested:
                        self.musicbot._playlist[channel.guild.id].order.pop(1)
                        self.guild_info(channel.guild.id).playinfo_view.skip.emoji = skip_emoji
                        self.guild_info(channel.guild.id).playinfo_view.skip.style = discord.ButtonStyle.gray
                        self.guild_info(channel.guild.id).playinfo_view.skip.disabled = True
                else:
                    button.label = '✅ 推薦音樂'
                    button.style = discord.ButtonStyle.success
                    print(f'[Suggestion] {channel.guild.id} enabled auto suggestion')
                    self.guild_info(channel.guild.id).music_suggestion = True
                    await self.musicbot.process_suggestion(channel.guild)
                    if len(self.musicbot._playlist[channel.guild.id].order) == 2 \
                        and self.musicbot._playlist[channel.guild.id].order[1].suggested:
                        self.guild_info(channel.guild.id).playinfo_view.skip.emoji = skip_emoji
                        self.guild_info(channel.guild.id).playinfo_view.skip.style = discord.ButtonStyle.blurple
                        self.guild_info(channel.guild.id).playinfo_view.skip.disabled = False
                await self.info_generator._UpdateSongInfo(interaction.guild.id)
                await interaction.response.edit_message(view=view)

            @discord.ui.button(
                emoji=pause_emoji if not voice_client.is_paused() else play_emoji, 
                style=discord.ButtonStyle.blurple)
            async def playorpause(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.voice_client.is_paused():
                    await self.voice_client.resume()
                    button.emoji = pause_emoji
                else:
                    await self.voice_client.pause()
                    button.emoji = play_emoji

                await self.info_generator._UpdateSongInfo(interaction.guild.id)
                await interaction.response.edit_message(view=view)

            @discord.ui.button(emoji=stop_emoji, style=discord.ButtonStyle.blurple)
            async def stop_action(self, interaction: discord.Interaction, button: discord.ui.Button):            
                await self.musicbot._stop(channel.guild)
                self.guild_info(channel.guild.id).music_suggestion = False
                self.clear_items()
                await interaction.response.send_message(f'''
            **:stop_button: | 停止播放**
            歌曲已由 {interaction.user.mention} 停止播放
            *輸入 **{self.bot.command_prefix}play** 以重新開始播放*
            ''')
                await self.guild_info(channel.guild.id).playinfo.edit(view=view)
                self.stop()

            @discord.ui.button(
                emoji=skip_emoji, 
                style=discord.ButtonStyle.gray if len(musicbot._playlist[channel.guild.id].order) == 1 else discord.ButtonStyle.blurple,
                disabled=len(musicbot._playlist[channel.guild.id].order) == 1
                )
            async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.musicbot._skip(channel.guild)
                self.guild_info(channel.guild.id).skip = True
                self.clear_items()
                await interaction.response.edit_message(view=view)
                self.stop()

            @discord.ui.button(
                emoji=repeat_emoji if musicbot._playlist[channel.guild.id].loop_state == LoopState.PLAYLIST \
                                or musicbot._playlist[channel.guild.id].loop_state == LoopState.NOTHING \
                                else repeat_sing_emoji,
                label='ₛ' if musicbot._playlist[channel.guild.id].loop_state == LoopState.SINGLEINF else '',
                style=discord.ButtonStyle.danger if musicbot._playlist[channel.guild.id].loop_state == LoopState.NOTHING \
                                                    else discord.ButtonStyle.success)
            async def loop_control(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.musicbot._playlist[channel.guild.id].loop_state == LoopState.NOTHING:
                    self.musicbot._playlist[channel.guild.id].loop_state = LoopState.PLAYLIST
                    button.emoji = repeat_emoji
                    button.label = ''
                    button.style = discord.ButtonStyle.success
                elif self.musicbot._playlist[channel.guild.id].loop_state == LoopState.PLAYLIST:
                    self.musicbot._playlist[channel.guild.id].loop_state = LoopState.SINGLEINF
                    button.emoji = repeat_sing_emoji
                    button.label = 'ₛ'
                    button.style = discord.ButtonStyle.success
                else:
                    self.musicbot._playlist[channel.guild.id].loop_state = LoopState.NOTHING
                    button.emoji = repeat_emoji
                    button.label = ''
                    button.style = discord.ButtonStyle.danger
                await self.info_generator._UpdateSongInfo(interaction.guild.id)
                await interaction.response.edit_message(view=view)

            @discord.ui.button(
                label='⬜ 推薦音樂' if not self.guild_info(channel.guild.id).music_suggestion else "✅ 推薦音樂", 
                style=discord.ButtonStyle.gray if self.musicbot._playlist[channel.guild.id].current().audio_source == 'soundcloud' \
                    else discord.ButtonStyle.danger if not self.guild_info(channel.guild.id).music_suggestion \
                        else discord.ButtonStyle.success,
                disabled=self.musicbot._playlist[channel.guild.id].current().audio_source == 'soundcloud',
                emoji=bulb_emoji)
            async def suggest(self, interaction: discord.Interaction, button: discord.ui.Button):            
                await self.suggestion_control(interaction, button)

            @discord.ui.button(label='列出候播清單', emoji=queue_emoji, style=discord.ButtonStyle.gray)
            async def listqueue(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.queue.ShowQueue(interaction, 'button')

            @discord.ui.button(label='離開語音頻道' if isinstance(channel.guild.voice_client.channel, discord.VoiceChannel) else '離開舞台頻道',
                                emoji=leave_emoji, style=discord.ButtonStyle.gray)
            async def leavech(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.musicbot._leave(channel.guild)
                self.leave.reset_value(channel.guild)
                self.clear_items()
                await channel.send(f'''
            **:outbox_tray: | 已離開語音/舞台頻道**
            {interaction.user.mention} 已讓我停止所有音樂並離開目前所在的語音/舞台頻道
            ''')
                await self.guild_info(channel.guild.id).playinfo.edit(view=view)
                self.stop()

        if self.guild_info(channel.guild.id).skip:
            if len(playlist.order) > 1:
                msg = f'''
            **:fast_forward: | 跳過歌曲**
            目前歌曲已成功跳過，正在播放下一首歌曲，資訊如下所示
            *輸入 **{self.bot.command_prefix}play** 以加入新歌曲*
                '''
            else:
                msg = f'''
            **:fast_forward: | 跳過歌曲**
            目前歌曲已成功跳過，候播清單已無歌曲
            正在播放最後一首歌曲，資訊如下所示
            *輸入 **{self.bot.command_prefix}play** 以加入新歌曲*
                '''
            self.guild_info(channel.guild.id).skip = False
            self.guild_info(channel.guild.id).lastskip = True

            if playlist.loop_state != LoopState.SINGLEINF:
                playlist.loop_state = LoopState.NOTHING
                playlist.times = 0
        else:
            if (playlist.loop_state == LoopState.SINGLE \
                    or playlist.loop_state == LoopState.SINGLEINF) \
                        and not playlist.current().suggested:
                return

            msg = f'''
            **:arrow_forward: | 正在播放以下歌曲**
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*'''
            
        if not self.auto_stage_available(channel.guild.id):
            msg += '\n            *可能需要手動對機器人*` 邀請發言` *才能正常播放歌曲*'
        
        self.guild_info(channel.guild.id).lastskip = False

        embed = self.info_generator._SongInfo(guild_id=channel.guild.id)
        view = PlaybackControl()

        view.skip.emoji = discord.PartialEmoji.from_str('<a:loading:696701361504387212>')
        view.skip.disabled = True
        view.skip.style = discord.ButtonStyle.gray
        self.bot.loop.create_task(view.restore_skip())

        self.guild_info(channel.guild.id).playinfo_view = view
        self.guild_info(channel.guild.id).playinfo = await channel.send(msg, embed=embed, view=view)
        try: 
            await self.stage._UpdateStageTopic(channel.guild.id)
        except: 
            pass

    async def PlayingError(self, channel: discord.TextChannel, exception):
        await self.exception_handler._MusicExceptionHandler(channel, exception, None)

    async def DonePlaying(self, channel: discord.TextChannel) -> None:
        await channel.send(f'''
            **:clock4: | 播放完畢，等待播放動作**
            候播清單已全數播放完畢，等待使用者送出播放指令
            *輸入 **{self.bot.command_prefix}play [URL/歌曲名稱]** 即可播放/搜尋*
        ''')

        # reset values
        self.guild_info(channel.guild.id).skip = False
        self.guild_info(channel.guild.id).music_suggestion = False
        self.guild_info(channel.guild.id).processing_msg = None
        self.guild_info(channel.guild.id).suggestions = []
        if self.musicbot[channel.guild.id]._resuggest_task is not None:
            self.musicbot[channel.guild.id]._resuggest_task.cancel()
            self.musicbot[channel.guild.id]._resuggest_task = None
        if self.musicbot[channel.guild.id]._suggest_search_task is not None:
            self.musicbot[channel.guild.id]._suggest_search_task.cancel()
            self.musicbot[channel.guild.id]._suggest_search_task = None
        try: 
            self.guild_info(channel.guild.id).playinfo_view.clear_items()
            await self.guild_info(channel.guild.id).playinfo.edit(view=self.guild_info(channel.guild.id).playinfo_view)
            self.guild_info(channel.guild.id).playinfo_view.stop()
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
        self.guild_info(command.guild.id).playinfo_view.playorpause.label = '▶️'
        await self.guild_info(command.guild.id).playinfo.edit(view=self.guild_info(command.guild.id).playinfo_view)
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
        self.guild_info(channel.guild.id).playinfo_view.playorpause.emoji = play_emoji
        self.guild_info(channel.guild.id).playinfo_view.playorpause.disabled = True
        self.guild_info(channel.guild.id).playinfo_view.playorpause.style = discord.ButtonStyle.gray
        await self.guild_info(channel.guild.id).playinfo.edit(view=self.guild_info(channel.guild.id).playinfo_view)
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
        self.guild_info(command.guild.id).playinfo_view.playorpause.emoji = pause_emoji
        await self.guild_info(command.guild.id).playinfo.edit(view=self.guild_info(command.guild.id).playinfo_view)
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
                icon = '🔂ₛ'
                color = discord.ButtonStyle.green
            elif loopstate == LoopState.SINGLE:
                msg = f'''
            **:repeat_one: | 循環播放**
            已啟動單曲循環播放，將會循環 {looptimes} 次
            '''
                icon = '🔂ₛ'
                color = discord.ButtonStyle.green
            elif loopstate == LoopState.PLAYLIST:
                msg = '''
            **:repeat: | 循環播放**
            已啟動待播清單循環播放
            '''
                icon = '🔁'
                color = discord.ButtonStyle.green
            else:
                msg = '''
            **:repeat: | 循環播放**
            已關閉循環播放功能
            '''
                icon = '🔁'
                color = discord.ButtonStyle.danger
            await command.send(msg)
        if self.guild_info(command.guild.id).playinfo is not None:
            await self.info_generator._UpdateSongInfo(command.guild.id)
            self.guild_info(command.guild.id).playinfo_view.loop_control.label = icon
            self.guild_info(command.guild.id).playinfo_view.loop_control.style = color
            await self.guild_info(command.guild.id).playinfo.edit(view=self.guild_info(command.guild.id).playinfo_view)

    async def SingleLoopFailed(self, command: Command) -> None:
        await self.exception_handler._CommonExceptionHandler(command, "LOOPFAIL_SIG")
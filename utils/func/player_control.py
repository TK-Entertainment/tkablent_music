import random
from typing import *
import discord
import wavelink
import asyncio
from wavelink import YouTubeTrack, SoundCloudTrack

from ..playlist import LoopState
from .info import InfoGenerator
from .stage import Stage
from .exception_handler import ExceptionHandler
from .queue import Queue
from .leave import Leave
from ..ui import _sec_to_hms, pause_emoji, play_emoji, stop_emoji, skip_emoji, leave_emoji \
            , repeat_emoji, repeat_sing_emoji, bulb_emoji, queue_emoji, end_emoji\
            , loading_emoji, shuffle_emoji, search_emoji, done_emoji, prevpage_emoji, nextpage_emoji

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

    async def NowPlaying(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.send_message("⠀")
            tmpmsg = await interaction.original_response()
            await tmpmsg.delete()

        self.guild_info(interaction.guild.id).playinfo_view.clear_items()
        await self.guild_info(interaction.guild.id).playinfo.edit(view=self.guild_info(interaction.guild.id).playinfo_view)
        self.guild_info(interaction.guild.id).playinfo_view.stop()
        self.guild_info(interaction.guild.id).playinfo = None
        await self.PlayingMsg(interaction.channel)

    ############################################################
    # Play #####################################################

    async def SearchResultSelection(self, interaction: discord.Interaction, result: list[Union[YouTubeTrack, SoundCloudTrack]]) -> None:
        class SelectUI(discord.ui.Select):
            musicbot = self.musicbot

            def __init__(self, result: list[Union[YouTubeTrack, SoundCloudTrack]], page: int=1):
                super().__init__(placeholder='請選擇一個或多個結果...', min_values=1, row=0)
                self.interaction = None
                
                for i in range(len(result)):
                    currentindex = i + 24*(page-1)
                    if currentindex + 1 > len(result):
                        break

                    if isinstance(result[currentindex], str):
                        result.pop(currentindex)
                        continue

                    if i > 24:
                        break
                    length = _sec_to_hms(seconds=(result[currentindex].length)/1000, format="symbol")
                    self.add_option(label=result[currentindex].title, value=currentindex, description=f"{result[currentindex].author} / {length}")
                
                self.max_values = len(self.options)

            async def callback(self, interaction: discord.Interaction):
                await msg.edit(content="⠀", view=None)
                view.clear_items()
                view.stop()
                if len(self.values) > 0:
                    songlist = []
                    for i in self.values:
                        songlist.append(result[int(i)])
                    songlist.append('Search')
                    await self.musicbot.play(interaction, songlist)
                else:
                    option_index = int(self.values[0])
                    await self.musicbot.play(interaction, result[option_index])
        
        class SelectView(discord.ui.View):
            def __init__(self, result: list[Union[YouTubeTrack, SoundCloudTrack]]):
                super().__init__(timeout=180)
                self.select_ui = SelectUI(result)
                self.page = 1
                self.add_item(self.select_ui)

            @discord.ui.button(emoji=prevpage_emoji, style=discord.ButtonStyle.blurple, row=1)
            async def prevpage(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.page -= 1
                content = f'''
        **:mag_right: | 搜尋結果**
        請選擇一個您欲播放的歌曲：
        第 {self.page} 頁 / 共 {(len(result) // 24) + 1} 頁
        '''
                self.remove_item(self.select_ui)
                self.select_ui = SelectUI(result, self.page)
                self.add_item(self.select_ui)

                if self.page != 1:
                    self.prevpage.disabled = False
                    self.prevpage.style = discord.ButtonStyle.blurple
                else:
                    self.prevpage.disabled = True
                    self.prevpage.style = discord.ButtonStyle.gray

                if self.page < (len(result) // 24) + 1:
                    self.nextpage.disabled = False
                    self.nextpage.style = discord.ButtonStyle.blurple

                await interaction.response.edit_message(content=content, view=view)

            @discord.ui.button(emoji=nextpage_emoji, style=discord.ButtonStyle.blurple, row=1)
            async def nextpage(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.page += 1
                content = f'''
        **:mag_right: | 搜尋結果**
        請選擇一個您欲播放的歌曲：
        第 {self.page} 頁 / 共 {(len(result) // 24) + 1} 頁
        '''
                self.remove_item(self.select_ui)
                self.select_ui = SelectUI(result, self.page)
                self.add_item(self.select_ui)

                if self.page >= (len(result) // 24) + 1:
                    self.nextpage.disabled = True
                    self.nextpage.style = discord.ButtonStyle.gray
                else:
                    self.nextpage.disabled = False
                    self.nextpage.style = discord.ButtonStyle.blurple

                if self.page != 1:
                    self.prevpage.disabled = False
                    self.prevpage.style = discord.ButtonStyle.blurple

                await interaction.response.edit_message(content=content, view=view)

            @discord.ui.button(emoji=end_emoji, style=discord.ButtonStyle.danger, row=1)
            async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.pong()
                await interaction.message.delete()
                self.stop()

            async def on_timeout(self):
                self.clear_items()
                try:
                    await msg.edit(view=self)
                    await msg.add_reaction('🛑')
                except:
                    pass

        view = SelectView(result)
        if len(result) <= 24:
            view.remove_item(view.prevpage)
            view.remove_item(view.nextpage)
            pagetext = ''
        else:
            view.prevpage.disabled = True
            view.prevpage.style = discord.ButtonStyle.gray
            pagetext = f'第 {view.page} 頁 / 共 {(len(result) // 24) + 1} 頁'

        content = f'''
        **:mag_right: | 搜尋結果**
        請選擇一個您欲播放的歌曲：
        {pagetext}
        '''

        view.remove_item(view.done)
        await interaction.edit_original_response(content=content, view=view)
        msg = await interaction.original_response()

    async def MultiTypeSetup(self, interaction: discord.Interaction):
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
                    self.musicbot[interaction.guild.id].multitype_remembered = False
                    self.musicbot[interaction.guild.id].multitype_choice = ""
                    await interaction.response.edit_message(
                        content='''
        **:white_check_mark: | 已清除混合連結預設動作設定**
        已清除混合連結預設動作設定，之後將會重新詢問預設動作
                        ''', view=view
                    )
                else:
                    self.musicbot[interaction.guild.id].multitype_remembered = True
                    self.musicbot[interaction.guild.id].multitype_choice = choice
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
                style=discord.ButtonStyle.danger if musicbot[interaction.guild.id].multitype_remembered else discord.ButtonStyle.gray,
                disabled = not musicbot[interaction.guild.id].multitype_remembered)
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
        await interaction.response.send_message(content, view=view)
        msg = await interaction.original_response()

    async def MultiTypeNotify(self, interaction: discord.Interaction, search):
        content = f'''
        **:bell: | 你所提供的連結有點特別**
        你的連結似乎同時包含歌曲和播放清單，請選擇你想要加入的那一種
        *(如果有選擇困難，你也可以交給機器人決定(#)*
        *"你開心就好" 選項不會被儲存，即使勾選了 "記住我的選擇"*
        *如果記住選擇後想要更改，可以輸入 /playwith 來重新選擇*'''

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
                    if self.musicbot[interaction.guild.id].multitype_remembered and choice != 'whatever':
                        self.musicbot[interaction.guild.id].multitype_choice = choice
                    await interaction.response.pong()
                    await interaction.message.delete()
                    track = await self.get_track(interaction, search, self.choice)
                    await self.musicbot.play(interaction, track)
                    self.stop()
                else:
                    if button.label == '⬜ 記住我的選擇':
                        button.label = '✅ 記住我的選擇'
                        button.style = discord.ButtonStyle.success
                        self.musicbot[interaction.guild.id].multitype_remembered = True
                    else:
                        button.label = '⬜ 記住我的選擇'
                        button.style = discord.ButtonStyle.danger
                        self.musicbot[interaction.guild.id].multitype_remembered = False
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
                label='⬜ 記住我的選擇' if not musicbot[interaction.guild.id].multitype_remembered else "✅ 記住我的選擇", 
                style=discord.ButtonStyle.danger if not musicbot[interaction.guild.id].multitype_remembered else discord.ButtonStyle.success)
            async def remember(self, interaction: discord.Interaction, button: discord.ui.Button):            
                await self.toggle(interaction, button, 'remember_choice')

            @discord.ui.button(emoji=end_emoji, style=discord.ButtonStyle.danger)
            async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.musicbot[interaction.guild.id].multitype_remembered and \
                    self.musicbot[interaction.guild.id].multitype_choice == "":
                    self.musicbot[interaction.guild.id].multitype_remembered = False
                await interaction.response.pong()
                await interaction.message.delete()
                self.stop()

            async def on_timeout(self):
                if self.musicbot[interaction.guild.id].multitype_remembered and \
                    self.musicbot[interaction.guild.id].multitype_choice == "":
                    self.musicbot[interaction.guild.id].multitype_remembered = False
                self.clear_items()
                await msg.edit(view=self)
                await msg.add_reaction('🛑')

        view = MultiType()
        await interaction.response.send_message(content, view=view)
        msg = await interaction.original_response()

    async def PlayingMsg(self, channel: Union[discord.TextChannel, discord.Interaction]):
        playlist = self.musicbot._playlist[channel.guild.id]

        if len(playlist.order) > 0 \
                and (playlist.loop_state != LoopState.NOTHING) \
                and not playlist.current().suggested \
                and not self.guild_info(channel.guild.id).skip:
            await self.info_generator._UpdateSongInfo(channel.guild.id)
            return

        if len(self.musicbot._playlist[channel.guild.id].order) == 0:
            msg = f'''
            **:arrow_forward: | 目前沒有歌曲正在播放**
            *輸入 **{self.bot.command_prefix}play** 來開始播放歌曲*'''

            if await self.guild_info(channel.guild.id).playinfo is not None:
                await self.guild_info(channel.guild.id).playinfo.edit(content=msg)
            else:
                if isinstance(channel, discord.Interaction):
                    await channel.response.send_message(msg)
                else:
                    await channel.send(msg)

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

            async def restore_shuffle(self):
                await asyncio.sleep(3)
                self.shuffle.emoji = shuffle_emoji
                self.shuffle.disabled = False
                self.shuffle.style = discord.ButtonStyle.blurple
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
                    await self.musicbot._playlist.process_suggestion(channel.guild, self.guild_info(channel.guild.id))
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
                await interaction.response.send_message(f'''
            **:stop_button: | 停止播放**
            歌曲已由 {interaction.user.mention} 停止播放
            *輸入 **{self.bot.command_prefix}play** 以重新開始播放*
            ''')
                self.stop()

            @discord.ui.button(
                emoji=skip_emoji, 
                style=discord.ButtonStyle.gray if len(musicbot._playlist[channel.guild.id].order) == 1 else discord.ButtonStyle.blurple,
                disabled=len(musicbot._playlist[channel.guild.id].order) == 1
                )
            async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.guild_info(channel.guild.id).skip = True
                await self.musicbot._skip(channel.guild)

                if len(playlist.order) > 1:
                    embed = self.info_generator._SongInfo(guild_id=channel.guild.id, index=1)

                    self.guild_info(channel.guild.id).playinfo_view.skip.emoji = loading_emoji
                    self.guild_info(channel.guild.id).playinfo_view.skip.disabled = True
                    self.guild_info(channel.guild.id).playinfo_view.skip.style = discord.ButtonStyle.gray
                    self.bot.loop.create_task(self.guild_info(channel.guild.id).playinfo_view.restore_skip())
                    view = self.guild_info(channel.guild.id).playinfo_view
                else:
                    embed = self.info_generator._SongInfo(guild_id=channel.guild.id)
                    view = None

                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(
                emoji=shuffle_emoji, 
                disabled=len(musicbot._playlist[channel.guild.id].order) < 3,
                style=discord.ButtonStyle.gray if len(musicbot._playlist[channel.guild.id].order) < 3 else discord.ButtonStyle.blurple,
                )
            async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):            
                self.musicbot._playlist[channel.guild.id].shuffle()
                self.shuffle.emoji = done_emoji
                self.shuffle.disabled = True
                self.shuffle.style = discord.ButtonStyle.success
                await interaction.response.edit_message(view=view)
                await self.info_generator._UpdateSongInfo(interaction.guild.id)
                self.bot.loop.create_task(self.restore_shuffle())

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

                await self.musicbot._playlist.process_suggestion(channel.guild, self.guild_info(channel.guild.id))

                await self.info_generator._UpdateSongInfo(interaction.guild.id)
                await interaction.response.edit_message(view=view)

            @discord.ui.button(
                label='⬜ 推薦音樂' if not self.guild_info(channel.guild.id).music_suggestion else "✅ 推薦音樂", 
                style=discord.ButtonStyle.danger if not self.guild_info(channel.guild.id).music_suggestion \
                        else discord.ButtonStyle.success,
                emoji=bulb_emoji)
            async def suggest(self, interaction: discord.Interaction, button: discord.ui.Button):            
                await self.suggestion_control(interaction, button)

            @discord.ui.button(label='搜尋/新增歌曲', emoji=search_emoji, style=discord.ButtonStyle.green)
            async def new_song(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(self.queue.new_song_modal_helper()(interaction.user))

            @discord.ui.button(label='列出候播清單', emoji=queue_emoji, style=discord.ButtonStyle.gray, row=2)
            async def listqueue(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.queue.ShowQueue(interaction, 'button')

            @discord.ui.button(label='離開語音頻道' if isinstance(channel.guild.voice_client.channel, discord.VoiceChannel) else '離開舞台頻道',
                                emoji=leave_emoji, style=discord.ButtonStyle.gray, row=2)
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
        
        self.guild_info(channel.guild.id).lastskip = False

        embed = self.info_generator._SongInfo(guild_id=channel.guild.id)

        if self.guild_info(channel.guild.id).skip:
            self.guild_info(channel.guild.id).skip = False
            self.guild_info(channel.guild.id).lastskip = True

        if self.guild_info(channel.guild.id).playinfo is None:
            view = PlaybackControl()

            view.skip.emoji = loading_emoji
            view.skip.disabled = True
            view.skip.style = discord.ButtonStyle.gray
            self.bot.loop.create_task(view.restore_skip())

            self.guild_info(channel.guild.id).playinfo_view = view
            self.guild_info(channel.guild.id).playinfo = await channel.send(embed=embed, view=view)
        else:
            await self.guild_info(channel.guild.id).playinfo.edit(embed=embed)

        try: 
            await self.stage._UpdateStageTopic(channel.guild.id)
        except: 
            pass

    async def PlayingError(self, channel: discord.TextChannel, exception):
        await self.exception_handler._MusicExceptionHandler(channel, exception, None)

    async def DonePlaying(self, channel: discord.TextChannel) -> None:
        try:
            self.guild_info(channel.guild.id).playinfo_view.clear_items()
            await self.info_generator._UpdateSongInfo(channel.guild.id)
            self.guild_info(channel.guild.id).playinfo_view.stop()
        except:
            pass

        # reset values
        self.guild_info(channel.guild.id).skip = False
        self.guild_info(channel.guild.id).music_suggestion = False
        self.guild_info(channel.guild.id).processing_msg = None
        self.guild_info(channel.guild.id).suggestions = []
        if self.musicbot._playlist[channel.guild.id]._resuggest_task is not None:
            self.musicbot._playlist[channel.guild.id]._resuggest_task.cancel()
            self.musicbot._playlist[channel.guild.id]._resuggest_task = None
        if self.musicbot._playlist[channel.guild.id]._suggest_search_task is not None:
            self.musicbot._playlist[channel.guild.id]._suggest_search_task.cancel()
            self.musicbot._playlist[channel.guild.id]._suggest_search_task = None
        self.guild_info(channel.guild.id).playinfo_view = None
        self.guild_info(channel.guild.id).playinfo = None
        try: 
            await self.stage._UpdateStageTopic(channel.guild.id, 'done')
        except: 
            pass

    ############################################################
    # Pause ####################################################

    async def PauseSucceed(self, interaction: discord.Interaction, guild_id: int) -> None:
        await interaction.response.send_message(f'''
            **:pause_button: | 暫停歌曲**
            歌曲已暫停播放
            *輸入 **{self.bot.command_prefix}resume** 以繼續播放*
            ''')
        self.guild_info(interaction.guild.id).playinfo_view.playorpause.label = '▶️'
        await self.guild_info(interaction.guild.id).playinfo.edit(view=self.guild_info(interaction.guild.id).playinfo_view)
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
    
    async def PauseFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(interaction, "PAUSEFAIL", exception)

    ############################################################
    # Resume ###################################################

    async def ResumeSucceed(self, interaction: discord.Interaction, guild_id: int) -> None:
        await interaction.response.send_message(f'''
            **:arrow_forward: | 續播歌曲**
            歌曲已繼續播放
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
            ''')
        self.guild_info(interaction.guild.id).playinfo_view.playorpause.emoji = pause_emoji
        await self.guild_info(interaction.guild.id).playinfo.edit(view=self.guild_info(interaction.guild.id).playinfo_view)
        try: 
            await self.stage._UpdateStageTopic(guild_id, 'resume')
        except: 
            pass
    
    async def ResumeFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(interaction, "RESUMEFAIL", exception)

    ############################################################
    # Skip #####################################################

    def SkipProceed(self, guild_id: int):
        self.guild_info(guild_id).skip = True

    async def SkipFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(interaction, "SKIPFAIL", exception)

    ############################################################
    # Stop #####################################################

    async def StopSucceed(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f'''
            **:stop_button: | 停止播放**
            歌曲已停止播放
            *輸入 **{self.bot.command_prefix}play** 以重新開始播放*
            ''')
    
    async def StopFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(interaction, "STOPFAIL", exception)

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
    
    async def SeekSucceed(self, interaction: discord.Interaction, timestamp: int) -> None:
        playlist = self.musicbot._playlist[interaction.guild.id]
        if timestamp >= (playlist[0].length)/1000:
            return
        seektime = self._sec_to_hms(timestamp, "symbol")
        duration = self._sec_to_hms(playlist[0].length, "symbol")
        bar = self._ProgressBar(timestamp, (playlist[0].length)/1000)
        await interaction.response.send_message(f'''
            **:timer: | 跳轉歌曲**
            已成功跳轉至指定時間
            **{seektime}** {bar} **{duration}**
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
        ''')
    
    async def SeekFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(interaction, "SEEKFAIL", exception)

    ############################################################
    # Replay ###################################################

    async def ReplaySucceed(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f'''
            **:repeat: | 重播歌曲**
            歌曲已重新開始播放
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*
            ''')
    
    async def ReplayFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(interaction, "REPLAYFAIL", exception)

    ############################################################
    # Loop #####################################################

    async def LoopSucceed(self, interaction: discord.Interaction) -> None:
        if self.guild_info(interaction.guild.id).playinfo is None:
            loopstate = self.musicbot._playlist[interaction.guild.id].loop_state
            looptimes = self.musicbot._playlist[interaction.guild.id].times
            if loopstate == LoopState.SINGLEINF:
                msg = '''
            **:repeat_one: | 循環播放**
            已啟動單曲循環播放
            '''
                text = 'ₛ'
                icon = repeat_sing_emoji
                color = discord.ButtonStyle.green
            elif loopstate == LoopState.SINGLE:
                msg = f'''
            **:repeat_one: | 循環播放**
            已啟動單曲循環播放，將會循環 {looptimes} 次
            '''
                text = f'ₛ {looptimes} 次'
                icon = repeat_sing_emoji
                color = discord.ButtonStyle.green
            elif loopstate == LoopState.PLAYLIST:
                msg = '''
            **:repeat: | 循環播放**
            已啟動待播清單循環播放
            '''
                text = ''
                icon = repeat_emoji
                color = discord.ButtonStyle.green
            else:
                msg = '''
            **:repeat: | 循環播放**
            已關閉循環播放功能
            '''
                text = ''
                icon = repeat_emoji
                color = discord.ButtonStyle.danger
            await interaction.response.send_message(msg)
        if self.guild_info(interaction.guild.id).playinfo is not None:
            await self.info_generator._UpdateSongInfo(interaction.guild.id)
            self.guild_info(interaction.guild.id).playinfo_view.loop_control.emoji = icon
            self.guild_info(interaction.guild.id).playinfo_view.loop_control.label = text
            self.guild_info(interaction.guild.id).playinfo_view.loop_control.style = color
            await self.guild_info(interaction.guild.id).playinfo.edit(view=self.guild_info(interaction.guild.id).playinfo_view)

    async def SingleLoopFailed(self, interaction: discord.Interaction) -> None:
        await self.exception_handler._CommonExceptionHandler(interaction, "LOOPFAIL_SIG")

    ###############################################################
    # Shuffle #####################################################

    async def ShuffleSucceed(self, interaction: discord.Interaction) -> None:
        msg = f'''
            **:twisted_rightwards_arrows: | 隨機排列待播清單**
            待播清單已成功隨機排列
            '''
        await interaction.response.send_message(msg, ephemeral=True)

    async def ShuffleFailed(self, interaction: discord.Interaction) -> None:
        await self.exception_handler._CommonExceptionHandler(interaction, "SHUFFLEFAIL")
from typing import *
import asyncio, json, os
import dotenv
import validators

import discord
from discord.ext import commands
from discord import app_commands

import bilibili_api as bilibili
import wavelink
from wavelink.ext import spotify
from .playlist import Playlist, SpotifyAlbum, SpotifyPlaylist, LoopState

INF = int(1e18)

class GuildInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.text_channel: discord.TextChannel = None
        self._task: asyncio.Task = None
        self._refresh_msg_task: asyncio.Task = None
        self._timer: asyncio.Task = None
        self._dsa: bool = None
        self._multitype_remembered: bool = None
        self._multitype_choice: str = None


    @property
    def data_survey_agreement(self):
        if self._dsa is None:
            self._dsa = self.fetch('dsa')
        return self._dsa

    @data_survey_agreement.setter
    def data_survey_agreement(self, value: bool):
        self._dsa(self, value)
        self.update("dsa", value)

    @property
    def multitype_remembered(self):
        if self._multitype_remembered is None:
            self._multitype_remembered = self.fetch('multitype_remembered')
        return self._multitype_remembered
    
    @multitype_remembered.setter
    def multitype_remembered(self, value: bool):
        self._multitype_remembered(self, value)
        self.update("multitype_remembered", value)

    @property
    def multitype_choice(self):
        if self._multitype_choice is None:
            self._multitype_choice = self.fetch('multitype_choice')
        return self._multitype_choice

    @multitype_choice.setter
    def multitype_choice(self, value: str):
        self._multitype_choice(self, value)
        self.update("multitype_choice", value)

    def fetch(self, key: str) -> not None:
        '''fetch from database'''
        with open(fr"{os.getcwd()}/utils/data.json", 'r') as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None or data[str(self.guild_id)].get(key) is None:
            return data['default'][key]
        return data[str(self.guild_id)][key]

    def update(self, key: str, value: str) -> None:
        '''update database'''

        with open(fr"{os.getcwd()}/utils/data.json", 'r') as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None:
            data[str(self.guild_id)] = dict()
        data[str(self.guild_id)][key] = value
        with open(fr"{os.getcwd()}/utils/data.json", 'w') as f:
            json.dump(data, f)

class Player:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._playlist: Playlist = Playlist()
        self._guilds_info: Dict[int, GuildInfo] = dict()
        self._spotify: spotify.SpotifyClient = None

    def __getitem__(self, guild_id) -> GuildInfo:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = GuildInfo(guild_id)
        return self._guilds_info[guild_id] 

    async def _create_daemon(self):
        TW_HOST = os.getenv('WAVELINK_TW_HOST')
        US_HOST = os.getenv('WAVELINK_US_HOST')
        SEARCH_HOST = os.getenv('WAVELINK_SEARCH_HOST')
        PORT = os.getenv('WAVELINK_PORT')
        SEARCH_PORT = os.getenv('WAVELINK_SEARCH_PORT')
        PASSWORD = os.getenv('WAVELINK_PWD')
        SPOTIFY_ID = os.getenv('SPOTIFY_ID')
        SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
        SESSDATA = os.getenv('SESSDATA')
        BILI_JCT = os.getenv('BILI_JCT')
        BUVID3 = os.getenv('BUVID3')
        DEDEUSERID = os.getenv('DEDEUSERID')
        AC_TIME_VALUE = os.getenv('AC_TIME_VALUE')
        
        self._playlist.init_spotify(SPOTIFY_ID, SPOTIFY_SECRET)
        mainplayhost = wavelink.Node(
            id="US_PlayBackNode",
            uri=f"http://{US_HOST}:{PORT}",
            use_http=True,
            password=PASSWORD,
        )
        altplayhost = wavelink.Node(
            id="TW_PlayBackNode",
            uri=f"http://{TW_HOST}:{PORT}",
            use_http=True,
            password=PASSWORD,
        )
        searchhost = wavelink.Node(
            id="SearchNode",
            uri=f"http://{SEARCH_HOST}:{SEARCH_PORT}",
            use_http=True,
            password=PASSWORD,
        )

        self._bilibilic = bilibili.Credential(
            sessdata=SESSDATA,
            bili_jct=BILI_JCT,
            buvid3=BUVID3,
            dedeuserid=DEDEUSERID,
            ac_time_value=AC_TIME_VALUE
        )
        
        valid = await self._bilibilic.check_valid()

        print(f"[BiliBili API] Cookie valid: {valid}")

        # if valid:
        #     await self.bot.loop.create_task(self._refresh_sessdata())

        self._spotify = spotify.SpotifyClient(client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET)

        await wavelink.NodePool.connect(
            client=self.bot,
            nodes=[mainplayhost, altplayhost, searchhost],
            spotify=self._spotify
        )

    async def _refresh_sessdata(self):
        while True:
            need_refresh = await self._bilibilic.chcek_refresh()
            if need_refresh:
                await self._bilibilic.refresh()
                sessdata = self._bilibilic.sessdata
                bili_jct = self._bilibilic.bili_jct
                dotenv.set_key(dotenv_path=fr"{os.getcwd()}/.env", key_to_set="SESSDATA", value_to_set=sessdata)
                dotenv.set_key(dotenv_path=fr"{os.getcwd()}/.env", key_to_set="BILI_JCT", value_to_set=bili_jct)
            await asyncio.sleep(120)

    async def _join(self, channel: discord.VoiceChannel):
        voice_client = channel.guild.voice_client
        mainplayhost = wavelink.NodePool.get_node(id="US_PlayBackNode")
        altplayhost = wavelink.NodePool.get_node(id="TW_PlayBackNode")
        if voice_client is None:
            await channel.connect(cls=wavelink.Player(nodes=[mainplayhost, altplayhost]))

    async def _leave(self, guild: discord.Guild):
        voice_client = guild.voice_client
        if voice_client is not None:
            await self._stop(guild)
            await voice_client.disconnect()
            
    async def _search(self, guild: discord.Guild, trackinfo, requester: discord.Member):
        await self._playlist.add_songs(guild.id, trackinfo, requester)

    async def _pause(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if not voice_client.is_paused() and voice_client.is_playing():
            await voice_client.pause()

    async def _resume(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client.is_paused():
            await voice_client.resume()

    async def _skip(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            if voice_client.is_paused():
                await voice_client.resume()
            await voice_client.stop()
            self._playlist[guild.id].times = 0
            if self._playlist[guild.id].loop_state == LoopState.SINGLEINF:
                self._playlist[guild.id].loop_state = LoopState.NOTHING
    
    async def _stop(self, guild: discord.Guild):
        self._playlist[guild.id].clear()
        await self._skip(guild)
    
    async def _seek(self, guild: discord.Guild, timestamp: float):
        voice_client: wavelink.Player = guild.voice_client
        if timestamp >= (self._playlist[guild.id].current().length)/1000:
            await voice_client.stop()
        await voice_client.seek(timestamp * 1000)
    
    async def _volume(self, guild: discord.Guild, volume: float):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client is not None:
            mute = volume == 0
            if mute:
                volume = 1e-5
            else:
                self[guild.id].volume_level = volume
            await voice_client.set_volume(volume)
            await self.bot.ws.voice_state(guild.id, voice_client.channel.id, self_mute=mute)
            
    async def _play(self, guild: discord.Guild, channel: discord.TextChannel):
        self[guild.id].text_channel = channel
        await self._start_mainloop(guild)

    async def _start_mainloop(self, guild: discord.Guild):
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
            self[guild.id]._timer = None
        if self[guild.id]._task is not None:
            return
        coro = self._mainloop(guild)
        self[guild.id]._task = self.bot.loop.create_task(coro)
        self[guild.id]._task.add_done_callback(lambda task, guild=guild: self._start_timer(guild))
    
    async def _mainloop(self, guild: discord.Guild):
        # implement in musicbot class for ui support
        '''
        while len(self._playlist[guild.id].order):
            await self[guild.id].text_channel.send('now playing')
            voice_client: VoiceClient = guild.voice_client
            song = self._playlist[guild.id].current()
            try:
                voice_client.play(discord.FFmpegPCMAudio(song.url))
                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(1.0)
            finally:
                self._playlist.rule(guild.id)
        '''
        raise NotImplementedError

    def _start_timer(self, guild: discord.Guild):
        if self[guild.id]._task is not None:
            self[guild.id]._task.cancel()
            self[guild.id]._task = None
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
        coro = self._timer(guild)
        self[guild.id]._timer = self.bot.loop.create_task(coro)
    
    async def _timer(self, guild: discord.Guild):
        await asyncio.sleep(600.0)
        await self._leave(guild)
    
    def _cleanup(self, guild: discord.Guild):
        if self[guild.id]._task is not None:
            self[guild.id]._task = None
        del self._playlist[guild.id]
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
            self[guild.id]._timer = None

class MusicCog(Player, commands.Cog):
    def __init__(self, bot: commands.Bot, bot_version):
        Player.__init__(self, bot)
        commands.Cog.__init__(self)
        self.bot: commands.Bot = bot
        self.bot_version = bot_version

    async def resolve_ui(self):   
        from .ui import UI, auto_stage_available, guild_info
        self.ui = UI(self, self.bot_version)
        self.auto_stage_available = auto_stage_available
        self.ui_guild_info = guild_info
        from .ui import groupbutton
        self.groupbutton = groupbutton

    @app_commands.command(name='help', description="❓ | 不知道怎麼使用我嗎？來這裡就對了~")
    async def help(self, interaction: discord.Interaction):
        await self.ui.Help.Help(interaction)

    ##############################################

    @app_commands.command(name='playwith', description="⚙️ | 設定對於混合連結的預設動作")
    async def mtsetup(self, interaction: discord.Interaction):
        await self.ui.PlayerControl.MultiTypeSetup(interaction)

    ##############################################

    async def ensure_stage_status(self, interaction: discord.Interaction):
        '''a helper function for opening a stage'''

        if not isinstance(interaction.user.voice.channel, discord.StageChannel):
            return

        bot_itself: discord.Member = await interaction.guild.fetch_member(self.bot.user.id)
        auto_stage_vaildation = self.auto_stage_available(interaction.guild.id)
        
        if interaction.user.voice.channel.instance is None:
            await self.ui.Stage.CreateStageInstance(interaction, interaction.guild.id)
        
        if auto_stage_vaildation and bot_itself.voice.suppress:
            try: 
                await bot_itself.edit(suppress=False)
            except: 
                auto_stage_vaildation = False

    async def rejoin(self, interaction: discord.Interaction):
        voice_client: wavelink.Player = interaction.guild.voice_client
        # Get the bot former playing state
        former: discord.VoiceChannel = voice_client.channel
        former_state: bool = voice_client.is_paused()
        # To determine is the music paused before rejoining or not
        if not former_state: 
            await self._pause(interaction.guild)
        # Moving itself to author's channel
        await voice_client.move_to(interaction.user.voice.channel)
        if isinstance(interaction.user.voice.channel, discord.StageChannel):
            await self.ensure_stage_status(interaction)

        # If paused before rejoining, resume the music
        if not former_state: 
            await self._resume(interaction.guild)
        # Send a rejoin message
        await self.ui.Join.RejoinNormal(interaction)
        # If the former channel is a discord.StageInstance which is the stage
        # channel with topics, end that stage instance
        if isinstance(former, discord.StageChannel) and \
                isinstance(former.instance, discord.StageInstance):
            await self.ui.Stage.EndStage(interaction.guild.id)

    async def join(self, interaction: discord.Interaction):
        voice_client: wavelink.Player = interaction.guild.voice_client
        if isinstance(voice_client, wavelink.Player):
            if voice_client.channel != interaction.user.voice.channel:
                await self.rejoin(interaction)
            else:
                # If bot joined the same channel, send a message to notice user
                await self.ui.Join.JoinAlready(interaction)
            return
        try:
            await self._join(interaction.user.voice.channel)
            voice_client: wavelink.Player = interaction.guild.voice_client
            if isinstance(voice_client.channel, discord.StageChannel):
                await self.ensure_stage_status(interaction)
                await self.ui.Join.JoinStage(interaction, interaction.guild.id)
            else:
                await self.ui.Join.JoinNormal(interaction)
        except Exception as e:
            await self.ui.Join.JoinFailed(interaction, e)

    @app_commands.command(name='join', description='📥 | 將我加入目前您所在的頻道')
    async def _join_s(self, interaction: discord.Interaction):
        await self.join(interaction)

    ##############################################

    @app_commands.command(name='leave', description='📤 | 讓我從目前您所在的頻道離開')
    async def leave(self, interaction: discord.Interaction):
        voice_client: wavelink.Player = interaction.guild.voice_client
        try:
            if isinstance(voice_client.channel, discord.StageChannel) and \
                    isinstance(voice_client.channel.instance, discord.StageInstance):
                await self.ui.Stage.EndStage(interaction.guild.id)
            await self._leave(interaction.guild)
            await self.ui.Leave.LeaveSucceed(interaction)
        except Exception as e:
            await self.ui.Leave.LeaveFailed(interaction, e)

    ##############################################

    @app_commands.command(name='pause', description='⏸️ | 暫停目前播放的音樂')
    async def pause(self, interaction: discord.Interaction):
        try:
            await self._pause(interaction.guild)
            await self.ui.PlayerControl.PauseSucceed(interaction, interaction.guild.id)
        except Exception as e:
            await self.ui.PlayerControl.PauseFailed(interaction, e)

    ##############################################

    @app_commands.command(name='resume', description='▶️ | 繼續播放目前暫停的歌曲')
    async def resume(self, interaction: discord.Interaction):
        try:
            if isinstance(interaction.channel, discord.StageChannel):
                await self.ensure_stage_status(interaction)
            await self._resume(interaction.guild)
            await self.ui.PlayerControl.ResumeSucceed(interaction, interaction.guild.id)
        except Exception as e:
            await self.ui.PlayerControl.ResumeFailed(interaction, e)

    ##############################################

    @app_commands.command(name='skip', description='⏩ | 跳過目前播放的歌曲')
    async def skip(self, interaction: discord.Interaction):
        try:
            await self._skip(interaction.guild)
            self.ui.PlayerControl.SkipProceed(interaction.guild.id)
            if not interaction.response.is_done():
                await interaction.response.send_message("⠀")
                tmpmsg = await interaction.original_response()
                await tmpmsg.delete()
        except Exception as e:
            await self.ui.PlayerControl.SkipFailed(interaction, e)

    ##############################################
    
    @app_commands.command(name='np', description='▶️ | 查看現在在播放什麼!')
    async def nowplaying(self, interaction: discord.Interaction):
        await self.ui.PlayerControl.NowPlaying(interaction)

    ##############################################

    @app_commands.command(name='stop', description='⏹️ | 停止音樂並清除待播清單')
    async def stop(self, interaction: discord.Interaction):
        try:
            await self._stop(interaction.guild)
            await self.ui.PlayerControl.StopSucceed(interaction)
        except Exception as e:
            await self.ui.PlayerControl.StopFailed(interaction, e)

    ##############################################

    @app_commands.command(name='seek', description='⏲️ | 跳轉你想要聽的地方')
    @app_commands.describe(timestamp='目標時間 (時間戳格式 0:20) 或 (秒數 20)')
    @app_commands.rename(timestamp='目標時間')
    async def seek(self, interaction, timestamp: str):
        try:
            if isinstance(timestamp, str):
                tmp = map(int, reversed(timestamp.split(":")))
                timestamp = 0
                for idx, val in enumerate(tmp):
                    timestamp += (60 ** idx) * val
            await self._seek(interaction.guild, timestamp)
            await self.ui.PlayerControl.SeekSucceed(interaction, timestamp)
        except ValueError as e:  # For ignoring string with ":" like "o:ro"
            await self.ui.PlayerControl.SeekFailed(interaction, e)
            return

    ##############################################

    @app_commands.command(name='restart', description='🔁 | 重頭開始播放目前的歌曲')
    async def restart(self, interaction: discord.Interaction):
        try:
            await self._seek(0)
            await self.ui.PlayerControl.ReplaySucceed(interaction)
        except Exception as e:
            await self.ui.PlayerControl.ReplayFailed(interaction, e)

    ##############################################

    @app_commands.command(name='loop', description='🔂 | 循環播放目前的歌曲')
    @app_commands.describe(times='重複播放次數 (不填寫次數以啟動無限次數循環)')
    @app_commands.rename(times='重複播放次數')
    async def single_loop(self, interaction: discord.Interaction, times: int=INF):
        voice_client: wavelink.Player = interaction.guild.voice_client
        if not isinstance(times, int) or voice_client is None or len(self._playlist[interaction.guild.id].order) == 0:
            return await self.ui.PlayerControl.SingleLoopFailed(interaction)
        self._playlist.single_loop(interaction.guild.id, times)
        await self.ui.PlayerControl.LoopSucceed(interaction)

    ##############################################

    @app_commands.command(name='shuffle', description='🔀 | 隨機排序目前的待播清單')
    async def shuffle(self, interaction: discord.Interaction):
        if len(self._playlist[interaction.guild.id]) < 2:
            await self.ui.PlayerControl.ShuffleFailed(interaction)
        self._playlist[interaction.guild.id].shuffle()

    ##############################################

    @app_commands.command(name='queueloop', description='🔁 | 循環播放目前的待播清單')
    async def playlist_loop(self, interaction: discord.Interaction):
        voice_client: wavelink.Player = interaction.guild.voice_client
        if voice_client is None or len(self._playlist[interaction.guild.id].order) == 0:
            return await self.ui.PlayerControl.SingleLoopFailed(interaction)
        self._playlist.playlist_loop(interaction.guild.id)
        await self.ui.PlayerControl.LoopSucceed(interaction)

    ##############################################

    @app_commands.command(name='queue', description='ℹ️ | 列出目前的待播清單')
    async def show_queue(self, interaction: discord.Interaction):
        await self.ui.Queue.ShowQueue(interaction)

    ##############################################    

    @app_commands.command(name='remove', description='🗑️ | 刪除待播清單中的一首歌')
    @app_commands.describe(idx='欲刪除歌曲之位置 (可用 %queue 或 /queue 得知位置代號)')
    @app_commands.rename(idx='刪除歌曲位置')
    async def remove(self, interaction: discord.Interaction, idx: int):
        try:
            if self._playlist[interaction.guild.id].order[idx].suggested:
                await self.ui.QueueControl.RemoveFailed(interaction, '不能移除建議歌曲')
                return
            removed = self._playlist[interaction.guild.id].order[idx]
            self._playlist.pop(interaction.guild.id, idx)
            await self.ui.QueueControl.RemoveSucceed(interaction, removed, idx)
        except (IndexError, TypeError) as e:
            await self.ui.QueueControl.RemoveFailed(interaction, e)

   ##############################################

    @app_commands.command(name='swap', description='🔄 | 交換待播清單中兩首歌的位置')
    @app_commands.describe(idx1='歌曲1 位置 (可用 %queue 或 /queue 得知位置代號)', idx2='歌曲2 位置 (可用 %queue 或 /queue 得知位置代號)')
    @app_commands.rename(idx1='歌曲1位置', idx2='歌曲2位置')
    async def swap(self, interaction: discord.Interaction, idx1: int, idx2: int):
        try:
            if self._playlist[interaction.guild.id].order[idx1].suggested or self._playlist[interaction.guild.id].order[idx2].suggested:
                await self.ui.QueueControl.SwapFailed(interaction, '不能移動建議歌曲')
                return
            self._playlist.swap(interaction.guild.id, idx1, idx2)
            await self.ui.QueueControl.Embed_SwapSucceed(interaction, idx1, idx2)
        except (IndexError, TypeError) as e:
            await self.ui.QueueControl.SwapFailed(interaction, e)

    ##############################################

    @app_commands.command(name='move', description='🔄 | 移動待播清單中一首歌的位置')
    @app_commands.describe(origin='原位置 (可用 %queue 或 /queue 得知位置代號)', new='目標位置 (可用 %queue 或 /queue 得知位置代號)')
    @app_commands.rename(origin='原位置', new='目標位置')
    async def move_to(self, interaction: discord.Interaction, origin: int, new: int):
        try:
            if self._playlist[interaction.guild.id].order[origin].suggested or self._playlist[interaction.guild.id].order[new].suggested:
                await self.ui.QueueControl.MoveToFailed(interaction, '不能移動建議歌曲')
                return
            self._playlist.move_to(interaction.guild.id, origin, new)
            await self.ui.QueueControl.MoveToSucceed(interaction, origin, new)
        except (IndexError, TypeError) as e:
            await self.ui.QueueControl.MoveToFailed(interaction, e)

    ##############################################

    async def process(self, interaction: discord.Interaction,
                            trackinfo: Union[
                                wavelink.YouTubeTrack,
                                wavelink.YouTubeMusicTrack,
                                wavelink.SoundCloudTrack,
                                wavelink.YouTubePlaylist
                            ]):

        # Call search function
        try: 
            if isinstance(trackinfo, list):
                is_search = trackinfo[-1] == 'Search'
                is_ytpl = trackinfo[-1] == 'YTPL'
                if trackinfo[-1] == 'Search' or trackinfo[-1] == 'YTPL':
                    trackinfo.pop(-1)
            else:
                is_search = False
                is_ytpl = False
            await self._search(interaction.guild, trackinfo, requester=interaction.user)
        except Exception as e:
            # If search failed, sent to handler
            await self.ui.Search.SearchFailed(interaction, e)
            return
        # If queue has more than 1 songs, then show the UI
        await self.ui.Queue.Embed_AddedToQueue(interaction, trackinfo, requester=interaction.user, is_search=is_search, is_ytpl=is_ytpl)

    async def play(self, interaction: discord.Interaction, trackinfo: Union[
                                wavelink.GenericTrack,
                                wavelink.SoundCloudTrack,
                            ]):
        # Try to make bot join author's channel
        if isinstance(trackinfo, list):
            if trackinfo[-1] != 'Search' and trackinfo[-1] != "YTPL":
                trackinfo.pop(-1)
        voice_client: wavelink.Player = interaction.guild.voice_client
        if isinstance(voice_client, wavelink.Player) and \
            interaction.user.voice is None:
            pass
        elif not isinstance(voice_client, wavelink.Player) or \
                voice_client.channel != interaction.user.voice.channel:
            await self.join(interaction)
            voice_client = interaction.guild.voice_client
            if not isinstance(voice_client, wavelink.Player):
                return

        # Start search process
        await self.process(interaction, trackinfo)

        await self._play(interaction.guild, interaction.channel)
        if not interaction.response.is_done():
            await interaction.response.send_message("⠀")  
            tmpmsg = await interaction.original_response()
            await tmpmsg.delete()  

    @app_commands.command(name='play', description='🎶 | 想聽音樂？來這邊點歌吧~')
    @app_commands.describe(search='欲播放之影片網址或關鍵字 (支援 SoundCloud / Spotify / BiliBili(單曲))')
    @app_commands.rename(search='影片網址或關鍵字')
    async def _i_play(self, interaction: discord.Interaction, search: str):
        if validators.url(search):
            if "list" in search and "watch" in search and ("youtube" in search or "youtu.be" in search):
                if self[interaction.guild.id].multitype_remembered:
                    tracks = await self._get_track(interaction, search, self[interaction.guild.id].multitype_choice)   
                else:
                    await self.ui.PlayerControl.MultiTypeNotify(interaction, search)
                    return
            else:
                tracks = await self._get_track(interaction, search)
            if tracks == "NodeDisconnected":
                await self.ui.ExceptionHandler.NodeDisconnectedMessage()
                return
            await self.play(interaction, tracks)
        else:
            tracks = await self._get_track(interaction, search)
            await self.ui.PlayerControl.SearchResultSelection(interaction, tracks)

    async def _get_bilibili_track(self, interaction: discord.Interaction, search: str):
        searchnode = wavelink.NodePool.get_node(id="SearchNode")
        if "BV" in search and "https://www.bilibili.com/" not in search:
            vid = search
        else:
            try:
                int(search)
                is_aid = True
            except:
                is_aid = False
            if is_aid:
                vid = bilibili.aid2bvid(search)
            else:
                if "b23.tv" in search:
                    search = bilibili.get_real_url(search, self._bilibilic)
                
                url_split = search.split("/")
                vid = url_split[4]
        
        v_data = bilibili.video.Video(bvid=vid, credential=self._bilibilic)
        download_url_data = await v_data.get_download_url(0)
        detector = bilibili.video.VideoDownloadURLDataDetecter(download_url_data)

        data = detector.detect()
        for t in data:
            if isinstance(t, bilibili.video.AudioStreamDownloadURL):
                raw_url = t.url.replace("&", "%26")
                break
            else:
                raw_url = None
        
        if raw_url == None:
            return None

        trackinfo = await searchnode.get_tracks(wavelink.GenericTrack, raw_url)
        track = trackinfo[0]
        vinfo = await v_data.get_info()
        track.author = vinfo['owner']['name']
        track.duration = vinfo['duration'] * 1000
        track.identifier = vinfo['bvid']
        track.is_seekable = True
        track.title = vinfo['title']

        return track

    async def _get_track(self, interaction: discord.Interaction, search: str, choice="videoonly"):
        searchnode = wavelink.NodePool.get_node(id="SearchNode")
        if searchnode.status != wavelink.NodeStatus.CONNECTED:
            return "NodeDisconnected"
        await interaction.response.defer(ephemeral=True ,thinking=True)
        if ('bilibili' in search or 'b23.tv' in search) and validators.url(search):
            trackinfo = await self._get_bilibili_track(interaction, search)
        elif 'spotify' in search and validators.url(search):
            if 'track' in search:
                searchtype = spotify.SpotifySearchType.track
            elif 'album' in search:
                searchtype = spotify.SpotifySearchType.album
            else:
                searchtype = spotify.SpotifySearchType.playlist
            
            if ('album' in search or 'artist' in search or 'playlist' in search):
                self.ui_guild_info(interaction.guild.id).processing_msg = await self.ui.Search.SearchInProgress(interaction)

            searchnode = wavelink.NodePool.get_node(id="SearchNode")
            tracks = await spotify.SpotifyTrack.search(search, node=searchnode, type=searchtype, return_first=True)

            if tracks is None:
                trackinfo = None
            else:
                trackinfo = self._playlist.spotify_info_process(search, tracks, searchtype)
        else:
            if "https://www.youtube.com/" in search or "https://youtu.be/" in search:
                youtube_url = True
                if "list" in search:
                    extract = search.split('&')
                    if choice == 'videoonly':
                        url = extract[0]
                    elif choice == 'playlist':
                        url = f'https://www.youtube.com/playlist?{extract[1]}'
                    else:
                        url = search
                else:
                    url = search
            else:
                youtube_url = False
                url = search

            trackinfo = []
            if choice == 'playlist' or 'list' in search:
                data = await wavelink.YouTubePlaylist.search(search, node=searchnode)
                if data is not None:
                    trackinfo = data
            else:
                for trackmethod in [wavelink.YouTubeMusicTrack, wavelink.YouTubeTrack, wavelink.SoundCloudTrack]:
                    try:
                        # SearchableTrack.search(query, node, return_first)
                        data = await trackmethod.search(url, node=searchnode)
                        if data is not None:
                            trackinfo.extend(data)
                            if youtube_url:
                                break
                    except Exception:
                        # When there is no result for provided method
                        # Then change to next method to search
                        pass
        
        if trackinfo is None:
            await self.ui.Search.SearchFailed(interaction, search)
            return None
        elif not isinstance(trackinfo, Union[SpotifyAlbum, SpotifyPlaylist, wavelink.YouTubePlaylist, wavelink.GenericTrack]):
            if len(trackinfo) == 0:
                await self.ui.Search.SearchFailed(interaction, search)
                return None

        if isinstance(trackinfo, Union[SpotifyAlbum, SpotifyPlaylist, wavelink.YouTubePlaylist]):
            tracklist = trackinfo.tracks
            if isinstance(trackinfo, wavelink.YouTubePlaylist):
                tracklist.append('YTPL')
        elif isinstance(trackinfo, wavelink.GenericTrack):
            pass
        else:
            tracklist = trackinfo
            tracklist.append('YTorSC')

        if isinstance(trackinfo, wavelink.GenericTrack):
            trackinfo.suggested = False
            trackinfo.audio_source = "bilibili"
            tracklist = trackinfo
        else:
            for track in tracklist:
                if track == "YTorSC" or track == "YTPL":
                    break
                track.suggested = False
                if isinstance(track, wavelink.YouTubeTrack):
                    track.audio_source = "youtube"
                else:
                    track.audio_source = "soundcloud"

        return tracklist

    ##############################

    async def _refresh_msg(self, guild):
        await asyncio.sleep(3)
        await self.ui._InfoGenerator._UpdateSongInfo(guild.id)

    async def _mainloop(self, guild: discord.Guild):
        while len(self._playlist[guild.id].order):
            await asyncio.sleep(0.2)

            self._playlist[guild.id]._refresh_msg_task = self[guild.id]._refresh_msg_task

            await asyncio.wait_for(self._playlist.process_suggestion(guild, self.ui_guild_info(guild.id)), None)
            
            # Sync the task status with playlist
            self[guild.id]._refresh_msg_task = self._playlist[guild.id]._refresh_msg_task
            
            voice_client: wavelink.Player = guild.voice_client
            song = self._playlist[guild.id].current()
            try:
                try:
                    await voice_client.play(song)
                    self.ui_guild_info(guild.id).previous_title = song.title
                    await self.ui.PlayerControl.PlayingMsg(self[guild.id].text_channel)
                    self[guild.id]._refresh_msg_task = self._playlist[guild.id]._refresh_msg_task = self.bot.loop.create_task(self._refresh_msg(guild))
                except Exception as e:
                    try:
                        await voice_client.play(song)
                        self.ui_guild_info(guild.id).previous_title = song.title
                        await self.ui.PlayerControl.PlayingMsg(self[guild.id].text_channel)
                        self[guild.id]._refresh_msg_task = self._playlist[guild.id]._refresh_msg_task = self.bot.loop.create_task(self._refresh_msg(guild))
                    except:
                        await self.ui.PlayerControl.PlayingError(self[guild.id].text_channel, e)
                        pass

                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(0.1)
            finally:
                self._playlist.rule(guild.id, self.ui_guild_info(guild.id).skip)
                await asyncio.sleep(0.2)
                if self[guild.id]._refresh_msg_task is not None:
                    self[guild.id]._refresh_msg_task.cancel()
                    self[guild.id]._refresh_msg_task = self._playlist[guild.id]._refresh_msg_task = None
        await self.ui.PlayerControl.DonePlaying(self[guild.id].text_channel)
        
    @commands.Cog.listener(name='on_voice_state_update')
    async def end_session(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.id != self.bot.user.id or not (before.channel is not None and after.channel is None):
            return 
        guild = member.guild
        channel = self[guild.id].text_channel
        if self[guild.id]._timer is not None and self[guild.id]._timer.done():
            await self.ui.Leave.LeaveOnTimeout(channel)
        elif after.channel is None:
            await self._leave(member.guild)
        self._cleanup(guild)

    # Error handler
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            return
        print(error)
        await ctx.send(f'''
            **:no_entry: | 失敗 | UNKNOWNERROR**
            執行指令時發生了一點未知問題，請稍候再嘗試一次
            --------
            技術資訊:
            {error}
            --------
            *若您覺得有Bug或錯誤，請參照上方資訊及代碼，並到我們的群組回報*
        ''', view=self.groupbutton) 

    @commands.Cog.listener('on_voice_state_update')
    async def _pause_on_being_alone(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        try:
            voice_client: wavelink.Player = member.guild.voice_client
            if len(voice_client.channel.members) == 1 and member != self.bot.user:
                if not voice_client.is_paused():
                    await self.ui.PlayerControl.PauseOnAllMemberLeave(self[member.guild.id].text_channel, member.guild.id)
                    await self._pause(member.guild)
                else:
                    self.ui_guild_info(member.guild.id).playinfo_view.playorpause.disabled = True
                    self.ui_guild_info(member.guild.id).playinfo_view.playorpause.style = discord.ButtonStyle.gray
                    await self.ui_guild_info(member.guild.id).playinfo.edit(view=self.ui_guild_info(member.guild.id).playinfo_view)
            elif len(voice_client.channel.members) > 1 and voice_client.is_paused() and member != self.bot.user and self.ui_guild_info(member.guild.id).playinfo_view.playorpause.disabled:
                self.ui_guild_info(member.guild.id).playinfo_view.playorpause.disabled = False
                self.ui_guild_info(member.guild.id).playinfo_view.playorpause.style = discord.ButtonStyle.blurple
                await self.ui_guild_info(member.guild.id).playinfo.edit(view=self.ui_guild_info(member.guild.id).playinfo_view)
        except:
            pass
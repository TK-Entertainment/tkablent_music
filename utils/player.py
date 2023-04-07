from http import client
import random
from typing import *
import asyncio, json, os

import discord
from discord.ext import commands
from discord import VoiceClient, app_commands

import wavelink
import spotipy
import logging
from ytmusicapi import YTMusic
from spotipy.oauth2 import SpotifyClientCredentials
from wavelink.ext import spotify
from .playlist import Playlist, SpotifyAlbum, SpotifyPlaylist, LoopState
from .command import Command

INF = int(1e18)

class GuildInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.text_channel: discord.TextChannel = None
        self._task: asyncio.Task = None
        self._refresh_msg_task: asyncio.Task = None
        self._timer: asyncio.Task = None
        self._dsa: bool = None

    @property
    def data_survey_agreement(self):
        if self._dsa is None:
            self._dsa = self.fetch('dsa')
        return self._dsa

    @data_survey_agreement.setter
    def data_survey_agreement(self, value: bool):
        self._dsa(self, value)
        self.update("dsa", value)

    def fetch(self, key: str) -> not None:
        '''fetch from database'''

        with open(r'utils\data.json', 'r') as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None or data[str(self.guild_id)].get(key) is None:
            return data['default'][key]
        return data[str(self.guild_id)][key]

    def update(self, key: str, value: str) -> None:
        '''update database'''

        with open(r'utils\data.json', 'r') as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None:
            data[str(self.guild_id)] = dict()
        data[str(self.guild_id)][key] = value
        with open(r'utils\data.json', 'w') as f:
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

        self._spotify = spotify.SpotifyClient(client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET)

        await wavelink.NodePool.connect(
            client=self.bot,
            nodes=[mainplayhost, altplayhost, searchhost],
            spotify=self._spotify
        )

        self.bot.loop.create_task(self.reconnect_node())

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

    async def help(self, command: Union[commands.Context, discord.Interaction]):
        command: Command = Command(command)
        await self.ui.Help.Help(command)

    @app_commands.command(name='help', description="❓ | 不知道怎麼使用我嗎？來這裡就對了~")
    async def _i_help(self, interaction: discord.Interaction):
        await self.help(interaction)

    ##############################################

    async def ensure_stage_status(self, command: Command):
        '''a helper function for opening a stage'''

        if not isinstance(command.author.voice.channel, discord.StageChannel):
            return

        bot_itself: discord.Member = await command.guild.fetch_member(self.bot.user.id)
        auto_stage_vaildation = self.auto_stage_available(command.guild.id)
        
        if command.author.voice.channel.instance is None:
            await self.ui.Stage.CreateStageInstance(command, command.guild.id)
        
        if auto_stage_vaildation and bot_itself.voice.suppress:
            try: 
                await bot_itself.edit(suppress=False)
            except: 
                auto_stage_vaildation = False

    async def rejoin(self, command: Command):
        voice_client: wavelink.Player = command.guild.voice_client
        # Get the bot former playing state
        former: discord.VoiceChannel = voice_client.channel
        former_state: bool = voice_client.is_paused()
        # To determine is the music paused before rejoining or not
        if not former_state: 
            await self._pause(command.guild)
        # Moving itself to author's channel
        await voice_client.move_to(command.author.voice.channel)
        if isinstance(command.author.voice.channel, discord.StageChannel):
            await self.ensure_stage_status(command)

        # If paused before rejoining, resume the music
        if not former_state: 
            await self._resume(command.guild)
        # Send a rejoin message
        await self.ui.Join.RejoinNormal(command)
        # If the former channel is a discord.StageInstance which is the stage
        # channel with topics, end that stage instance
        if isinstance(former, discord.StageChannel) and \
                isinstance(former.instance, discord.StageInstance):
            await self.ui.Stage.EndStage(command.guild.id)

    async def join(self, command):
        if not isinstance(command, Command):
            command: Optional[Command] = Command(command)

        voice_client: wavelink.Player = command.guild.voice_client
        if isinstance(voice_client, wavelink.Player):
            if voice_client.channel != command.author.voice.channel:
                await self.rejoin(command)
            else:
                # If bot joined the same channel, send a message to notice user
                await self.ui.Join.JoinAlready(command)
            return
        try:
            await self._join(command.author.voice.channel)
            voice_client: wavelink.Player = command.guild.voice_client
            if isinstance(voice_client.channel, discord.StageChannel):
                await self.ensure_stage_status(command)
                await self.ui.Join.JoinStage(command, command.guild.id)
            else:
                await self.ui.Join.JoinNormal(command)
        except Exception as e:
            await self.ui.Join.JoinFailed(command, e)
    
    @app_commands.command(name='join', description='📥 | 將我加入目前您所在的頻道')
    async def _i_join(self, interaction: discord.Interaction):
        await self.join(interaction)

    ##############################################

    async def leave(self, command):
        if not isinstance(command, Command):
            command: Optional[Command] = Command(command)

        voice_client: wavelink.Player = command.guild.voice_client
        try:
            if isinstance(voice_client.channel, discord.StageChannel) and \
                    isinstance(voice_client.channel.instance, discord.StageInstance):
                await self.ui.Stage.EndStage(command.guild.id)
            await self._leave(command.guild)
            await self.ui.Leave.LeaveSucceed(command)
        except Exception as e:
            await self.ui.Leave.LeaveFailed(command, e)

    @app_commands.command(name='leave', description='📤 | 讓我從目前您所在的頻道離開')
    async def _i_leave(self, interaction: discord.Interaction):
        await self.leave(interaction)

    ##############################################

    async def pause(self, command):
        if not isinstance(command, Command):
            command: Optional[Command] = Command(command)
        try:
            await self._pause(command.guild)
            await self.ui.PlayerControl.PauseSucceed(command, command.guild.id)
        except Exception as e:
            await self.ui.PlayerControl.PauseFailed(command, e)

    @app_commands.command(name='pause', description='⏸️ | 暫停目前播放的音樂')
    async def _i_pause(self, interaction: discord.Interaction):
        await self.pause(interaction)

    ##############################################

    async def resume(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            if isinstance(command.channel, discord.StageChannel):
                await self.ensure_stage_status(command)
            await self._resume(command.guild)
            await self.ui.PlayerControl.ResumeSucceed(command, command.guild.id)
        except Exception as e:
            await self.ui.PlayerControl.ResumeFailed(command, e)

    @app_commands.command(name='resume', description='▶️ | 繼續播放目前暫停的歌曲')
    async def _i_resume(self, interaction: discord.Interaction):
        await self.resume(interaction)

    ##############################################

    async def skip(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            await self._skip(command.guild)
            self.ui.PlayerControl.SkipProceed(command.guild.id)
            if command.is_response() is not None and not command.is_response():
                await command.send("⠀")
        except Exception as e:
            await self.ui.PlayerControl.SkipFailed(command, e)
    
    @app_commands.command(name='skip', description='⏩ | 跳過目前播放的歌曲')
    async def _i_skip(self, interaction: discord.Interaction):
        await self.skip(interaction)

    ##############################################

    async def nowplaying(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        await self.ui.PlayerControl.NowPlaying(command)

    @app_commands.command(name='np', description='▶️ | 查看現在在播放什麼!')
    async def _i_nowplaying(self, interaction: discord.Interaction):
        await self.nowplaying(interaction)

    ##############################################

    async def stop(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            await self._stop(command.guild)
            await self.ui.PlayerControl.StopSucceed(command)
        except Exception as e:
            await self.ui.PlayerControl.StopFailed(command, e)

    @app_commands.command(name='stop', description='⏹️ | 停止音樂並清除待播清單')
    async def _i_stop(self, interaction: discord.Interaction):
        await self.stop(interaction)

    ##############################################

    async def seek(self, command, timestamp: Union[float, str]):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            if isinstance(timestamp, str):
                tmp = map(int, reversed(timestamp.split(":")))
                timestamp = 0
                for idx, val in enumerate(tmp):
                    timestamp += (60 ** idx) * val
            await self._seek(command.guild, timestamp)
            await self.ui.PlayerControl.SeekSucceed(command, timestamp)
        except ValueError as e:  # For ignoring string with ":" like "o:ro"
            await self.ui.PlayerControl.SeekFailed(command, e)
            return

    @app_commands.command(name='seek', description='⏲️ | 跳轉你想要聽的地方')
    @app_commands.describe(timestamp='目標時間 (時間戳格式 0:20) 或 (秒數 20)')
    @app_commands.rename(timestamp='目標時間')
    async def _i_seek(self, interaction: discord.Interaction, timestamp: str):
        await self.seek(interaction, timestamp)

    ##############################################

    async def restart(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            await self._seek(0)
            await self.ui.PlayerControl.ReplaySucceed(command)
        except Exception as e:
            await self.ui.PlayerControl.ReplayFailed(command, e)

    @app_commands.command(name='restart', description='🔁 | 重頭開始播放目前的歌曲')
    async def _i_restart(self, interaction: discord.Interaction):
        await self.restart(interaction)

    ##############################################

    async def single_loop(self, command, times: Union[int, str]=INF):
        if not isinstance(command, Command):
            command: Command = Command(command)
        if not isinstance(times, int):
            return await self.ui.PlayerControl.SingleLoopFailed(command)
        self._playlist.single_loop(command.guild.id, times)
        await self.ui.PlayerControl.LoopSucceed(command)

    @app_commands.command(name='loop', description='🔂 | 循環播放目前的歌曲')
    @app_commands.describe(times='重複播放次數 (不填寫次數以啟動無限次數循環)')
    @app_commands.rename(times='重複播放次數')
    async def _i_single_loop(self, interaction: discord.Interaction, times: int=INF):
        await self.single_loop(interaction, times)

    ##############################################

    async def shuffle(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        if len(self._playlist[command.guild.id]) < 2:
            await self.ui.PlayerControl.ShuffleFailed(command)
        self._playlist[command.guild.id].shuffle()

    @app_commands.command(name='shuffle', description='🔀 | 隨機排序目前的待播清單')
    async def _i_shuffle(self, interaction: discord.Interaction):
        await self.shuffle(interaction)

    ##############################################

    async def playlist_loop(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        self._playlist.playlist_loop(command.guild.id)
        await self.ui.PlayerControl.LoopSucceed(command)

    @app_commands.command(name='queueloop', description='🔁 | 循環播放目前的待播清單')
    async def _i_playlist_loop(self, interaction: discord.Interaction):
        await self.playlist_loop(interaction)

    ##############################################

    async def show_queue(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        await self.ui.Queue.ShowQueue(command)

    @app_commands.command(name='queue', description='ℹ️ | 列出目前的待播清單')
    async def _i_show_queue(self, interaction: discord.Interaction):
        await self.show_queue(interaction)

    ##############################################    

    async def remove(self, command, idx: Union[int, str]):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            if self._playlist[command.guild.id].order[idx].suggested:
                await self.ui.QueueControl.RemoveFailed(command, '不能移除建議歌曲')
                return
            removed = self._playlist[command.guild.id].order[idx]
            self._playlist.pop(command.guild.id, idx)
            await self.ui.QueueControl.RemoveSucceed(command, removed, idx)
        except (IndexError, TypeError) as e:
            await self.ui.QueueControl.RemoveFailed(command, e)

    @app_commands.command(name='remove', description='🗑️ | 刪除待播清單中的一首歌')
    @app_commands.describe(idx='欲刪除歌曲之位置 (可用 %queue 或 /queue 得知位置代號)')
    @app_commands.rename(idx='刪除歌曲位置')
    async def _i_remove(self, interaction: discord.Interaction, idx: int):
        await self.remove(interaction, idx)

   ##############################################

    async def swap(self, command, idx1: Union[int, str], idx2: Union[int, str]):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            if self._playlist[command.guild.id].order[idx1].suggested or self._playlist[command.guild.id].order[idx2].suggested:
                await self.ui.QueueControl.SwapFailed(command, '不能移動建議歌曲')
                return
            self._playlist.swap(command.guild.id, idx1, idx2)
            await self.ui.QueueControl.Embed_SwapSucceed(command, idx1, idx2)
        except (IndexError, TypeError) as e:
            await self.ui.QueueControl.SwapFailed(command, e)

    @app_commands.command(name='swap', description='🔄 | 交換待播清單中兩首歌的位置')
    @app_commands.describe(idx1='歌曲1 位置 (可用 %queue 或 /queue 得知位置代號)', idx2='歌曲2 位置 (可用 %queue 或 /queue 得知位置代號)')
    @app_commands.rename(idx1='歌曲1位置', idx2='歌曲2位置')
    async def _i_swap(self, interaction: discord.Interaction, idx1: int, idx2: int):
        await self.swap(interaction, idx1, idx2)
    ##############################################

    async def move_to(self, command, origin: Union[int, str], new: Union[int, str]):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            if self._playlist[command.guild.id].order[origin].suggested or self._playlist[command.guild.id].order[new].suggested:
                await self.ui.QueueControl.MoveToFailed(command, '不能移動建議歌曲')
                return
            self._playlist.move_to(command.guild.id, origin, new)
            await self.ui.QueueControl.MoveToSucceed(command, origin, new)
        except (IndexError, TypeError) as e:
            await self.ui.QueueControl.MoveToFailed(command, e)

    @app_commands.command(name='move', description='🔄 | 移動待播清單中一首歌的位置')
    @app_commands.describe(origin='原位置 (可用 %queue 或 /queue 得知位置代號)', new='目標位置 (可用 %queue 或 /queue 得知位置代號)')
    @app_commands.rename(origin='原位置', new='目標位置')
    async def _i_move_to(self, interaction: discord.Interaction, origin: int, new: int):
        await self.move_to(interaction, origin, new)

    ##############################################

    async def process(self, command: Command,
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
                trackinfo.pop(-1)
            else:
                is_search = False
            await self._search(command.guild, trackinfo, requester=command.author)
        except Exception as e:
            # If search failed, sent to handler
            await self.ui.Search.SearchFailed(command, e)
            return
        # If queue has more than 1 songs, then show the UI
        await self.ui.Queue.Embed_AddedToQueue(command, trackinfo, requester=command.author, is_search=is_search)
    
    async def play(self, command, trackinfo: Union[
                                wavelink.GenericTrack,
                                wavelink.SoundCloudTrack,
                            ]):
        if not isinstance(command, Command):
            command: Command = Command(command)
        # Try to make bot join author's channel
        if isinstance(trackinfo, list):
            if trackinfo[-1] != 'Search':
                trackinfo.pop(-1)
        if command.command_type == 'Context':
            await command.channel.typing()
        voice_client: wavelink.Player = command.guild.voice_client
        if isinstance(voice_client, wavelink.Player) and \
            command.author.voice is None:
            pass
        elif not isinstance(voice_client, wavelink.Player) or \
                voice_client.channel != command.author.voice.channel:
            await self.join(command)
            voice_client = command.guild.voice_client
            if not isinstance(voice_client, wavelink.Player):
                return

        # Start search process
        await self.process(command, trackinfo)

        await self._play(command.guild, command.channel)
        if command.command_type == 'Interaction' and command.is_response is not None and not command.is_response():
            await command.send("⠀")    

    @app_commands.command(name='play', description='🎶 | 想聽音樂？來這邊點歌吧~')
    @app_commands.describe(search='欲播放之影片網址或關鍵字 (支援 SoundCloud / Spotify)')
    @app_commands.rename(search='影片網址或關鍵字')
    async def _i_play(self, interaction: discord.Interaction, search: str):
        command: Command = Command(interaction)
        if "youtube" in search or 'youtu.be' in search:
            await self.ui.Search.YoutubeFuckedUp(command)
            return
        tracks = await self._get_track(command, search)
        if tracks == "NodeDisconnected":
            await self.ui.ExceptionHandler.NodeDisconnectedMessage()
        if isinstance(tracks, Union[SpotifyAlbum, SpotifyPlaylist]):
            await self.play(command, tracks)
        else:
            await self.ui.PlayerControl.SearchResultSelection(command, tracks)

    async def _get_track(self, command: Command, search: str):
        searchnode = wavelink.NodePool.get_node(id="SearchNode")
        if searchnode.status != wavelink.NodeStatus.CONNECTED:
            return "NodeDisconnected"
        if command.command_type == 'Interaction':
            await command.defer(ephemeral=True ,thinking=True)
        if 'spotify' in search:
            if 'track' in search:
                searchtype = spotify.SpotifySearchType.track
            elif 'album' in search:
                searchtype = spotify.SpotifySearchType.album
            else:
                searchtype = spotify.SpotifySearchType.playlist
            
            if ('album' in search or 'artist' in search or 'playlist' in search):
                self.ui_guild_info(command.guild.id).processing_msg = await self.ui.Search.SearchInProgress(command)

            searchnode = wavelink.NodePool.get_node(id="SearchNode")
            tracks = await spotify.SpotifyTrack.search(search, node=searchnode, type=searchtype, return_first=True)

            if tracks is None:
                trackinfo = None
            else:
                trackinfo = self._playlist.spotify_info_process(search, tracks, searchtype)
        else:
            trackinfo = []
            for trackmethod in [wavelink.YouTubeTrack, wavelink.SoundCloudTrack]:
                try:
                    # SearchableTrack.search(query, node, return_first)
                    data = await trackmethod.search(search, node=searchnode)
                    if data is not None:
                        trackinfo.extend(data)
                except Exception:
                    # When there is no result for provided method
                    # Then change to next method to search
                    pass
        
        if trackinfo is None:
            await self.ui.Search.SearchFailed(command, search)
            return None
        elif not isinstance(trackinfo, Union[SpotifyAlbum, SpotifyPlaylist]):
            if len(trackinfo) == 0:
                await self.ui.Search.SearchFailed(command, search)
                return None

        if isinstance(trackinfo, Union[SpotifyAlbum, SpotifyPlaylist]):
            tracklist = trackinfo.tracks
        else:
            tracklist = trackinfo
            trackinfo.append('YTorSC')

        for track in tracklist:
            if track == "YTorSC":
                break
            track.suggested = False
            if isinstance(track, wavelink.YouTubeTrack):
                track.audio_source = "youtube"
            else:
                track.audio_source = "soundcloud"

        return trackinfo

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
                    print(e)
                    if isinstance(e, wavelink.exceptions.InvalidLavalinkResponse):
                        await self._node_reconnection()
                        try:
                            await voice_client.play(song)
                            self.ui_guild_info(guild.id).previous_title = song.title
                            await self.ui.PlayerControl.PlayingMsg(self[guild.id].text_channel)
                            self[guild.id]._refresh_msg_task = self._playlist[guild.id]._refresh_msg_task = self.bot.loop.create_task(self._refresh_msg(guild))
                        except:
                            await self.ui.PlayerControl.PlayingError(self[guild.id].text_channel, e)
                            pass
                    else:
                        await self.ui.PlayerControl.PlayingError(self[guild.id].text_channel, e)

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
    
    async def reconnect_node(self):
        while True:
            await asyncio.sleep(5)
            await self._node_reconnection()


    async def _node_reconnection(self):
        for nodeid in ['US_PlayBackNode', 'TW_PlayBackNode', 'SearchNode']:
            try:
                node = wavelink.NodePool.get_node(id=nodeid)
            except wavelink.InvalidNode:
                TW_HOST = os.getenv('WAVELINK_TW_HOST')
                US_HOST = os.getenv('WAVELINK_US_HOST')
                SEARCH_HOST = os.getenv('WAVELINK_SEARCH_HOST')
                PORT = os.getenv('WAVELINK_PORT')
                SEARCH_PORT = os.getenv('WAVELINK_SEARCH_PORT')
                PASSWORD = os.getenv('WAVELINK_PWD')

                match nodeid:
                    case 'US_PlayBackNode':
                        node = wavelink.Node(
                            id="US_PlayBackNode",
                            uri=f"http://{US_HOST}:{PORT}",
                            use_http=True,
                            password=PASSWORD,
                        )
                    case 'TW_PlayBackNode':
                        node = wavelink.Node(
                                id="TW_PlayBackNode",
                                uri=f"http://{TW_HOST}:{PORT}",
                                use_http=True,
                                password=PASSWORD,
                            )
                    case 'SearchNode':
                        node = wavelink.Node(
                            id="SearchNode",
                            uri=f"http://{SEARCH_HOST}:{SEARCH_PORT}",
                            use_http=True,
                            password=PASSWORD,
                        )
            if node.status != wavelink.NodeStatus.CONNECTED:
                await wavelink.NodePool.connect(
                    client=self.bot, 
                    nodes=[node], 
                    spotify=self._spotify)
                print(f"[Debug] Reconnected {node.id}")

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
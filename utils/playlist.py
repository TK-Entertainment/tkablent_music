from typing import *
from enum import Enum, auto

import asyncio

import disnake
from disnake import FFmpegPCMAudio, PCMVolumeTransformer, TextChannel, VoiceClient

from .database import DatabaseSession

from .ytdl import YTDL

INF = int(1e18)

class SeekError(Exception): ...
class OutOfBound(Exception): ...

ytdl = YTDL()
# db = _database()

class Song:
    
    title: str
    author: str
    channel_url: str
    watch_url: str
    thumbnail_url: str
    length: int
    url: str
    source: PCMVolumeTransformer[FFmpegPCMAudio]

    def __init__(self, url: str, requester: disnake.Member):
        self.requester: disnake.Member = requester
        self.left_off: float = 0
        
        # flag for local server, need to change for multiple server
        self.is_stream: bool = False
        self.source: PCMVolumeTransformer[FFmpegPCMAudio] = None
        # self.add_info(url, requester)

    def set_source(self, volumelevel):
        self.source = PCMVolumeTransformer(FFmpegPCMAudio(self.url, **self.ffmpeg_options), volume=volumelevel)
        
    def set_ffmpeg_options(self, timestamp):
        self.left_off = timestamp
        self.ffmpeg_options = {
            'options': f'-vn -ss {timestamp}',
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10',
        }
    
    def seek(self, stamp: float):
        if self.is_stream:
            raise SeekError
        self.set_ffmpeg_options(stamp)

class LoopState(Enum):
    NOTHING = auto()
    SINGLE = auto()
    PLAYLIST = auto()
    SINGLEINF = auto()

class PlaylistBase:
    '''maintain some info in a playlist for single guild'''
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.order = list() # maintain the song order in a playlist
        self.count = dict() # indicate the frequency of a given video_id
        self.loop_state: LoopState = LoopState.NOTHING
        self.times: int = 0 # use to indicate the times left to play current song

    def __getitem__(self, idx):
        return self.order[idx]

    def current(self):
        return self[0]
    
    def swap(self, idx1: int, idx2: int):
        self[idx1], self[idx2] = self[idx2], self[idx1]

    def move_to(self, origin: int, new: int):
        self.order.insert(new, self.order.pop(origin))
    
    def rule(self):
        if self.loop_state == LoopState.SINGLEINF:
            return
        if self.loop_state == LoopState.SINGLE:
            self.times -= 1
        elif self.loop_state == LoopState.PLAYLIST:
            self.order.append(self.order.pop(0))
        else:
            self.order.pop(0)
        if self.loop_state == LoopState.SINGLE and self.times == 0:
            self.loop_state =  LoopState.NOTHING
            
    def single_loop(self, times: int = INF):
        if self.loop_state != LoopState.SINGLE and self.loop_state != LoopState.SINGLEINF:
            self.loop_state = LoopState.SINGLE
            self.times = times # "times" value only availible in Single Loop mode
            if self.times == INF:
                self.loop_state = LoopState.SINGLEINF
        else:
            self.loop_state = LoopState.NOTHING
            self.times = 0

    def playlist_loop(self):
        if self.loop_state == LoopState.PLAYLIST:
            self.loop_state = LoopState.NOTHING
        else:
            self.loop_state = LoopState.PLAYLIST

class Playlist:
    '''a connector between Python data and MySQL data'''
    def __init__(self):
        self._database = DatabaseSession()
        self._guilds_info = dict()

    def __getitem__(self, guild_id) -> PlaylistBase:
        return self._guilds_info.get(guild_id, PlaylistBase())

    def create_session(self, guild_id: int):
        self._database.create_session(guild_id)

    def end_session(self, guild_id: int):
        self._database.end_session(guild_id)

    async def _mainloop(self, guild: disnake.Guild, channel: disnake.TextChannel):
        if self._database.check_session(guild.id):
            return
        async def check():
            while not len(self[guild.id].order):
                await asyncio.sleep(1.0)
            return True
        async def inner():
            self._database.create_session(guild.id)
            await asyncio.wait_for(check, timeout=30.0)
            while len(self[guild.id].order):
                await channel.send('now playing')
                voice_client: VoiceClient = guild.voice_client
                video_id = self[guild.id].current()
                source: dict = self._database.get_music_info(guild.id, video_id)
                voice_client.play(disnake.FFmpegPCMAudio(source['url']))
                try:
                    while voice_client.is_playing() or voice_client.is_paused():
                        await asyncio.sleep(1.0)
                finally:
                    self.rule(guild.id)
            self._database.end_session(guild.id)
        return inner
    
    def add_info(self, url, guild_id, requester):
        info = ytdl.get_info(url)
        self._database.add_music_info(guild_id, info)
        self[guild_id].order.append(info['video_id'])
        # self.requester = requester
        # self.set_ffmpeg_options(0)

    def nowplaying(self, guild_id: int) -> dict:
        info = self._database.get_music_info(guild_id, self[guild_id].nowplaying())
        return info

    def swap(self, guild_id: int, idx1: int, idx2: int):
        self[guild_id].swap(idx1, idx2)

    def move_to(self, guild_id: int, origin: int, new: int):
        self[guild_id].move_to(origin, new)
    
    def rule(self, guild_id: int):
        self[guild_id].rule()
            
    def single_loop(self, guild_id: int, times: int = INF):
        self[guild_id].single_loop(times)

    def playlist_loop(self, guild_id: int):
        self[guild_id].playlist_loop()
from typing import *
from enum import Enum, auto

import asyncio

import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer, TextChannel, VoiceClient
import wavelink

from .ytdl import YTDL

INF = int(1e18)

class SeekError(Exception): ...
class OutOfBound(Exception): ...

ytdl = YTDL()

class LoopState(Enum):
    NOTHING = auto()
    SINGLE = auto()
    PLAYLIST = auto()
    SINGLEINF = auto()

class PlaylistBase:
    '''maintain some info in a playlist for single guild'''
    def __init__(self):
        self.order: list[wavelink.Track] = [] # maintain the song order in a playlist
        self.loop_state: LoopState = LoopState.NOTHING
        self.times: int = 0 # use to indicate the times left to play current song
        self.text_channel: discord.TextChannel = None # where to show information to user
        # self._playlisttask: dict[str, asyncio.Task] = {}

    def __getitem__(self, idx):
        if len(self.order) == 0:
            return None
        return self.order[idx]

    def clear(self):
        self.order.clear()
        self.loop_state = LoopState.NOTHING
        self.times = 0

    def current(self) -> Optional[wavelink.Track]:
        return self[0]
    
    def swap(self, idx1: int, idx2: int):
        self.order[idx1], self.order[idx2] = self.order[idx2], self.order[idx1]

    def move_to(self, origin: int, new: int):
        self.order.insert(new, self.order.pop(origin))
    
    def rule(self):
        if len(self.order) == 0:
            return
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
    def __init__(self):
        self._guilds_info: Dict[int, PlaylistBase] = dict()

    def __delitem__(self, guild_id: int):
        if self._guilds_info.get(guild_id) is None:
            return
        del self._guilds_info[guild_id]
        
    def __getitem__(self, guild_id) -> PlaylistBase:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = PlaylistBase()
        return self._guilds_info[guild_id]

    async def add_songs(self, guild_id, trackinfo: Union[wavelink.YouTubeTrack, wavelink.SoundCloudTrack, wavelink.YouTubePlaylist], requester):
        if isinstance(trackinfo, wavelink.YouTubePlaylist):
            for track in trackinfo.tracks:
                track.requester = requester
            self[guild_id].order.extend(trackinfo.tracks)
        else:
            trackinfo.requester = requester
            self[guild_id].order.append(trackinfo)

    def get_music_info(self, guild_id, index):
        return self[guild_id].order[index]

    def nowplaying(self, guild_id: int) -> dict:
        return self[guild_id].current()

    def swap(self, guild_id: int, idx1: int, idx2: int):
        self[guild_id].swap(idx1, idx2)

    def move_to(self, guild_id: int, origin: int, new: int):
        self[guild_id].move_to(origin, new)
    
    def pop(self, guild_id: int, idx: int):
        self[guild_id].order.pop(idx)

    def rule(self, guild_id: int):
        self[guild_id].rule()
            
    def single_loop(self, guild_id: int, times: int = INF):
        self[guild_id].single_loop(times)

    def playlist_loop(self, guild_id: int):
        self[guild_id].playlist_loop()
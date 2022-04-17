from typing import *
from enum import Enum
import disnake
from disnake import FFmpegPCMAudio, PCMVolumeTransformer

from .ytdl import YTDL

INF = int(1e18)

class SeekError(Exception): ...
class OutOfBound(Exception): ...

ytdl = YTDL()

class Song:
    
    title: str
    author: str
    channel_url: str
    watch_url: str
    thumbnail_url: str
    length: int
    url: str
    source: PCMVolumeTransformer[FFmpegPCMAudio]

    def __init__(self):
        self.requester: disnake.Member = None
        self.left_off: float = 0
        
        # flag for local server, need to change for multiple server
        self.is_stream: bool = False
        self.source: PCMVolumeTransformer[FFmpegPCMAudio] = None

    def add_info(self, url, requester, volumelevel):
        ytdl.get_info(self, url)
        self.requester = requester
        self.is_stream = (self.length == 0)
        self.set_ffmpeg_options(0)

    def cleanup(self, volumelevel):
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
        stamp = max(0, min(self.length, stamp))
        self.set_ffmpeg_options(stamp)

class LoopState(Enum):
    # 0 is for not looping, 1 is for single, 2 is for whole
    NOTHING = 0
    SINGLE = 1
    WHOLE = 2

class Playlist(List[Song]):
    def __init__(self):
        self.is_loop: LoopState = LoopState.NOTHING
        self.times: int = 0

    def nowplaying(self) -> Song:
        return self.index()

    def swap(self, idx1: int, idx2: int):
        self[idx1], self[idx2] = self[idx2], self[idx1]

    def move_to(self, origin: int, new: int):
        self.insert(new, self.pop(origin))

    def rule(self):
        if len(self) == 0:
            return
        if self.is_loop == LoopState.SINGLE and self.times > 0:
            self.times -= 1
        elif self.is_loop == LoopState.WHOLE:
            self.append(self.pop(0))
        else:
            self.pop(0)
    
    def single_loop(self, times: int=INF):
        if (self.is_loop == LoopState.SINGLE):
            self.is_loop = LoopState.NOTHING
        else:
            self.is_loop = LoopState.SINGLE
        self.times = times

    def whole_loop(self):
        if (self.is_loop == LoopState.WHOLE):
            self.is_loop = LoopState.NOTHING
        else:
            self.is_loop = LoopState.WHOLE
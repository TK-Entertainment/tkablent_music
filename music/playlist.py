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

    def __init__(self, url: str, requester: disnake.Member):
        self.requester: disnake.Member = requester
        self.left_off: float = 0
        
        # flag for local server, need to change for multiple server
        self.is_stream: bool = False
        self.source: PCMVolumeTransformer[FFmpegPCMAudio] = None
        self.add_info(url, requester)

    def add_info(self, url, requester):
        ytdl.get_info(self, url)
        self.requester = requester
        self.is_stream = (self.length == 0)
        self.set_ffmpeg_options(0)

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
        stamp = stamp
        self.set_ffmpeg_options(stamp)

class LoopState(Enum):
    # 0 is for not looping, 1 is for single, 2 is for whole
    NOTHING = 0
    SINGLE = 1
    WHOLE = 2
    SINGLEINF = 3

class Playlist(List[Song]):
    def __init__(self):
        self.loop_state: LoopState = LoopState.NOTHING
        self.times: int = 0

    def nowplaying(self) -> Song:
        return self.index()

    def swap(self, idx1: int, idx2: int):
        self[idx1], self[idx2] = self[idx2], self[idx1]

    def move_to(self, origin: int, new: int):
        self.insert(new, self.pop(origin))

    def rule(self):
        if len(self) == 0:
            return 0
        if self.loop_state == LoopState.SINGLE and self.times > 0:
            self.times -= 1
            return 0
        elif self.loop_state == LoopState.WHOLE:
            self.append(self.pop(0))
            return 0
        else:
            length = self[0].length
            self.pop(0)
            return length
            
    
    def single_loop(self, times: int=INF):
        if (self.loop_state == LoopState.SINGLE) and times == INF:
            self.loop_state = LoopState.NOTHING
        else:
            # "times" value only availible in Single Loop mode
            self.loop_state = LoopState.SINGLE
            if times == INF:
                self.loop_state = LoopState.SINGLEINF
        self.times = times

    def whole_loop(self):
        if (self.loop_state == LoopState.WHOLE):
            self.loop_state = LoopState.NOTHING
        else:
            self.loop_state = LoopState.WHOLE
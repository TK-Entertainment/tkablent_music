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

    def __init__(self):
        self.requester: disnake.Member = None
        self.left_off: float = 0
        
        # flag for local server, need to change for multiple server
        self.is_stream: bool = False
        self.source: FFmpegPCMAudio = None

    def add_info(self, url, requester, volumelevel):
        ytdl.get_info(self, url)
        self.requester = requester
        self.is_stream = (self.length == 0)
        self.set_ffmpeg_options(0)
        self.cleanup(volumelevel)

    def cleanup(self, volumelevel):
        self.source = None
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

    def info(self, embed_op, sthtool, botprefix=None, color: str=None, currentpl=None, mute=False):
        if color == "green": embed = disnake.Embed(title=self.title, url=self.watch_url, colour=disnake.Colour.from_rgb(97, 219, 83))
        else: embed = disnake.Embed(title=self.title, url=self.watch_url, colour=disnake.Colour.from_rgb(255, 255, 255))
        embed.add_field(name="作者", value=f'[{self.author}]({self.channel_url})', inline=True)
        if self.is_stream: 
            if color == None: embed.add_field(name="結束播放", value=f"輸入 ⏩ {botprefix}skip / ⏹️ {botprefix}stop\n來結束播放此直播", inline=True)
            if mute: embed.set_author(name=f"這首歌由 {self.requester.name}#{self.requester.tag} 點歌 | 🔴 直播 | 🔇 靜音", icon_url=self.requester.display_avatar)
            else: embed.set_author(name=f"這首歌由 {self.requester.name}#{self.requester.tag} 點歌 | 🔴 直播", icon_url=self.requester.display_avatar)
        else: 
            embed.add_field(name="歌曲時長", value=sthtool(self.length, "zh"), inline=True)
            if mute: embed.set_author(name=f"這首歌由 {self.requester.name}#{self.requester.tag} 點歌 | 🔇 靜音", icon_url=self.requester.display_avatar)
            else: embed.set_author(name=f"這首歌由 {self.requester.name}#{self.requester.tag} 點歌", icon_url=self.requester.display_avatar)
        if len(currentpl) > 1:
            queuelist: str = ""
            queuelist += f"1." + currentpl[1].title + f"\n ...還有 {len(currentpl)-2} 首歌"
            embed.add_field(name=f"待播清單 | {len(currentpl)-1} 首歌待播中", value=queuelist, inline=False)
        embed.set_thumbnail(url=self.thumbnail_url)
        embed = disnake.Embed.from_dict(dict(**embed.to_dict(), **embed_op))
        return embed

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
from typing import *
import threading, asyncio

from disnake import VoiceClient, VoiceChannel, FFmpegPCMAudio, PCMVolumeTransformer

from .playlist import Song, Playlist

class Player:                                                        
    def __init__(self):
        # flag for local server, need to change for multiple server
        self.voice_client: VoiceClient = None
        self.playlist: Playlist = Playlist()
        self.playing: threading.Thread = None
        self.in_mainloop: bool = False
        self.volumelevel: float = 1.0
        self.ismute: bool = False
    
    async def join(self, channel: VoiceChannel):
        if (self.voice_client is None) or (not self.voice_client.is_connected()):
            await channel.connect()
            self.voice_client = channel.guild.voice_client
        
    async def leave(self):
        if (self.voice_client.is_connected()):
            await self.voice_client.disconnect()
        else:
            raise Exception # this exception is for identifying the illegal operation

    def search(self, url, **kwargs):
        song: Song = Song()
        song.add_info(url, volumelevel=self.volumelevel, **kwargs)
        self.playlist.append(song)

    async def play(self):
        self.playlist[0].source.volume = self.volumelevel
        self.voice_client.play(self.playlist[0].source)

    async def wait(self):
        try:
            while not self.voice_client._player._end.is_set():
                await asyncio.sleep(1.0)
        except:
            return

    def pause(self):
        if (not self.voice_client.is_paused() and self.voice_client.is_playing()):
            self.voice_client.pause()
            self.playlist[0].left_off += self.voice_client._player.loops / 50
        else:
            raise Exception # this exception is for identifying the illegal operation

    def resume(self):
        if (self.voice_client.is_paused()):
            self.voice_client.resume()
        else:
            raise Exception # this exception is for identifying the illegal operation

    def skip(self):
        if (not self.voice_client._player._end.is_set()):
            self.voice_client.stop()
        self.playlist.times = 0
    
    def stop(self):
        self.playlist.clear()
        self.skip()

    def get_current_time(self) -> float:
        if self.voice_client.is_paused():
            return self.playlist[0].left_off
        return self.playlist[0].left_off + self.voice_client._player.loops / 50

    def seek(self, timestamp: float):
        self.playlist[0].seek(timestamp)
        self.voice_client.source = PCMVolumeTransformer(FFmpegPCMAudio(self.playlist[0].url, **self.playlist[0].ffmpeg_options), volume=self.volumelevel)
    
    def volume(self, volume: float):
        self.volumelevel = volume
        if not self.voice_client is None:
            self.voice_client.source.volume = self.volumelevel
            
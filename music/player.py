from typing import *
import threading, asyncio, gc

import disnake
from disnake import VoiceClient, VoiceChannel, FFmpegPCMAudio, PCMVolumeTransformer
from disnake.ext import commands

from .playlist import Song, Playlist, LoopState

INF = int(1e18)
bot_version = 'LOCAL DEVELOPMENT'

class Player:     
    def __del__(self):
        print('collected')  

    def __init__(self):
        # flag for local server, need to change for multiple server
        self.voice_client: VoiceClient = None
        self.playlist: Playlist = Playlist()
        self.in_mainloop: bool = False
        self.volumelevel: float = 1.0
        self.ismute: bool = False
        self.isskip: bool = False
    
    async def _join(self, channel: VoiceChannel):
        if (self.voice_client is None) or (not self.voice_client.is_connected()):
            await channel.connect()
            self.voice_client = channel.guild.voice_client
        
    async def _leave(self):
        if (self.voice_client.is_connected()):
            self._stop()
            await self.voice_client.disconnect()
            self.voice_client = None
        else:
            raise Exception # this exception is for identifying the illegal operation

    def _search(self, url, **kwargs):
        song: Song = Song()
        song.add_info(url, volumelevel=self.volumelevel, **kwargs)
        self.playlist.append(song)

    async def _play(self):
        self.playlist[0].cleanup(self.volumelevel)
        self.playlist[0].source.volume = self.volumelevel
        self.voice_client.play(self.playlist[0].source)

    async def wait(self):
        try:
            while not self.voice_client._player._end.is_set():
                await asyncio.sleep(1.0)
        except:
            return

    def _pause(self):
        if (not self.voice_client.is_paused() and self.voice_client.is_playing()):
            self.voice_client.pause()
            self.playlist[0].left_off += self.voice_client._player.loops / 50
        else:
            raise Exception # this exception is for identifying the illegal operation

    def _resume(self):
        if (self.voice_client.is_paused()):
            self.voice_client.resume()
        else:
            raise Exception # this exception is for identifying the illegal operation

    def _skip(self):
        try:
            if (not self.voice_client._player._end.is_set()):
                self.voice_client.stop()
                self.isskip = True
        except:
            pass
        finally:
            self.playlist.times = 0
    
    def _stop(self):
        self.playlist.clear()
        self._skip()

    def _get_current_time(self) -> float:
        if self.voice_client.is_paused():
            return self.playlist[0].left_off
        return self.playlist[0].left_off + self.voice_client._player.loops / 50

    def _seek(self, timestamp: float):
        if timestamp >= self.playlist[0].length:
            self.voice_client.stop()
            return 'Exceed'
        self.playlist[0].seek(timestamp)
        self.voice_client.source = PCMVolumeTransformer(FFmpegPCMAudio(self.playlist[0].url, **self.playlist[0].ffmpeg_options), volume=self.volumelevel)
    
    def _volume(self, volume: float):
        self.volumelevel = volume
        if not self.voice_client is None:
            self.voice_client.source.volume = self.volumelevel

from .ui import UI       

class MusicBot(Player):
    def __init__(self, bot):
        Player.__init__(self)
        self.bot: commands.Bot = bot
        self.ui: UI = UI(bot_version)
        self.ui.InitEmbedFooter(bot)
        self.task: asyncio.Task = None

    def sec_to_hms(self, seconds, format) -> str:
        sec = int(seconds%60); min = int(seconds//60%60); hr = int(seconds//3600)
        if format == "symbol":
            if hr == 0:
                return "{}{}:{}{}".format("0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
            else:
                return "{}{}:{}{}:{}{}".format("0" if hr < 10 else "", hr, "0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
        elif format == "zh":
            if hr != 0: 
                return f"{hr} 小時 {min} 分 {sec} 秒"
            elif min != 0:
                return f"{min} 分 {sec} 秒"
            elif sec != 0:
                return f"{sec} 秒"
                

    async def join(self, ctx: commands.Context, jointype=None):
        try:
            isinstance(self.voice_client.channel, None)
            notin = False
        except: notin = True
        if isinstance(self.voice_client, disnake.VoiceClient) or notin == False:
            if jointype == None:
                await self.ui.JoinAlready(ctx)
            return
        try:
            await self._join(ctx.author.voice.channel)
            if isinstance(ctx.author.voice.channel, disnake.StageChannel):
                await self.ui.JoinStage(ctx)
                await self.ui.CreateStageInstance(ctx)
            else:
                await self.ui.JoinNormal(ctx)
        except Exception as e:
            print(e)
            await self.ui.JoinFailed(ctx)
            return 'failed'

    async def leave(self, ctx: commands.Context):
        try:
            try: 
                if isinstance(self.voice_client.channel.instance, disnake.StageInstance):
                    await self.ui.EndStage(self)
            except: pass
            finally: await self._leave()
            await self.ui.LeaveSucceed(ctx)
        except Exception as e:
            await self.ui.LeaveFailed(ctx)

    async def play(self, ctx: commands.Context, *url):
        botitself: disnake.Member = await ctx.guild.fetch_member(self.bot.user.id)
        url = ' '.join(url)
        status = await self.join(ctx, "playattempt")
        if status == 'failed': return
        async with ctx.typing():
            await self.ui.StartSearch(ctx, url, self.playlist)
            self._search(url, requester=ctx.message.author)
            await self.ui.Embed_AddedToQueue(ctx, self.playlist)
        self.voice_client = ctx.guild.voice_client
        if botitself.voice.suppress:
            try: await botitself.edit(suppress=False)
            except: pass
        self.task = self.bot.loop.create_task(self._mainloop(ctx))
        

    async def _mainloop(self, ctx: commands.Context):
        if (self.in_mainloop):
            return
        self.in_mainloop = True
        
        while len(self.playlist):
            if not self.isskip:
                await self.ui.StartPlaying(ctx, self, self.ismute)
            else:
                if self.playlist.flag != LoopState.SINGLEINF:
                    self.playlist.is_loop = LoopState.NOTHING; self.playlist.times = 0
                await self.ui.SkipSucceed(ctx, self.playlist, self.ismute)
            await self._play()
            await self.wait()
            try: self.playlist[0].cleanup(self.volumelevel)
            except: pass
            self.playlist.rule()

        self.in_mainloop = False
        # Reset value
        self.playlist.is_loop = LoopState.NOTHING
        self.playlist.flag = None
        self.isskip = False
        self.task = None
        await self.ui.DonePlaying(ctx, self)

    async def pause(self, ctx: commands.Context):
        try:
            self._pause()
            await self.ui.PauseSucceed(ctx, self)
        except:
            await self.ui.PauseFailed(ctx)

    async def resume(self, ctx: commands.Context):
        try:
            self._resume()
            await self.ui.ResumeSucceed(ctx, self)
        except:
            await self.ui.ResumeFailed(ctx)

    async def skip(self, ctx: commands.Context):
        try:
            self._skip()
        except:
            await self.ui.SkipFailed(ctx)

    async def stop(self, ctx: commands.Context):
        try:
            self.in_mainloop = False
            self._stop()
            await self.ui.StopSucceed(ctx)
        except:
            await self.ui.StopFailed(ctx)

    async def mute(self, ctx):
        if self.ismute: await self.volume(ctx, 100.0, unmute=True)
        else: await self.volume(ctx, 0.0)

    async def volume(self, ctx: commands.Context, percent: Union[float, str]=None, unmute: bool=False):
        if not isinstance(percent, float) and percent is not None:
            await self.ui.VolumeAdjustFailed(ctx)
            return
        if percent == 0 or (percent == 100 and unmute):
            self.ismute = await self.ui.MuteorUnMute(ctx, percent, self)
        else:
            self.ismute = await self.ui.VolumeAdjust(ctx, percent, self)
        if percent is not None:
            self._volume(percent / 100)

    async def seek(self, ctx: commands.Context, timestamp: Union[float, str]):
        try:
            if isinstance(timestamp, str) and ":" in timestamp:
                tmp = timestamp.split(":"); timestamp = 0
                for i in range(0, len(tmp)):
                    timestamp += int(tmp[-i-1])*(60**(i))
            int(timestamp) # For ignoring string with ":" like "o:ro"
        except ValueError: 
            await self.ui.SeekFailed(ctx)
            return
        if self._seek(timestamp) != 'Exceed':
            await self.ui.SeekSucceed(ctx, timestamp, self)

    async def restart(self, ctx: commands.Context):
        try:
            self._seek(0)
            await self.ui.ReplaySucceed(ctx)
        except:
            await self.ui.ReplayFailed(ctx)

    async def single_loop(self, ctx: commands.Context, times: Union[int, str]=INF):
        if not isinstance(times, int):
            return await self.ui.SingleLoopFailed(ctx)
        self.playlist.single_loop(times)
        await self.ui.LoopSucceed(ctx, self.playlist, self.ismute)

    async def whole_loop(self, ctx: commands.Context):
        self.playlist.whole_loop()
        await self.ui.LoopSucceed(ctx, self.playlist, self.ismute)

    async def show(self, ctx: commands.Context):
        await self.ui.ShowQueue(ctx, self.playlist)

    async def remove(self, ctx: commands.Context, idx: Union[int, str]):
        try:
            snapshot = []; snapshot.append(self.playlist.pop(idx))
            await self.ui.RemoveSucceed(ctx, snapshot, idx)
        except (IndexError, TypeError):
            await self.ui.RemoveFailed(ctx)
    
    async def swap(self, ctx: commands.Context, idx1: Union[int, str], idx2: Union[int, str]):
        try:
            self.playlist.swap(idx1, idx2)
            await self.ui.Embed_SwapSucceed(ctx, self.playlist, idx1, idx2)
        except (IndexError, TypeError):
            await self.ui.SwapFailed(ctx)

    async def move_to(self, ctx: commands.Context, origin: Union[int, str], new: Union[int, str]):
        try:
            self.playlist.move_to(origin, new)
            await self.ui.MoveToSucceed(ctx, self.playlist, origin, new)
        except (IndexError, TypeError):
            await self.ui.MoveToFailed(ctx)
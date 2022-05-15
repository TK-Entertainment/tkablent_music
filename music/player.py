from typing import *
import threading, asyncio, gc

import disnake
from disnake import VoiceClient, VoiceChannel, FFmpegPCMAudio, PCMVolumeTransformer
from disnake.ext import commands

from .playlist import Song, Playlist, LoopState
from pytube import exceptions as PytubeExceptions
from yt_dlp import utils as YTDLPExceptions

INF = int(1e18)
bot_version = 'master Branch'

class Player:
    def __del__(self):
        print('collected')  

    def __init__(self):
        # flag for local server, need to change for multiple server
        self.voice_client: VoiceClient = None
        self.playlist: Playlist = Playlist()
        self.in_mainloop: bool = False
        self.volume_level: float = 1.0
        self.ismute: bool = False
        self.isskip: bool = False
        self.totallength: int = 0

    @property
    def current_timestamp(self) -> float:
        if self.voice_client.is_paused():
            return self.playlist[0].left_off
        return self.playlist[0].left_off + self.voice_client._player.loops / 50
    
    async def _join(self, channel: VoiceChannel):
        if self.voice_client is None or not self.voice_client.is_connected():
            await channel.connect()
            self.voice_client = channel.guild.voice_client
        
    async def _leave(self):
        if self.voice_client.is_connected():
            self._stop()
            await self.voice_client.disconnect()
            self.voice_client = None
        else:
            raise Exception # this exception is for identifying the illegal operation

    def _search(self, url: str, requester: disnake.Member):
        song: Song = Song(url, requester)
        self.playlist.append(song)

    async def _play(self):
        self.playlist[0].set_source(self.volume_level)
        self.playlist[0].source.volume = self.volume_level
        self.voice_client.play(self.playlist[0].source)

    async def wait(self):
        try:
            while not self.voice_client._player._end.is_set():
                await asyncio.sleep(1.0)
        finally:
            return

    def _pause(self):
        if not self.voice_client.is_paused() and self.voice_client.is_playing():
            self.voice_client.pause()
            self.playlist[0].left_off += self.voice_client._player.loops / 50
        else:
            raise Exception # this exception is for identifying the illegal operation

    def _resume(self):
        if self.voice_client.is_paused():
            self.voice_client.resume()
        else:
            raise Exception # this exception is for identifying the illegal operation

    def _skip(self):
        try:
            if not self.voice_client._player._end.is_set():
                self.voice_client.stop()
                self.isskip = True
        finally:
            self.playlist.times = 0
    
    def _stop(self):
        self.playlist.clear()
        self._skip()
        self.isskip = False

    def _seek(self, timestamp: float):
        if timestamp >= self.playlist[0].length:
            self.voice_client.stop()
            return 'Exceed'
        self.playlist[0].seek(timestamp)
        self.playlist[0].set_source(self.volume_level)
    
    def _volume(self, volume: float):
        self.volume_level = volume
        if not self.voice_client is None:
            self.voice_client.source.volume = self.volume_level

from .ui import UI

class MusicBot(Player):
    def __init__(self, bot):
        commands.Cog.__init__(self)
        Player.__init__(self)
        self.bot: commands.Bot = bot
        self.ui: UI = UI(bot_version)
        self.ui.InitEmbedFooter(bot)
        self.task: asyncio.Task = None
        self.inactive: bool = False
        self.timedout: bool = False

    async def timeout(self, ctx):
        if self.inactive:
            await asyncio.sleep(600)
            try:
                await self.leave(ctx, 'timeout')
            except:
                pass

    def sec_to_hms(self, seconds, format) -> str:
        sec = int(seconds%60); min = int(seconds//60%60); hr = int(seconds//24//60%60); day = int(seconds//86400)
        if format == "symbol":
            if day != 0:
                return "{}{}:{}{}:{}{}:{}{}".format("0" if day < 10 else "", day, "0" if hr < 10 else "", hr, "0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
            if hr != 0:
                return "{}{}:{}{}:{}{}".format("0" if hr < 10 else "", hr, "0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
            else:
                return "{}{}:{}{}".format("0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
        elif format == "zh":
            if day != 0:
                return f"{day} 天 {hr} 小時 {min} 分 {sec} 秒"
            elif hr != 0: 
                return f"{hr} 小時 {min} 分 {sec} 秒"
            elif min != 0:
                return f"{min} 分 {sec} 秒"
            elif sec != 0:
                return f"{sec} 秒"
    
    async def help(self, ctx: commands.Context):
        await self.ui.Help(ctx)

    async def join(self, ctx: commands.Context, jointype: str='normal'):
        if self.task is not None:
            self.task.cancel()
        botitself: disnake.Member = await ctx.guild.fetch_member(self.bot.user.id)
        try:
            isinstance(self.voice_client.channel, None)
            notin = False
        except: notin = True
        if isinstance(self.voice_client, disnake.VoiceClient) or notin == False:
            if self.voice_client.channel != ctx.author.voice.channel:
                former = self.voice_client.channel; formerstate = self.voice_client.is_paused()
                pause_after_rejoin = False
                if not formerstate:
                    self._pause()
                    pause_after_rejoin = True
                await botitself.move_to(ctx.author.voice.channel)
                if pause_after_rejoin: self._resume()
                if formerstate: self.task = self.bot.loop.create_task(self.timeout(ctx))
                await self.ui.JoinNormal(ctx, 'rejoin')
                if isinstance(former, disnake.StageChannel):
                    if isinstance(former.instance, disnake.StageInstance):
                        await former.delete()
                return
            else:
                if jointype == 'playattempt': return
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
            await self.ui.JoinFailed(ctx)
            return 'failed'

    async def leave(self, ctx: commands.Context, mode: str='normal'):
        try:
            try: 
                if isinstance(self.voice_client.channel.instance, disnake.StageInstance):
                    await self.ui.EndStage(self)
                await self._leave()
            except: await self._leave()
            if mode == 'timeout': 
                self.timedout: bool = True
                await self.ui.LeaveOnTimeout(ctx)
            else: 
                if self.task is not None:
                    self.task.cancel()
                await self.ui.LeaveSucceed(ctx)
        except:
            await self.ui.LeaveFailed(ctx)

    async def play(self, ctx: commands.Context, *url):
        botitself: disnake.Member = await ctx.guild.fetch_member(self.bot.user.id)
        url = ' '.join(url)
        status = await self.join(ctx, 'playattempt')
        if status == 'failed': return
        async with ctx.typing():
            await self.ui.StartSearch(ctx, url, self.playlist)
            try: 
                self._search(url, requester=ctx.message.author)
            except Exception as e:
                await self._SearchFailedHandler(ctx, e, url)
                return
            await self.ui.Embed_AddedToQueue(ctx, self.playlist)
            if len(self.playlist) > 1:
                self.totallength += self.playlist[-1].length
        self.voice_client = ctx.guild.voice_client
        if self.ui.autostageavailable and isinstance(ctx.author.voice.channel, disnake.StageChannel):
            if botitself.voice.suppress:
                try: await botitself.edit(suppress=False)
                except: pass
        self.bot.loop.create_task(self._mainloop(ctx))

    async def _SearchFailedHandler(self, ctx: commands.Context, exception: Exception, url: str):
        if isinstance(exception, PytubeExceptions.VideoPrivate) or (isinstance(exception, YTDLPExceptions.DownloadError) and "Private Video" in exception.msg):
            await self.ui.SearchFailed(ctx, url, "VideoPrivate")
        elif isinstance(exception, PytubeExceptions.MembersOnly):
            await self.ui.SearchFailed(ctx, url, 'MembersOnly')
        else:
            await self.ui.SearchFailed(ctx, url, 'Unknown')

    async def _mainloop(self, ctx: commands.Context):
        if (self.in_mainloop):
            return
        self.in_mainloop = True
        
        while len(self.playlist):
            if self.task is not None:
                self.task.cancel()
            self.inactive = False
            if not self.isskip:
                await self.ui.StartPlaying(ctx, self, self.ismute)
            else:
                if self.playlist.flag != LoopState.SINGLEINF:
                    self.playlist.loop_state = LoopState.NOTHING; self.playlist.times = 0
                await self.ui.SkipSucceed(ctx, self.playlist, self.ismute)
                await self.ui.__UpdateStageTopic__(self)
                self.isskip = False
            await self._play()
            await self.wait()
            try: self.playlist[0].set_source(self.volume_level)
            except: pass
            self.totallength -= self.playlist.rule()

        self.in_mainloop = False
        if self.isskip: await self.ui.SkipSucceed(ctx, self.playlist, self.ismute)
        # Reset value
        self.playlist.loop_state = LoopState.NOTHING
        self.playlist.flag = None
        self.isskip = False
        if not self.timedout:
            await self.ui.DonePlaying(ctx, self)
        if not self.timedout:
            self.inactive = True
            self.task = self.bot.loop.create_task(self.timeout(ctx))

    async def pause(self, ctx: commands.Context, onlybotin: bool=False):
        try:
            self._pause()
            if self.task is not None:
                self.task.cancel()
            self.inactive = True
            self.task = self.bot.loop.create_task(self.timeout(ctx))
            if onlybotin: await self.ui.PauseOnAllMemberLeave(ctx, self)
            else: await self.ui.PauseSucceed(ctx, self)
        except Exception as e:
            print(e)
            await self.ui.PauseFailed(ctx)

    async def resume(self, ctx: commands.Context):
        try:
            if self.task is not None:
                self.task.cancel()
            self._resume()
            self.inactive = False
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
            if self.task is not None:
                self.task.cancel()
            self.task = self.bot.loop.create_task(self.timeout(ctx))
            self.inactive = True
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

    async def show_queue(self, ctx: commands.Context):
        await self.ui.ShowQueue(ctx, self.playlist, self.totallength)

    async def remove(self, ctx: commands.Context, idx: Union[int, str]):
        try:
            snapshot = []; snapshot.append(self.playlist.pop(idx))
            self.totallength -= snapshot[0].length
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
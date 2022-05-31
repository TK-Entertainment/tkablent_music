from typing import *
import threading, asyncio, gc, weakref

import disnake
from disnake import VoiceClient, VoiceChannel, FFmpegPCMAudio, PCMVolumeTransformer
from disnake.ext import commands

from .playlist import Song, Playlist, LoopState
from pytube import exceptions as PytubeExceptions
from yt_dlp import utils as YTDLPExceptions
from .ytdl import YTDL


INF = int(1e18)
bot_version = 'master Branch'

class Player(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self._playlist: Playlist = Playlist()
        self._volume_levels: Dict[int, int] = dict()
        self._tasks: Dict[int, asyncio.Task] = dict()
        self._timers: Dict[int, asyncio.Task] = dict()

    async def _join(self, channel: disnake.VoiceChannel):
        voice_client = channel.guild.voice_client
        if voice_client is None:
            await channel.connect()

    async def _leave(self, guild: disnake.Guild):
        voice_client = guild.voice_client
        if voice_client is not None:
            self._stop(guild)
            await voice_client.disconnect()
            
    def _search(self, guild: disnake.Guild, url, requester: disnake.Member):
        self._playlist.add_songs(guild.id, url, requester)

    def _pause(self, guild: disnake.Guild):
        voice_client: VoiceClient = guild.voice_client
        if not voice_client.is_paused() and voice_client.is_playing():
            voice_client.pause()

    def _resume(self, guild: disnake.Guild):
        voice_client: VoiceClient = guild.voice_client
        if voice_client.is_paused():
            self._playlist[guild.id].current().left_off += voice_client._player.loops / 50
            voice_client.resume()

    def _skip(self, guild: disnake.Guild):
        voice_client: VoiceClient = guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        self._playlist[guild].times = 0
    
    def _stop(self, guild: disnake.Guild):
        self._playlist[guild.id].clear()
        self._skip(guild)
    
    @property
    def current_timestamp(self, guild: disnake.Guild) -> float:
        voice_client: disnake.VoiceClient = guild.voice_client
        return self._playlist[guild.id].current().left_off + voice_client._player.loops / 50
    
    def _seek(self, guild: disnake.Guild, timestamp: float):
        voice_client: disnake.VoiceClient = guild.voice_client
        if timestamp >= self._playlist[guild.id].current().info['length']:
            voice_client.stop()
            return 'Exceed'
        self._playlist[guild.id].current().seek(timestamp)
        volume_level = self._volume_levels[guild.id]
        self._playlist[guild.id].current().set_source(volume_level)
        voice_client.source = self._playlist[guild.id].current().source
    
    def _volume(self, guild: disnake.Guild, volume: float):
        voice_client: disnake.VoiceClient = guild.voice_client
        if not voice_client is None:
            self._volume_levels[guild.id] = volume
            voice_client.source.volume = volume

    async def _play(self, guild: disnake.Guild, channel: disnake.TextChannel):
        self._playlist[guild.id].text_channel = channel
        await self._start_mainloop(guild)

    async def _start_mainloop(self, guild: disnake.Guild):
        if self._timers.get(guild.id) is not None:
            self._timers[guild.id].cancel()
            del self._timers[guild.id]
        if self._tasks.get(guild.id) is not None:
            return
        coro = self._mainloop(guild)
        self._tasks[guild.id] = self.bot.loop.create_task(coro)
        self._tasks[guild.id].add_done_callback(lambda task, guild=guild: self._start_timer(guild))
    
    async def _mainloop(self, guild: disnake.Guild):
        # implement in musicbot class for ui support
        '''
        while len(self._playlist[guild.id].order):
            await self._playlist[guild.id].text_channel.send('now playing')
            voice_client: VoiceClient = guild.voice_client
            song = self._playlist[guild.id].current()
            try:
                voice_client.play(disnake.FFmpegPCMAudio(song.url))
                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(1.0)
            finally:
                self._playlist.rule(guild.id)
        '''
        raise NotImplementedError

    def _start_timer(self, guild: disnake.Guild):
        if self._tasks.get(guild.id) is not None:
            self._tasks[guild.id].cancel()
            del self._tasks[guild.id]
        if self._timers.get(guild.id) is not None:
            self._timers[guild.id].cancel()
        coro = self._timer(guild)
        self._timers[guild.id] = self.bot.loop.create_task(coro)
    
    async def _timer(self, guild: disnake.Guild):
        await asyncio.sleep(15.0)
        await self._leave(guild)
    
    def _cleanup(self, guild: disnake.Guild):
        if self._tasks.get(guild.id) is not None:
            del self._tasks[guild.id]
        del self._playlist[guild.id]
        if self._timers.get(guild.id) is not None:
            self._timers[guild.id].cancel()
            del self._timers[guild.id]


from .ui import UI

class MusicBot(Player, commands.Cog):
    def __init__(self, bot: commands.Bot):
        Player.__init__(self, bot)
        commands.Cog.__init__(self)
        self.ui = UI(bot_version)
        # self.ui.InitEmbedFooter(bot)
    
    @commands.command(name='help')
    async def help(self, ctx: commands.Context):
        await self.ui.Help(ctx)
    
    async def rejoin(self, ctx: commands.Context):
        voice_client: disnake.VoiceClient = ctx.guild.voice_client
        # Get the bot former playing state
        former = voice_client.channel
        former_state = voice_client.is_paused()
        # To determine is the music paused before rejoining or not
        if not former_state: 
            self._pause()
        # Moving itself to author's channel
        await voice_client.move_to(ctx.author.voice.channel)
        # If paused before rejoining, resume the music
        if not former_state: 
            self._resume()
        # Send a rejoin message
        await self.ui.RejoinNormal(ctx)
        # If the former channel is a disnake.StageInstance which is the stage
        # channel with topics, end that stage instance
        if isinstance(former, disnake.StageChannel) and \
                isinstance(former.instance, disnake.StageInstance):
            await former.delete()
    
    @commands.command(name='join')
    async def join(self, ctx: commands.Context):
        voice_client: disnake.VoiceClient = ctx.guild.voice_client
        if isinstance(voice_client, disnake.VoiceClient):
            if voice_client.channel != ctx.author.voice.channel:
                await self.rejoin(ctx)
            else:
                # If bot joined the same channel, send a message to notice user
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
    
    @commands.command(name='leave', aliases=['quit'])
    async def leave(self, ctx: commands.Context):
        voice_client: disnake.VoiceClient = ctx.guild.voice_client
        try:
            if isinstance(voice_client.channel, disnake.StageChannel) and \
                    isinstance(voice_client.channel.instance, disnake.StageInstance):
                await self.ui.EndStage(self)
            await self._leave(ctx.guild)
            await self.ui.LeaveSucceed(ctx)
        except:
            await self.ui.LeaveFailed(ctx)

    async def search(self, ctx: commands.Context, *url):
        # Get user defined url/keyword
        url = ' '.join(url)

        async with ctx.typing():
            # Show searching UI (if user provide exact url, then it
            # won't send the UI)
            # await self.ui.StartSearch(ctx, url, self.playlist)
            # Call search function
            try: 
                self._search(ctx.guild, url, requester=ctx.message.author)
            except Exception as e:
                # If search failed, sent to handler
                # await self._SearchFailedHandler(ctx, e, url)
                return
            # If queue has more than 1 songs, then show the UI
            # await self.ui.Embed_AddedToQueue(ctx, self.playlist)
            # Experiment features (show total length in queuelist)
    
    @commands.command(name='play', aliases=['p', 'P'])
    async def play(self, ctx: commands.Context, *url):
        # Try to make bot join author's channel
        voice_client: VoiceClient = ctx.guild.voice_client
        if not isinstance(voice_client, disnake.VoiceClient) or \
                voice_client.channel != ctx.author.voice.channel:
            await self.join(ctx)
            voice_client = ctx.guild.voice_client
            if not isinstance(voice_client, disnake.VoiceClient):
                return

        # Start search process
        await self.search(ctx, *url)

        # Get bot user value
        bot_itself: disnake.Member = await ctx.guild.fetch_member(self.bot.user.id)
        if self.ui.is_auto_stage_available and \
                isinstance(ctx.author.voice.channel, disnake.StageChannel) and \
                bot_itself.voice.suppress:
            try: 
                await bot_itself.edit(suppress=False)
            except: 
                pass

        await self._play(ctx.guild, ctx.channel)

    async def _mainloop(self, guild: disnake.Guild):
        while len(self._playlist[guild.id].order):
            await self._playlist[guild.id].text_channel.send('now playing')
            voice_client: VoiceClient = guild.voice_client
            song = self._playlist[guild.id].current()
            try:
                voice_client.play(disnake.FFmpegPCMAudio(song.url))
                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(1.0)
            finally:
                self._playlist.rule(guild.id)
        
    @commands.Cog.listener(name='on_voice_state_update')
    async def end_session(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.id != self.bot.user.id or not (before.channel is not None and after.channel is None):
            return
        guild = member.guild
        channel = self._playlist[guild.id].text_channel
        if self._timers.get(guild.id) is not None and self._timers[guild.id].done():
            await self.ui.LeaveOnTimeout(channel)
        self._cleanup(guild)
    

'''
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
                
    async def help(self, ctx: commands.Context):
        await self.ui.Help(ctx)

    async def rejoin(self, ctx):
        # Get the bot former playing state
        former = self.voice_client.channel
        former_state = self.voice_client.is_paused()
        # To determine is the music paused before rejoining or not
        if not former_state: 
            self._pause()
        # Moving itself to author's channel
        await self.voice_client.move_to(ctx.author.voice.channel)
        # If paused before rejoining, resume the music
        if not former_state: 
            self._resume()
        # If paused before rejoining, reflag itself as inactive
        # (leaving channel after 10 minutes)
        if former_state: 
            self.task = self.bot.loop.create_task(self.timeout(ctx))
        # Send a rejoin message
        await self.ui.RejoinNormal(ctx)
        # If the former channel is a disnake.StageInstance which is the stage
        # channel with topics, end that stage instance
        if isinstance(former, disnake.StageChannel):
            if isinstance(former.instance, disnake.StageInstance):
                await former.delete()

    async def join(self, ctx: commands.Context):
        # Becoming active (cancel timer)
        if self.task is not None:
            self.task.cancel()
        if isinstance(self.voice_client, disnake.VoiceClient):
            if self.voice_client.channel != ctx.author.voice.channel:
                await self.rejoin(ctx)
            else:
                # If bot joined the same channel, send a message to notice user
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
            finally:
                await self._leave()
            if mode == 'timeout': 
                self.timedout: bool = True
                await self.ui.LeaveOnTimeout(ctx)
            else: 
                if self.task is not None:
                    self.task.cancel()
                await self.ui.LeaveSucceed(ctx)
        except:
            await self.ui.LeaveFailed(ctx)

    async def search(self, ctx: commands.Context, *url):
        # Get user defined url/keyword
        url = ' '.join(url)

        async with ctx.typing():
            # Show searching UI (if user provide exact url, then it
            # won't send the UI)
            await self.ui.StartSearch(ctx, url, self.playlist)
            # Call search function
            try: 
                self._search(url, requester=ctx.message.author)
            except Exception as e:
                # If search failed, sent to handler
                await self._SearchFailedHandler(ctx, e, url)
                return
            # If queue has more than 1 songs, then show the UI
            await self.ui.Embed_AddedToQueue(ctx, self.playlist)
            # Experiment features (show total length in queuelist)
            if len(self.playlist) > 1:
                self.totallength += self.playlist[-1].length

    async def play(self, ctx: commands.Context, *url):
        # Get bot user value
        bot_itself: disnake.Member = await ctx.guild.fetch_member(self.bot.user.id)
        
        # Try to make bot join author's channel
        if not isinstance(self.voice_client, disnake.VoiceClient) or \
            self.voice_client.channel != ctx.author.voice.channel:

            status = await self.join(ctx)
            if status == 'failed': 
                return

        # Start search process
        await self.search(ctx, *url)

        self.voice_client = ctx.guild.voice_client

        if self.ui.is_auto_stage_available and \
        isinstance(ctx.author.voice.channel, disnake.StageChannel) and \
        bot_itself.voice.suppress:

            try: 
                await bot_itself.edit(suppress=False)
            except: 
                pass

        self.bot.loop.create_task(self._mainloop(ctx))

    async def _SearchFailedHandler(self, ctx: commands.Context, exception: Union[YTDLPExceptions.DownloadError, Exception], url: str):
        # Video Private error handler
        if isinstance(exception, PytubeExceptions.VideoPrivate)\
            or (isinstance(exception, YTDLPExceptions.DownloadError) and "Private Video" in exception.msg):
            
            await self.ui.SearchFailed(ctx, url, "VideoPrivate")
        # Members Only Video error handler
        elif isinstance(exception, PytubeExceptions.MembersOnly):
            await self.ui.SearchFailed(ctx, url, 'MembersOnly')
        # Otherwise, go here
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
            await self.ui.PlayingMsg(ctx, self)
            await self.ui.__UpdateStageTopic__(self)
            await self._play()
            await self.wait()
            try: 
                self.playlist[0].set_source(self.volume_level)
            except: 
                pass
            self.totallength -= self.playlist.rule()

        self.in_mainloop = False
        if self.isskip: 
            await self.ui.PlayingMsg(ctx, self)
        # Reset value
        self.playlist.loop_state = LoopState.NOTHING
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
            if onlybotin: 
                await self.ui.PauseOnAllMemberLeave(ctx, self)
            else: 
                await self.ui.PauseSucceed(ctx, self)
        except Exception as e:
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
            if isinstance(timestamp, str):
                tmp = map(int, reversed(timestamp.split(":")))
                timestamp = 0
                for idx, val in enumerate(tmp):
                    timestamp += (60 ** idx) * val
        except ValueError:  # For ignoring string with ":" like "o:ro"
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

    async def playlist_loop(self, ctx: commands.Context):
        self.playlist.playlist_loop()
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
'''
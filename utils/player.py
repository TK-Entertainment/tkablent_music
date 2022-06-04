from typing import *
import threading, asyncio, gc, weakref

import disnake
from disnake import VoiceClient, VoiceChannel, FFmpegPCMAudio, PCMVolumeTransformer
from disnake.ext import commands

from .playlist import Song, Playlist, LoopState
from .ytdl import YTDL


INF = int(1e18)
bot_version = 'master Branch'

class GuildInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.text_channel: disnake.TextChannel = None
        self._volume_level: int = None
        self._task: asyncio.Task = None
        self._timer: asyncio.Task = None
    
    @property
    def volume_level(self):
        if self._volume_level is None:
            self.fetch()
        return self._volume_level

    @volume_level.setter
    def volume_level(self, value):
        self._volume_level = value
        self.update()

    def fetch(self):
        '''fetch from database'''

    def update(self):
        '''update database'''

class Player(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self._playlist: Playlist = Playlist()
        self._guilds_info: Dict[int, GuildInfo] = dict()

    def __getitem__(self, guild_id) -> GuildInfo:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = GuildInfo(guild_id)
        return self._guilds_info[guild_id] 

    async def _join(self, channel: disnake.VoiceChannel):
        voice_client = channel.guild.voice_client
        if voice_client is None:
            await channel.connect()

    async def _leave(self, guild: disnake.Guild):
        voice_client = guild.voice_client
        if voice_client is not None:
            self._stop(guild)
            await voice_client.disconnect()
            
    async def _search(self, guild: disnake.Guild, url, requester: disnake.Member):
        await self._playlist.add_songs(guild.id, url, requester)
        if self._playlist.is_playlist(url):
            self._start_playlist_process(guild, url, requester)

    def _start_playlist_process(self, guild: disnake.Guild, url, requester: disnake.Member):
        coro = self._playlist.process_playlist(guild.id, url, requester)
        id = self._playlist.get_playlist_id(url)
        task = self.bot.loop.create_task(coro)
            
        self._playlist[guild.id]._playlisttask[id] = task
        task.add_done_callback(lambda task , guild_id=guild.id, playlist_id=id: self._end_playlist_process(guild_id, playlist_id))

    def _end_playlist_process(self, guild_id, id):
        if self._playlist[guild_id]._playlisttask.get(id) is None:
            return
        self._playlist[guild_id]._playlisttask[id].cancel()
        self._playlist[guild_id]._playlisttask.pop(id)

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
    
    def current_timestamp(self, guild: disnake.Guild) -> float:
        voice_client: disnake.VoiceClient = guild.voice_client
        return self._playlist[guild.id].current().left_off + voice_client._player.loops / 50
    
    def _seek(self, guild: disnake.Guild, timestamp: float):
        voice_client: disnake.VoiceClient = guild.voice_client
        if timestamp >= self._playlist[guild.id].current().info['length']:
            voice_client.stop()
            return 'Exceed'
        self._playlist[guild.id].current().seek(timestamp)
        volume_level = self[guild.id].volume_level
        self._playlist[guild.id].current().set_source(volume_level)
        voice_client.source = self._playlist[guild.id].current().source
    
    def _volume(self, guild: disnake.Guild, volume: float):
        voice_client: disnake.VoiceClient = guild.voice_client
        if not voice_client is None:
            self[guild.id].volume_level = volume
            voice_client.source.volume = volume

    async def _play(self, guild: disnake.Guild, channel: disnake.TextChannel):
        self[guild.id].text_channel = channel
        await self._start_mainloop(guild)

    async def _start_mainloop(self, guild: disnake.Guild):
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
            self[guild.id]._timer = None
        if self[guild.id]._task is not None:
            return
        coro = self._mainloop(guild)
        self[guild.id]._task = self.bot.loop.create_task(coro)
        self[guild.id]._task.add_done_callback(lambda task, guild=guild: self._start_timer(guild))
    
    async def _mainloop(self, guild: disnake.Guild):
        # implement in musicbot class for ui support
        '''
        while len(self._playlist[guild.id].order):
            await self[guild.id].text_channel.send('now playing')
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
        if self[guild.id]._task is not None:
            self[guild.id]._task.cancel()
            self[guild.id]._task = None
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
        coro = self._timer(guild)
        self[guild.id]._timer = self.bot.loop.create_task(coro)
    
    async def _timer(self, guild: disnake.Guild):
        await asyncio.sleep(60.0)
        await self._leave(guild)
    
    def _cleanup(self, guild: disnake.Guild):
        if self[guild.id]._task is not None:
            self[guild.id]._task = None
        del self._playlist[guild.id]
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
            self[guild.id]._timer = None


class MusicBot(Player, commands.Cog):
    def __init__(self, bot: commands.Bot):
        Player.__init__(self, bot)
        commands.Cog.__init__(self)
        self.bot: commands.Bot = bot

    @commands.Cog.listener('on_ready')
    async def resolve_ui(self):      
        from .ui import UI
        self.ui = UI(self, bot_version)
    
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
                await self.ui.JoinStage(ctx, ctx.guild.id)
                await self.ui.CreateStageInstance(ctx, ctx.guild.id)
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
                await self.ui.EndStage(self, ctx.guild.id)
            await self._leave(ctx.guild)
            await self.ui.LeaveSucceed(ctx)
        except:
            await self.ui.LeaveFailed(ctx)
    
    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context):
        try:
            self._pause(ctx.guild)
            await self.ui.PauseSucceed(ctx, ctx.guild.id)
        except Exception as e:
            await self.ui.PauseFailed(ctx)
    
    @commands.command(name='resume')
    async def resume(self, ctx: commands.Context):
        try:
            self._resume(ctx.guild)
            await self.ui.ResumeSucceed(ctx, ctx.guild.id)
        except:
            await self.ui.ResumeFailed(ctx)

    @commands.command(name='skip')
    async def skip(self, ctx: commands.Context):
        try:
            self._skip(ctx.guild)
            self.ui.SkipProceed(ctx.guild.id)
        except:
            await self.ui.SkipFailed(ctx)

    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context):
        try:
            self._stop(ctx.guild)
            await self.ui.StopSucceed(ctx)
        except:
            await self.ui.StopFailed(ctx)
    
    @commands.command(name='seek')
    async def seek(self, ctx: commands.Context, timestamp: Union[float, str]):
        try:
            if isinstance(timestamp, str):
                tmp = map(int, reversed(timestamp.split(":")))
                timestamp = 0
                for idx, val in enumerate(tmp):
                    timestamp += (60 ** idx) * val
            self.ui.SeekSucceed(ctx, timestamp)
        except ValueError:  # For ignoring string with ":" like "o:ro"
            await self.ui.SeekFailed(ctx)
            return
        if self._seek(ctx.guild, timestamp) != 'Exceed':
            # await self.ui.SeekSucceed(ctx, timestamp, self)
            return

    @commands.command(name='volume')
    async def volume(self, ctx: commands.Context, percent: Union[float, str]=None):
        if not isinstance(percent, float) and percent is not None:
            await self.ui.VolumeAdjustFailed(ctx)
            return
        await self.ui.VolumeAdjust(ctx, percent)
        if percent is not None:
            self._volume(ctx.guild, percent / 100)

    @commands.command(name="mute", aliases=['quiet', 'shutup'])
    async def mute(self, ctx: commands.Context):
        if self[ctx.guild.id]._volume_level == 0: 
            await self.volume(ctx, 100.0)
        else: 
            await self.volume(ctx, 0.0)
        await self.ui.MuteorUnMute(ctx, self[ctx.guild.id]._volume_level)

    @commands.command(name='restart', aliases=['replay'])
    async def restart(self, ctx: commands.Context):
        try:
            self._seek(0)
            await self.ui.ReplaySucceed(ctx)
        except:
            await self.ui.ReplayFailed(ctx)

    @commands.command(name='loop', aliases=['songloop'])
    async def single_loop(self, ctx: commands.Context, times: Union[int, str]=INF):
        if not isinstance(times, int):
            return await self.ui.SingleLoopFailed(ctx)
        self._playlist.single_loop(ctx.guild.id, times)
        await self.ui.LoopSucceed(ctx)

    @commands.command(name='playlistloop', aliases=['queueloop', 'qloop', 'all_loop'])
    async def playlist_loop(self, ctx: commands.Context):
        self._playlist.playlist_loop(ctx.guild.id)
        await self.ui.LoopSucceed(ctx)

    @commands.command(name='show_queue', aliases=['queuelist', 'queue', 'show'])
    async def show_queue(self, ctx: commands.Context):
        await self.ui.ShowQueue(ctx)

    @commands.command(name='remove', aliases=['queuedel'])
    async def remove(self, ctx: commands.Context, idx: Union[int, str]):
        try:
            await self.ui.RemoveSucceed(ctx, idx)
            self._playlist.pop(ctx.guild.id, idx)
        except (IndexError, TypeError):
            await self.ui.RemoveFailed(ctx)
    
    @commands.command(name='swap')
    async def swap(self, ctx: commands.Context, idx1: Union[int, str], idx2: Union[int, str]):
        try:
            self._playlist.swap(ctx.guild.id, idx1, idx2)
            await self.ui.Embed_SwapSucceed(ctx, idx1, idx2)
        except (IndexError, TypeError) as e:
            print(e)
            await self.ui.SwapFailed(ctx)

    @commands.command(name='move_to', aliases=['insert_to', 'move'])
    async def move_to(self, ctx: commands.Context, origin: Union[int, str], new: Union[int, str]):
        try:
            self._playlist.move_to(ctx.guild.id, origin, new)
            await self.ui.MoveToSucceed(ctx, origin, new)
        except (IndexError, TypeError):
            await self.ui.MoveToFailed(ctx)

    async def search(self, ctx: commands.Context, *url):
        # Get user defined url/keyword
        url = ' '.join(url)

        async with ctx.typing():
            # Show searching UI (if user provide exact url, then it
            # won't send the UI)
            await self.ui.StartSearch(ctx, url)
            # Call search function
            try: 
                await self._search(ctx.guild, url, requester=ctx.message.author)
            except Exception as e:
                # If search failed, sent to handler
                await self.ui.SearchFailed(ctx, url, e)
                return
            # If queue has more than 1 songs, then show the UI
            await self.ui.Embed_AddedToQueue(ctx, url)
    
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
        if self.ui.auto_stage_available(ctx.guild.id) and \
                isinstance(ctx.author.voice.channel, disnake.StageChannel) and \
                bot_itself.voice.suppress:
            try: 
                await bot_itself.edit(suppress=False)
            except: 
                pass

        await self._play(ctx.guild, ctx.channel)

    async def _mainloop(self, guild: disnake.Guild):
        while len(self._playlist[guild.id].order):
            await self.ui.PlayingMsg(self[guild.id].text_channel)
            voice_client: VoiceClient = guild.voice_client
            song = self._playlist[guild.id].current()
            try:
                song.set_ffmpeg_options(0)
                voice_client.play(disnake.FFmpegPCMAudio(song.url, **song.ffmpeg_options))
                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(1.0)
            finally:
                self._playlist.rule(guild.id)
        await self.ui.DonePlaying(self[guild.id].text_channel)
        
    @commands.Cog.listener(name='on_voice_state_update')
    async def end_session(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.id != self.bot.user.id or not (before.channel is not None and after.channel is None):
            return
        guild = member.guild
        channel = self[guild.id].text_channel
        if self[guild.id]._timer is not None and self[guild.id]._timer.done():
            await self.ui.LeaveOnTimeout(channel)
        self._cleanup(guild)
    

    # Error handler
    #@commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        print(error)
        await ctx.send(f'''
            **:no_entry: | 失敗 | UNKNOWNERROR**
            執行指令時發生了一點未知問題，請稍候再嘗試一次
            --------
            技術資訊:
            {error}
            --------
            *若您覺得有Bug或錯誤，請參照上方資訊及代碼回報至 Github*
        ''') 

    @commands.Cog.listener('on_voice_state_update')
    async def _pause_on_being_alone(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        try:
            voice_client: disnake.VoiceClient = member.guild.voice_client
            if voice_client is None:
                return
            if len(voice_client.channel.members) == 1 and not voice_client.is_paused():
                await self.ui.PauseOnAllMemberLeave(self[member.guild.id].text_channel, self)
                self._pause(member.guild)
        except: 
            pass

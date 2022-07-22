from typing import *
import asyncio, json, os

import discord
from discord.ext import commands
from discord import VoiceClient, app_commands

import wavelink
from .playlist import Playlist
from .command import Command

INF = int(1e18)
bot_version = 'lavalink-test Branch'

class GuildInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.text_channel: discord.TextChannel = None
        self._volume_level: int = None
        self._multitype_remembered: bool = None
        self._multitype_choice: str = None
        self._task: asyncio.Task = None
        self._timer: asyncio.Task = None
    
    @property
    def volume_level(self):
        if self._volume_level is None:
            self._volume_level = self.fetch('volume_level')
        return self._volume_level

    @volume_level.setter
    def volume_level(self, value):
        self._volume_level = value
        self.update('volume_level', value)

    @property
    def multitype_remembered(self):
        if self._multitype_remembered is None:
            self._multitype_remembered = self.fetch('multitype_remembered')
        return self._multitype_remembered

    @multitype_remembered.setter
    def multitype_remembered(self, value):
        self._multitype_remembered = value
        self.update('multitype_remembered', value)

    @property
    def multitype_choice(self):
        if self._multitype_choice is None:
            self._multitype_choice = self.fetch('multitype_choice')
        return self._multitype_choice

    @multitype_choice.setter
    def multitype_choice(self, value):
        self._multitype_choice = value
        self.update('multitype_choice', value)

    def fetch(self, key: str) -> not None:
        '''fetch from database'''

        with open(r'utils\data.json', 'r') as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None or data[str(self.guild_id)].get(key) is None:
            return data['default'][key]
        return data[str(self.guild_id)][key]

    def update(self, key: str, value: str) -> None:
        '''update database'''

        with open(r'utils\data.json', 'r') as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None:
            data[str(self.guild_id)] = dict()
        data[str(self.guild_id)][key] = value
        with open(r'utils\data.json', 'w') as f:
            json.dump(data, f)

class Player:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._playlist: Playlist = Playlist()
        self._guilds_info: Dict[int, GuildInfo] = dict()
        self.playnode: wavelink.Node = None

    def __getitem__(self, guild_id) -> GuildInfo:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = GuildInfo(guild_id)
        return self._guilds_info[guild_id] 

    def _start_daemon(self, bot, host, port, password):
        return wavelink.NodePool.create_node(
            bot=bot,
            host=host,
            port=port,
            password=password,
            identifier="PlaybackServer"
        )

    async def _join(self, channel: discord.VoiceChannel):
        voice_client = channel.guild.voice_client
        if voice_client is None:
            await channel.connect(cls=wavelink.Player)

    async def _leave(self, guild: discord.Guild):
        voice_client = guild.voice_client
        if voice_client is not None:
            await self._stop(guild)
            await voice_client.disconnect()
            
    async def _search(self, guild: discord.Guild, trackinfo, requester: discord.Member):
        await self._playlist.add_songs(guild.id, trackinfo, requester)

    async def _pause(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if not voice_client.is_paused() and voice_client.is_playing():
            await voice_client.pause()

    async def _resume(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client.is_paused():
            await voice_client.resume()

    async def _skip(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            await voice_client.stop()
        self._playlist[guild].times = 0
    
    async def _stop(self, guild: discord.Guild):
        self._playlist[guild.id].clear()
        await self._skip(guild)
    
    async def _seek(self, guild: discord.Guild, timestamp: float):
        voice_client: wavelink.Player = guild.voice_client
        if timestamp >= self._playlist[guild.id].current().length:
            await voice_client.stop()
        await voice_client.seek(timestamp * 1000)
    
    async def _volume(self, guild: discord.Guild, volume: float):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client is not None:
            mute = volume == 0
            if mute:
                volume = 1e-5
            else:
                self[guild.id].volume_level = volume
            await voice_client.set_volume(volume)
            await self.bot.ws.voice_state(guild.id, voice_client.channel.id, self_mute=mute)
            
    async def _play(self, guild: discord.Guild, channel: discord.TextChannel):
        self[guild.id].text_channel = channel
        await self._start_mainloop(guild)

    async def _start_mainloop(self, guild: discord.Guild):
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
            self[guild.id]._timer = None
        if self[guild.id]._task is not None:
            return
        coro = self._mainloop(guild)
        self[guild.id]._task = self.bot.loop.create_task(coro)
        self[guild.id]._task.add_done_callback(lambda task, guild=guild: self._start_timer(guild))
    
    async def _mainloop(self, guild: discord.Guild):
        # implement in musicbot class for ui support
        '''
        while len(self._playlist[guild.id].order):
            await self[guild.id].text_channel.send('now playing')
            voice_client: VoiceClient = guild.voice_client
            song = self._playlist[guild.id].current()
            try:
                voice_client.play(discord.FFmpegPCMAudio(song.url))
                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(1.0)
            finally:
                self._playlist.rule(guild.id)
        '''
        raise NotImplementedError

    def _start_timer(self, guild: discord.Guild):
        if self[guild.id]._task is not None:
            self[guild.id]._task.cancel()
            self[guild.id]._task = None
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
        coro = self._timer(guild)
        self[guild.id]._timer = self.bot.loop.create_task(coro)
    
    async def _timer(self, guild: discord.Guild):
        await asyncio.sleep(60.0)
        await self._leave(guild)
    
    def _cleanup(self, guild: discord.Guild):
        if self[guild.id]._task is not None:
            self[guild.id]._task = None
        del self._playlist[guild.id]
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
            self[guild.id]._timer = None

class MusicCog(Player, commands.Cog):
    def __init__(self, bot: commands.Bot):
        Player.__init__(self, bot)
        commands.Cog.__init__(self)
        self.bot: commands.Bot = bot

    async def resolve_ui(self):   
        from .ui import UI
        self.ui = UI(self, bot_version)

    @app_commands.command(name="reportbug", description="🐛 | 在這裡回報你遇到的錯誤吧！")
    async def reportbug(self, interaction: discord.Interaction):
        await self.ui.Interaction_BugReportingModal(interaction, interaction.guild)

    ##############################################

    async def mtsetup(self, command: Union[commands.Context, discord.Interaction]):
        command: Command = Command(command)
        await self.ui.MultiTypeSetup(command)

    @commands.command(name='playwith')
    async def _c_mtsetup(self, ctx: commands.Context):
        await self.mtsetup(ctx)

    @app_commands.command(name='playwith', description="⚙️ | 設定對於混合連結的預設動作")
    async def _i_mtsetup(self, interaction: discord.Interaction):
        await self.mtsetup(interaction)
    ##############################################

    async def help(self, command: Union[commands.Context, discord.Interaction]):
        command: Command = Command(command)
        await self.ui.Help(command)

    @commands.command(name='help')
    async def _c_help(self, ctx: commands.Context):
        await self.help(ctx)

    @app_commands.command(name='help', description="❓ | 不知道怎麼使用我嗎？來這裡就對了~")
    async def _i_help(self, interaction: discord.Interaction):
        await self.help(interaction)

    ##############################################

    async def ensure_stage_status(self, command: Command):
        '''a helper function for opening a stage'''

        if not isinstance(command.author.voice.channel, discord.StageChannel):
            return

        bot_itself: discord.Member = await command.guild.fetch_member(self.bot.user.id)
        auto_stage_vaildation = self.ui.auto_stage_available(command.guild.id)
        
        if command.author.voice.channel.instance is None:
            await self.ui.CreateStageInstance(command, command.guild.id)
        
        if auto_stage_vaildation and bot_itself.voice.suppress:
            try: 
                await bot_itself.edit(suppress=False)
            except: 
                auto_stage_vaildation = False

    async def rejoin(self, command: Command):
        voice_client: wavelink.Player = command.guild.voice_client
        # Get the bot former playing state
        former: discord.VoiceChannel = voice_client.channel
        former_state: bool = voice_client.is_paused()
        # To determine is the music paused before rejoining or not
        if not former_state: 
            await self._pause(command.guild)
        # Moving itself to author's channel
        await voice_client.move_to(command.author.voice.channel)
        if isinstance(command.author.voice.channel, discord.StageChannel):
            await self.ensure_stage_status(command)

        # If paused before rejoining, resume the music
        if not former_state: 
            await self._resume(command.guild)
        # Send a rejoin message
        await self.ui.RejoinNormal(command)
        # If the former channel is a discord.StageInstance which is the stage
        # channel with topics, end that stage instance
        if isinstance(former, discord.StageChannel) and \
                isinstance(former.instance, discord.StageInstance):
            await self.ui.EndStage(command.guild.id)

    async def join(self, command):
        if not isinstance(command, Command):
            command: Optional[Command] = Command(command)

        voice_client: wavelink.Player = command.guild.voice_client
        if isinstance(voice_client, wavelink.Player):
            if voice_client.channel != command.author.voice.channel:
                await self.rejoin(command)
            else:
                # If bot joined the same channel, send a message to notice user
                await self.ui.JoinAlready(command)
            return
        try:
            await self._join(command.author.voice.channel)
            voice_client: wavelink.Player = command.guild.voice_client
            if isinstance(voice_client.channel, discord.StageChannel):
                await self.ensure_stage_status(command)
                await self.ui.JoinStage(command, command.guild.id)
            else:
                await self.ui.JoinNormal(command)
        except Exception as e:
            await self.ui.JoinFailed(command, e)

    @commands.command(name='join')
    async def _c_join(self, ctx: commands.Context):
        await self.join(ctx)
    
    @app_commands.command(name='join', description='📥 | 將我加入目前您所在的頻道')
    async def _i_join(self, interaction: discord.Interaction):
        await self.join(interaction)

    ##############################################

    async def leave(self, command):
        if not isinstance(command, Command):
            command: Optional[Command] = Command(command)

        voice_client: wavelink.Player = command.guild.voice_client
        try:
            if isinstance(voice_client.channel, discord.StageChannel) and \
                    isinstance(voice_client.channel.instance, discord.StageInstance):
                await self.ui.EndStage(command.guild.id)
            await self._leave(command.guild)
            await self.ui.LeaveSucceed(command)
        except Exception as e:
            await self.ui.LeaveFailed(command, e)

    @commands.command(name='leave', aliases=['quit'])
    async def _c_leave(self, ctx: commands.Context):
        await self.leave(ctx)

    @app_commands.command(name='leave', description='📤 | 讓我從目前您所在的頻道離開')
    async def _i_leave(self, interaction: discord.Interaction):
        await self.leave(interaction)

    ##############################################

    async def pause(self, command):
        if not isinstance(command, Command):
            command: Optional[Command] = Command(command)
        try:
            await self._pause(command.guild)
            await self.ui.PauseSucceed(command, command.guild.id)
        except Exception as e:
            await self.ui.PauseFailed(command, e)

    @commands.command(name='pause')
    async def _c_pause(self, ctx: commands.Context):
        await self.pause(ctx)

    @app_commands.command(name='pause', description='⏸️ | 暫停目前播放的音樂')
    async def _i_pause(self, interaction: discord.Interaction):
        await self.pause(interaction)

    ##############################################

    async def resume(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            if isinstance(command.channel, discord.StageChannel):
                await self.ensure_stage_status(command)
            await self._resume(command.guild)
            await self.ui.ResumeSucceed(command, command.guild.id)
        except Exception as e:
            await self.ui.ResumeFailed(command, e)

    @commands.command(name='resume')
    async def _c_resume(self, ctx: commands.Context):
        await self.resume(ctx)

    @app_commands.command(name='resume', description='▶️ | 繼續播放目前暫停的歌曲')
    async def _i_resume(self, interaction: discord.Interaction):
        await self.resume(interaction)

    ##############################################

    async def skip(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            await self._skip(command.guild)
            self.ui.SkipProceed(command.guild.id)
            if command.is_response() is not None and not command.is_response():
                await command.send("⠀")
        except Exception as e:
            await self.ui.SkipFailed(command, e)

    @commands.command(name='skip')
    async def _c_skip(self, ctx: commands.Context):
        await self.skip(ctx)
    
    @app_commands.command(name='skip', description='⏩ | 跳過目前播放的歌曲')
    async def _i_skip(self, interaction: discord.Interaction):
        await self.skip(interaction)

    ##############################################

    async def stop(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            await self._stop(command.guild)
            await self.ui.StopSucceed(command)
        except Exception as e:
            await self.ui.StopFailed(command, e)

    @commands.command(name='stop')
    async def _c_stop(self, ctx: commands.Context):
        await self.stop(ctx)

    @app_commands.command(name='stop', description='⏹️ | 停止音樂並清除待播清單')
    async def _i_stop(self, interaction: discord.Interaction):
        await self.stop(interaction)

    ##############################################

    async def seek(self, command, timestamp: Union[float, str]):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            if isinstance(timestamp, str):
                tmp = map(int, reversed(timestamp.split(":")))
                timestamp = 0
                for idx, val in enumerate(tmp):
                    timestamp += (60 ** idx) * val
            await self._seek(command.guild, timestamp)
            await self.ui.SeekSucceed(command, timestamp)
        except ValueError as e:  # For ignoring string with ":" like "o:ro"
            await self.ui.SeekFailed(command, e)
            return

    @commands.command(name='seek')
    async def _c_seek(self, ctx: commands.Context, timestamp: Union[float, str]):
        await self.seek(ctx, timestamp)

    @app_commands.command(name='seek', description='⏲️ | 跳轉你想要聽的地方')
    @app_commands.describe(timestamp='目標時間 (時間戳格式 0:20) 或 (秒數 20)')
    @app_commands.rename(timestamp='目標時間')
    async def _i_seek(self, interaction: discord.Interaction, timestamp: str):
        await self.seek(interaction, timestamp)

    ##############################################

    # async def volume(self, command, percent: Union[int, str]=None):
    #     if not isinstance(command, Command):
    #         command: Command = Command(command)
    #     if not isinstance(percent, int) and percent is not None or command.guild.voice_client is None:
    #         await self.ui.VolumeAdjustFailed(command)
    #         return 'Failed'
    #     if percent is not None:
    #         percent = max(0, min(200, percent))
    #     await self.ui.VolumeAdjust(command, percent)
    #     if percent is not None:
    #         await self._volume(command.guild, percent)

    # @commands.command(name='volume')
    # async def _c_volume(self, ctx: commands.Context, percent: Union[int, str]=None):
    #     await self.volume(ctx, percent)

    # @app_commands.command(name='volume', description='🔊 | 太大聲？還是太小聲了？還是想知道目前音量？')
    # @app_commands.describe(percent='音量 (使用百份比單位，不輸入此項來取得目前音量)')
    # @app_commands.rename(percent='音量')
    # async def _i_volume(self, interaction: discord.Interaction, percent: int=None):
    #     await self.volume(interaction, percent)

    ##############################################

    async def restart(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            await self._seek(0)
            await self.ui.ReplaySucceed(command)
        except Exception as e:
            await self.ui.ReplayFailed(command, e)

    @commands.command(name='restart', aliases=['replay'])
    async def _c_restart(self, ctx: commands.Context):
        await self.restart(ctx)

    @app_commands.command(name='restart', description='🔁 | 重頭開始播放目前的歌曲')
    async def _i_restart(self, interaction: discord.Interaction):
        await self.restart(interaction)

    ##############################################

    async def single_loop(self, command, times: Union[int, str]=INF):
        if not isinstance(command, Command):
            command: Command = Command(command)
        if not isinstance(times, int):
            return await self.ui.SingleLoopFailed(command)
        self._playlist.single_loop(command.guild.id, times)
        await self.ui.LoopSucceed(command)

    @commands.command(name='loop', aliases=['songloop'])
    async def _c_single_loop(self, ctx: commands.Context, times: Union[int, str]=INF):
        await self.single_loop(ctx, times)

    @app_commands.command(name='loop', description='🔂 | 循環播放目前的歌曲')
    @app_commands.describe(times='重複播放次數 (不填寫次數以啟動無限次數循環)')
    @app_commands.rename(times='重複播放次數')
    async def _i_single_loop(self, interaction: discord.Interaction, times: int=INF):
        await self.single_loop(interaction, times)

    ##############################################

    async def playlist_loop(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        self._playlist.playlist_loop(command.guild.id)
        await self.ui.LoopSucceed(command)

    @commands.command(name='playlistloop', aliases=['queueloop', 'qloop', 'all_loop'])
    async def _c_playlist_loop(self, ctx: commands.Context):
        await self.playlist_loop(ctx)

    @app_commands.command(name='queueloop', description='🔁 | 循環播放目前的待播清單')
    async def _i_playlist_loop(self, interaction: discord.Interaction):
        await self.playlist_loop(interaction)

    ##############################################

    async def show_queue(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        await self.ui.ShowQueue(command)

    @commands.command(name='show_queue', aliases=['queuelist', 'queue', 'show'])
    async def _c_show_queue(self, ctx: commands.Context):
        await self.show_queue(ctx)

    @app_commands.command(name='queue', description='ℹ️ | 列出目前的待播清單')
    async def _i_show_queue(self, interaction: discord.Interaction):
        await self.show_queue(interaction)

    ##############################################    

    async def remove(self, command, idx: Union[int, str]):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            await self.ui.RemoveSucceed(command, idx)
            self._playlist.pop(command.guild.id, idx)
        except (IndexError, TypeError) as e:
            await self.ui.RemoveFailed(command, e)

    @commands.command(name='remove', aliases=['queuedel'])
    async def _c_remove(self, ctx: commands.Context, idx: Union[int, str]):
        await self.remove(ctx, idx)

    @app_commands.command(name='remove', description='🗑️ | 刪除待播清單中的一首歌')
    @app_commands.describe(idx='欲刪除歌曲之位置 (可用 %queue 或 /queue 得知位置代號)')
    @app_commands.rename(idx='刪除歌曲位置')
    async def _i_remove(self, interaction: discord.Interaction, idx: int):
        await self.remove(interaction, idx)

   ##############################################

    async def swap(self, command, idx1: Union[int, str], idx2: Union[int, str]):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            self._playlist.swap(command.guild.id, idx1, idx2)
            await self.ui.Embed_SwapSucceed(command, idx1, idx2)
        except (IndexError, TypeError) as e:
            await self.ui.SwapFailed(command, e)

    @commands.command(name='swap')
    async def _c_swap(self, ctx: commands.Context, idx1: Union[int, str], idx2: Union[int, str]):
        await self.swap(ctx, idx1, idx2)

    @app_commands.command(name='swap', description='🔄 | 交換待播清單中兩首歌的位置')
    @app_commands.describe(idx1='歌曲1 位置 (可用 %queue 或 /queue 得知位置代號)', idx2='歌曲2 位置 (可用 %queue 或 /queue 得知位置代號)')
    @app_commands.rename(idx1='歌曲1位置', idx2='歌曲2位置')
    async def _i_swap(self, interaction: discord.Interaction, idx1: int, idx2: int):
        await self.swap(interaction, idx1, idx2)
    ##############################################

    async def move_to(self, command, origin: Union[int, str], new: Union[int, str]):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            self._playlist.move_to(command.guild.id, origin, new)
            await self.ui.MoveToSucceed(command, origin, new)
        except (IndexError, TypeError) as e:
            await self.ui.MoveToFailed(command, e)

    @commands.command(name='move_to', aliases=['insert_to', 'move'])
    async def _c_move_to(self, ctx: commands.Context, origin: Union[int, str], new: Union[int, str]):
        await self.move_to(ctx, origin, new)

    @app_commands.command(name='move', description='🔄 | 移動待播清單中一首歌的位置')
    @app_commands.describe(origin='原位置 (可用 %queue 或 /queue 得知位置代號)', new='目標位置 (可用 %queue 或 /queue 得知位置代號)')
    @app_commands.rename(origin='原位置', new='目標位置')
    async def _i_move_to(self, interaction: discord.Interaction, origin: int, new: int):
        await self.move_to(interaction, origin, new)

    ##############################################

    async def process(self, command: Command,
                            trackinfo: Union[
                                wavelink.YouTubeTrack,
                                wavelink.YouTubeMusicTrack,
                                wavelink.SoundCloudTrack,
                                wavelink.YouTubePlaylist
                            ]):

        # Call search function
        try: 
            await self._search(command.guild, trackinfo, requester=command.author)
        except Exception as e:
            # If search failed, sent to handler
            await self.ui.SearchFailed(command, e)
            return
        # If queue has more than 1 songs, then show the UI
        await self.ui.Embed_AddedToQueue(command, trackinfo, requester=command.author)
    
    async def play(self, command, trackinfo: Union[
                                wavelink.YouTubeTrack,
                                wavelink.YouTubeMusicTrack,
                                wavelink.SoundCloudTrack,
                                wavelink.YouTubePlaylist
                            ]):
        # Try to make bot join author's channel
        if command.command_type == 'Context':
            await command.channel.typing()
        voice_client: wavelink.Player = command.guild.voice_client
        if not isinstance(voice_client, wavelink.Player) or \
                voice_client.channel != command.author.voice.channel:
            await self.join(command)
            voice_client = command.guild.voice_client
            if not isinstance(voice_client, wavelink.Player):
                return

        # Start search process
        await self.process(command, trackinfo)

        await self._play(command.guild, command.channel)
        if command.command_type == 'Interaction' and command.is_response is not None and not command.is_response():
            await command.send("⠀")

    @commands.command(name='play', aliases=['p', 'P'])
    async def _c_play(self, ctx: commands.Context, *, search):
        command: Command = Command(ctx)
        if "list" in search \
                and "watch" in search \
                and "http" in search \
                and "//" in search:
            if self[command.guild.id].multitype_remembered:
                await self._get_track(command, search, self[command.guild.id].multitype_choice)   
            else:
                await self.ui.MultiTypeNotify(command, search)
        else:
            await self._get_track(command, search, 'normal')       

    @app_commands.command(name='play', description='🎶 | 想聽音樂？來這邊點歌吧~')
    @app_commands.describe(search='欲播放之影片網址或關鍵字 (支援 Youtube / SoundCloud)')
    @app_commands.rename(search='影片網址或關鍵字')
    async def _i_play(self, interaction: discord.Interaction, search: str):
        command: Command = Command(interaction)
        if "list" in search \
                and "watch" in search \
                and "http" in search \
                and "//" in search:
            if self[command.guild.id].multitype_remembered:
                await self._get_track(command, search, self[command.guild.id].multitype_choice)   
            else:
                await self.ui.MultiTypeNotify(command, search)
        else:
            await self._get_track(command, search, 'normal')       

    async def _get_track(self, command, search: str, choice):
        extract = search.split('&')
        if choice == 'videoonly':
            url = extract[0]
        elif choice == 'playlist':
            url = f'https://www.youtube.com/playlist?{extract[1]}'
        else:
            url = search
        for trackmethod in [
                                wavelink.YouTubePlaylist,
                                wavelink.LocalTrack,
                                wavelink.YouTubeTrack,
                                wavelink.YouTubeMusicTrack,
                                wavelink.SoundCloudTrack,
                            ]:
            try:
                # SearchableTrack.convert(ctx, query)
                # ctx here actually useless
                trackinfo = await trackmethod.convert(command, url)
            except Exception:
                # When there is no result for provided method
                # Then change to next method to search
                trackinfo = None
                pass
            if trackinfo is not None:
                break
        
        if trackinfo is None:
            await self.ui.SearchFailed(command, url)

        await self.play(command, trackinfo)

    ##############################

    async def _mainloop(self, guild: discord.Guild):
        while len(self._playlist[guild.id].order):
            voice_client: wavelink.Player = guild.voice_client
            song = self._playlist[guild.id].current()
            try:
                try:
                    await voice_client.play(song)
                    await self.ui.PlayingMsg(self[guild.id].text_channel)
                except Exception as e:
                    await self.ui.PlayingError(self[guild.id].text_channel, e)

                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(0.1)
            finally:
                self._playlist.rule(guild.id)
        await self.ui.DonePlaying(self[guild.id].text_channel)
        
    @commands.Cog.listener(name='on_voice_state_update')
    async def end_session(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
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
    async def _pause_on_being_alone(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        try:
            voice_client: wavelink.Player = member.guild.voice_client
            if voice_client is None:
                if not voice_client.is_playing() or not voice_client.is_paused():
                    await self._stop(member.guild)
                    self._cleanup(member.guild)
                    return
            if len(voice_client.channel.members) == 1 and not voice_client.is_paused():
                await self.ui.PauseOnAllMemberLeave(self[member.guild.id].text_channel, member.guild.id)
                await self._pause(member.guild)
        except: 
            pass

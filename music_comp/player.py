from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from typing import *
import asyncio, os
import dotenv
import validators
import logging
from sentry_sdk import capture_exception

import discord
from discord.ext import commands
from discord import app_commands

import wavelink
from .playlist import Playlist, LoopState
from .utils.storage import GuildInfo
from .emoji import Emoji

INF = int(1e18)

class Player:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._playlist: Playlist = Playlist()
        self._guilds_info: Dict[int, GuildInfo] = dict()

    def __getitem__(self, guild_id) -> GuildInfo:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = GuildInfo(guild_id)
        return self._guilds_info[guild_id]

    ############
    # Daemon setup (Wavelink, cache and etc.)
    ############
    async def _create_daemon(self):
        # Env value setup
        # Wavelink needed value
        TW_HOST = os.getenv("WAVELINK_TW_HOST")
        BILI_HOST = os.getenv("WAVELINK_BILI_HOST")
        LOCAL_SEARCH_HOST_1 = os.getenv("WAVELINK_SEARCH_HOST_1")
        LOCAL_SEARCH_HOST_2 = os.getenv("WAVELINK_SEARCH_HOST_2")
        PORT = os.getenv("WAVELINK_PORT")
        SEARCH_PORT_1 = os.getenv("WAVELINK_SEARCH_PORT_1")
        SEARCH_PORT_2 = os.getenv("WAVELINK_SEARCH_PORT_2")
        PASSWORD = os.getenv("WAVELINK_PWD")

        # Define Wavelink Host
        mainplayhost = wavelink.Node(
            identifier="TW_PlayBackNode",
            uri=f"http://{TW_HOST}:{PORT}",
            password=PASSWORD,
        )
        bilibili_host = wavelink.Node(
            identifier="BilibiliNode",
            uri=f"http://{BILI_HOST}:{PORT}",
            password=PASSWORD,
        )
        searchhost_1 = wavelink.Node(
            identifier="SearchNode_1",
            uri=f"http://{LOCAL_SEARCH_HOST_1}:{SEARCH_PORT_1}",
            password=PASSWORD,
        )
        searchhost_2 = wavelink.Node(
            identifier="SearchNode_2",
            uri=f"http://{LOCAL_SEARCH_HOST_2}:{SEARCH_PORT_2}",
            password=PASSWORD,
        )

        # Wavelink connection establishing
        await wavelink.Pool.connect(
            nodes=[mainplayhost, bilibili_host, searchhost_1, searchhost_2],
            client=self.bot,
        )

    #############
    # Join Core #
    #############
    async def _join(self, channel: discord.VoiceChannel):
        voice_client = channel.guild.voice_client
        mainplayhost = wavelink.Pool.get_node("TW_PlayBackNode")
        backupplayhost = wavelink.Pool.get_node("BilibiliNode")
        if voice_client is None:
            if mainplayhost.status == wavelink.NodeStatus.CONNECTED:
                player = wavelink.Player(nodes=[mainplayhost])
            else:
                player = wavelink.Player(nodes=[backupplayhost])
            player.inactive_timeout = 600
            await channel.connect(cls=player, self_deaf=True)

    ##############
    # Leave Core #
    ##############
    async def _leave(self, guild: discord.Guild):
        voice_client = guild.voice_client
        if voice_client is not None:
            await self._stop(guild)
            await voice_client.disconnect()

    ###############
    # Search Core #
    ###############
    async def _search(self, guild: discord.Guild, trackinfo, requester: discord.Member):
        await self._playlist.add_songs(guild.id, trackinfo, requester)

    ##############
    # Pause Core #
    ##############
    async def _pause(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if not voice_client.paused and voice_client.playing:
            await voice_client.pause(True)

    ###############
    # Resume Core #
    ###############
    async def _resume(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client.paused:
            await voice_client.pause(False)

    #############
    # Skip Core #
    #############
    async def _skip(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client.playing or voice_client.paused:
            await voice_client.skip()
            self._playlist[guild.id].times = 0
            if self._playlist[guild.id].loop_state == LoopState.SINGLEINF:
                self._playlist[guild.id].loop_state = LoopState.NOTHING

    #############
    # Stop Core #
    #############
    async def _stop(self, guild: discord.Guild):
        self._playlist[guild.id].clear()
        self._cleanup(guild)
        await self._skip(guild)

    #############
    # Seek Core #
    #############
    async def _seek(self, guild: discord.Guild, timestamp: float):
        voice_client: wavelink.Player = guild.voice_client
        if timestamp >= (self._playlist[guild.id].current().length) / 1000:
            await voice_client.skip()
            return
        await voice_client.seek(timestamp * 1000)

    ###############
    # Volume Core # (Currently not working)
    ###############
    async def _volume(self, guild: discord.Guild, volume: float):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client is not None:
            mute = volume == 0
            if mute:
                volume = 1e-5
            else:
                self[guild.id].volume_level = volume
            await voice_client.set_volume(volume)
            await self.bot.ws.voice_state(
                guild.id, voice_client.channel.id, self_mute=mute
            )

    #############
    # Play Core #
    #############
    async def _play(self, guild: discord.Guild, channel: discord.TextChannel):
        self[guild.id].text_channel = channel
        voice_client: wavelink.Player = guild.voice_client

        if (not voice_client.paused) and (voice_client.current is None) and (len(self._playlist[guild.id].order) > 0):
            await voice_client.play(self._playlist[guild.id].current())

    ########
    # Misc #
    ########
    def _cleanup(self, guild: discord.Guild):
        if self[guild.id]._task is not None:
            self[guild.id]._task = None
        del self._playlist[guild.id]

# ========================================================================================================

class MusicCog(Player, commands.Cog):
    def __init__(self, bot: commands.Bot, bot_version):
        Player.__init__(self, bot)
        commands.Cog.__init__(self)
        self.bot: commands.Bot = bot
        self.bot_version: str = bot_version
        self.ui = None
        self.auto_stage_available = None
        self.ui_guild_info = None
        self._sec_to_hms = None
        self.track_helper = None

    async def post_boot(self):
        from .ui import UI, auto_stage_available, guild_info, _sec_to_hms
        from .utils.track_helper import TrackHelper

        self.ui = UI(self, self.bot_version)
        self.auto_stage_available = auto_stage_available
        self.ui_guild_info = guild_info
        self._sec_to_hms = _sec_to_hms
        self.track_helper = TrackHelper(self.ui, self._playlist)

        from .ui import groupbutton
        self.groupbutton = groupbutton

    ############
    # sessdata refresh (currently not working)
    ############
    async def _refresh_sessdata(self):
        while True:
            need_refresh = await self.track_helper._bilibilic.check_refresh()
            if need_refresh:
                await self.track_helper._bilibilic.refresh()
                dotenv.set_key(
                    dotenv_path=rf"{os.getcwd()}/.env",
                    key_to_set="SESSDATA",
                    value_to_set=self.track_helper._bilibilic.sessdata,
                )
                dotenv.set_key(
                    dotenv_path=rf"{os.getcwd()}/.env",
                    key_to_set="BILI_JCT",
                    value_to_set=self.track_helper._bilibilic.bili_jct,
                )
                dotenv.set_key(
                    dotenv_path=rf"{os.getcwd()}/.env",
                    key_to_set="BUVID3",
                    value_to_set=self.track_helper._bilibilic.buvid3,
                )
            await asyncio.sleep(120)

    @app_commands.command(name="help", description="❓ | 不知道怎麼使用我嗎？來這裡就對了~")
    async def help(self, interaction: discord.Interaction):
        await self.ui.Changelogs.SendChangelogs(interaction)
        await self.ui.Help.Help(interaction)

    ##############################################

    @app_commands.command(name="playwith", description="⚙️ | 設定對於混合連結的預設動作")
    async def mtsetup(self, interaction: discord.Interaction):
        await self.ui.PlayerControl.MultiTypeSetup(interaction)

    ##############################################

    async def ensure_stage_status(self, interaction: discord.Interaction):
        """a helper function for opening a stage"""

        if not isinstance(interaction.user.voice.channel, discord.StageChannel):
            return

        bot_itself: discord.Member = await interaction.guild.fetch_member(
            self.bot.user.id
        )

        if interaction.user.voice.channel.instance is None:
            await self.ui.Stage.CreateStageInstance(interaction, interaction.guild.id)

        if self.auto_stage_available(interaction.guild.id) and bot_itself.voice.suppress:
            try:
                await bot_itself.edit(suppress=False)
            except Exception as e:
                self.ui_guild_info(interaction.guild.id).auto_stage_available = False
                logging.warning(f"Failed to unsuppress bot: {e}")

    ##############################################

    async def rejoin(self, interaction: discord.Interaction):
        voice_client: wavelink.Player = interaction.guild.voice_client
        # Get the bot former playing state
        former: discord.VoiceChannel = voice_client.channel
        former_paused: bool = voice_client.paused

        # To determine is the music paused before rejoining or not
        if not former_paused:
            await self._pause(interaction.guild)

        # Moving itself to author's channel
        await voice_client.move_to(interaction.user.voice.channel)
        if isinstance(interaction.user.voice.channel, discord.StageChannel):
            await self.ensure_stage_status(interaction)

        # If not paused before rejoining, resume the music
        if not former_paused:
            await self._resume(interaction.guild)

        # Send a rejoin message
        await self.ui.Join.RejoinNormal(interaction)

        # If the former channel is a discord.StageInstance which is the stage
        # channel with topics, end that stage instance
        if isinstance(former, discord.StageChannel) and isinstance(
            former.instance, discord.StageInstance
        ):
            await self.ui.Stage.EndStage(interaction.guild.id)

    ##############################################

    async def join(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if isinstance(voice_client, wavelink.Player):
            if voice_client.channel != interaction.user.voice.channel:
                await self.rejoin(interaction)
            else:
                # If bot joined the same channel, send a message to notice user
                await self.ui.Join.JoinAlready(interaction)
            return
        try:
            await self._join(interaction.user.voice.channel)
            voice_client: wavelink.Player = interaction.guild.voice_client
            if isinstance(voice_client.channel, discord.StageChannel):
                await self.ensure_stage_status(interaction)
                await self.ui.Join.JoinStage(interaction, interaction.guild.id)
            else:
                await self.ui.Join.JoinNormal(interaction)
        except Exception as e:
            await self.ui.Join.JoinFailed(interaction, e)

    @app_commands.command(name="join", description="📥 | 將我加入目前您所在的頻道")
    async def _join_s(self, interaction: discord.Interaction):
        await self.join(interaction)

    ##############################################

    @app_commands.command(name="leave", description="📤 | 讓我從目前您所在的頻道離開")
    async def leave(self, interaction: discord.Interaction):
        voice_client: wavelink.Player = interaction.guild.voice_client
        try:
            if isinstance(voice_client.channel, discord.StageChannel) and isinstance(
                voice_client.channel.instance, discord.StageInstance
            ):
                await self.ui.Stage.EndStage(interaction.guild.id)
            await self._leave(interaction.guild)
            await self.ui.Leave.LeaveSucceed(interaction)
        except Exception as e:
            await self.ui.Leave.LeaveFailed(interaction, e)

    ##############################################

    @app_commands.command(name="pause", description="⏸️ | 暫停目前播放的音樂")
    async def pause(self, interaction: discord.Interaction):
        try:
            await self._pause(interaction.guild)
            await self.ui.PlayerControl.PauseSucceed(interaction, interaction.guild.id)
        except Exception as e:
            await self.ui.PlayerControl.PauseFailed(interaction, e)

    ##############################################

    @app_commands.command(name="resume", description="▶️ | 繼續播放目前暫停的歌曲")
    async def resume(self, interaction: discord.Interaction):
        try:
            if isinstance(interaction.channel, discord.StageChannel):
                await self.ensure_stage_status(interaction)
            await self._resume(interaction.guild)
            await self.ui.PlayerControl.ResumeSucceed(interaction, interaction.guild.id)
        except Exception as e:
            await self.ui.PlayerControl.ResumeFailed(interaction, e)

    ##############################################

    @app_commands.command(name="skip", description="⏩ | 跳過目前播放的歌曲")
    async def skip(self, interaction: discord.Interaction):
        try:
            await self._skip(interaction.guild)
            self.ui.PlayerControl.SkipProceed(interaction.guild.id)
            if not interaction.response.is_done():
                await interaction.response.send_message("⠀")
                tmpmsg = await interaction.original_response()
                await tmpmsg.delete()
        except Exception as e:
            await self.ui.PlayerControl.SkipFailed(interaction, e)

    ##############################################

    @app_commands.command(name="np", description="▶️ | 查看現在在播放什麼!")
    async def nowplaying(self, interaction: discord.Interaction):
        await self.ui.Changelogs.SendChangelogs(interaction)
        await self.ui.PlayerControl.NowPlaying(interaction)

    ##############################################

    @app_commands.command(name="stop", description="⏹️ | 停止音樂並清除待播清單")
    async def stop(self, interaction: discord.Interaction):
        await self.ui.Changelogs.SendChangelogs(interaction)
        try:
            await self._stop(interaction.guild)
            await self.ui.PlayerControl.StopSucceed(interaction)
        except Exception as e:
            await self.ui.PlayerControl.StopFailed(interaction, e)

    ##############################################

    @app_commands.command(name="seek", description="⏲️ | 跳轉你想要聽的地方")
    @app_commands.describe(timestamp="目標時間 (時間戳格式 0:20) 或 (秒數 20)")
    @app_commands.rename(timestamp="目標時間")
    async def seek(self, interaction, timestamp: str):
        try:
            # timestamp in seconds
            # playlist[].length in milliseconds
            if isinstance(timestamp, str):
                tmp = map(int, reversed(timestamp.split(":")))
                timestamp = 0
                for idx, val in enumerate(tmp):
                    timestamp += (60**idx) * val
            else:
                raise ValueError(f"Args validation failed, got: {timestamp}")
            await self._seek(interaction.guild, timestamp)
            await self.ui.PlayerControl.SeekSucceed(interaction, timestamp)
        except ValueError as e:  # For ignoring string with ":" like "o:ro"
            await self.ui.PlayerControl.SeekFailed(interaction, e)
            return

    ##############################################

    @app_commands.command(name="replay", description="🔁 | 重頭開始播放目前的歌曲")
    async def replay(self, interaction: discord.Interaction):
        try:
            await self._seek(interaction.guild, 0)
            await self.ui.PlayerControl.ReplaySucceed(interaction)
        except Exception as e:
            await self.ui.PlayerControl.ReplayFailed(interaction, e)

    ##############################################

    @app_commands.command(name="loop", description="🔂 | 循環播放目前的歌曲")
    @app_commands.describe(times="重複播放次數 (不填寫次數以啟動無限次數循環)")
    @app_commands.rename(times="重複播放次數")
    async def single_loop(self, interaction: discord.Interaction, times: int = INF):
        voice_client: wavelink.Player = interaction.guild.voice_client
        if (
            not isinstance(times, int)
            or voice_client is None
            or len(self._playlist[interaction.guild.id].order) == 0
        ):
            return await self.ui.PlayerControl.SingleLoopFailed(interaction)
        self._playlist.single_loop(interaction.guild.id, times)
        await self.ui.PlayerControl.LoopSucceed(interaction)

    ##############################################

    @app_commands.command(name="shuffle", description="🔀 | 隨機排序目前的待播清單")
    async def shuffle(self, interaction: discord.Interaction):
        if len(self._playlist[interaction.guild.id]) < 2:
            await self.ui.PlayerControl.ShuffleFailed(interaction)
        self._playlist[interaction.guild.id].shuffle()

    ##############################################

    @app_commands.command(name="queueloop", description="🔁 | 循環播放目前的待播清單")
    async def playlist_loop(self, interaction: discord.Interaction):
        voice_client: wavelink.Player = interaction.guild.voice_client
        if voice_client is None or len(self._playlist[interaction.guild.id].order) == 0:
            return await self.ui.PlayerControl.SingleLoopFailed(interaction)
        self._playlist.playlist_loop(interaction.guild.id)
        await self.ui.PlayerControl.LoopSucceed(interaction)

    ##############################################

    @app_commands.command(name="queue", description="ℹ️ | 列出目前的待播清單")
    async def show_queue(self, interaction: discord.Interaction):
        await self.ui.Queue.ShowQueue(interaction)

    ##############################################

    @app_commands.command(name="remove", description="🗑️ | 刪除待播清單中的一首歌")
    @app_commands.describe(idx="欲刪除歌曲之位置 (可用 %queue 或 /queue 得知位置代號)")
    @app_commands.rename(idx="刪除歌曲位置")
    async def remove(self, interaction: discord.Interaction, idx: int):
        try:
            if self._playlist[interaction.guild.id].order[idx].extras.suggested:
                await self.ui.QueueControl.RemoveFailed(interaction, "不能移除建議歌曲")
                return
            removed = self._playlist[interaction.guild.id].order[idx]
            self._playlist.pop(interaction.guild.id, idx)
            await self.ui.QueueControl.RemoveSucceed(interaction, removed, idx)
        except (IndexError, TypeError) as e:
            await self.ui.QueueControl.RemoveFailed(interaction, e)

    ##############################################

    @app_commands.command(name="swap", description="🔄 | 交換待播清單中兩首歌的位置")
    @app_commands.describe(
        idx1="歌曲1 位置 (可用 %queue 或 /queue 得知位置代號)",
        idx2="歌曲2 位置 (可用 %queue 或 /queue 得知位置代號)",
    )
    @app_commands.rename(idx1="歌曲1位置", idx2="歌曲2位置")
    async def swap(self, interaction: discord.Interaction, idx1: int, idx2: int):
        try:
            if (
                self._playlist[interaction.guild.id].order[idx1].extras.suggested
                or self._playlist[interaction.guild.id].order[idx2].extras.suggested
            ):
                await self.ui.QueueControl.SwapFailed(interaction, "不能移動建議歌曲")
                return
            self._playlist.swap(interaction.guild.id, idx1, idx2)
            await self.ui.QueueControl.Embed_SwapSucceed(interaction, idx1, idx2)
        except (IndexError, TypeError) as e:
            await self.ui.QueueControl.SwapFailed(interaction, e)

    ##############################################

    @app_commands.command(name="move", description="🔄 | 移動待播清單中一首歌的位置")
    @app_commands.describe(
        origin="原位置 (可用 %queue 或 /queue 得知位置代號)", new="目標位置 (可用 %queue 或 /queue 得知位置代號)"
    )
    @app_commands.rename(origin="原位置", new="目標位置")
    async def move_to(self, interaction: discord.Interaction, origin: int, new: int):
        try:
            if (
                self._playlist[interaction.guild.id].order[origin].extras.suggested
                or self._playlist[interaction.guild.id].order[new].extras.suggested
            ):
                await self.ui.QueueControl.MoveToFailed(interaction, "不能移動建議歌曲")
                return
            self._playlist.move_to(interaction.guild.id, origin, new)
            await self.ui.QueueControl.MoveToSucceed(interaction, origin, new)
        except (IndexError, TypeError) as e:
            await self.ui.QueueControl.MoveToFailed(interaction, e)

    ##############################################

    async def process(
        self,
        interaction: discord.Interaction,
        trackinfo: list[Union[wavelink.Playable, wavelink.Playlist, None]],
    ):
        # Call search function
        try:
            is_search = isinstance(trackinfo, list) and (
                not isinstance(trackinfo[0], wavelink.Playlist) and (
                len(trackinfo) > 1)
            )
            await self._search(interaction.guild, trackinfo, requester=interaction.user)
        except Exception as e:
            # If search failed, sent to handler
            await self.ui.Search.SearchFailed(interaction, e)
            return
        # If queue has more than 1 songs, then show the UI
        await self.ui.Queue.Embed_AddedToQueue(
            interaction, trackinfo, requester=interaction.user, is_search=is_search
        )

    async def play(
        self,
        interaction: discord.Interaction,
        trackinfo: list[Union[wavelink.Playable, wavelink.Playlist, None]],
    ):
        # Try to make bot join author's channel
        voice_client: wavelink.Player = interaction.guild.voice_client
        if isinstance(voice_client, wavelink.Player) and interaction.user.voice is None:
            pass
        elif (
            not isinstance(voice_client, wavelink.Player)
            or voice_client.channel != interaction.user.voice.channel
        ):
            await self.join(interaction)
            voice_client = interaction.guild.voice_client
            if not isinstance(voice_client, wavelink.Player):
                return

        # Start search process
        await self.process(interaction, trackinfo)

        await self._play(interaction.guild, interaction.channel)
        if not interaction.response.is_done():
            await interaction.response.send_message("⠀")
            tmpmsg = await interaction.original_response()
            await tmpmsg.delete()

    async def get_search_suggest(self, interaction: discord.Interaction, current: str):
        return await self.track_helper.get_search_suggest(interaction, current, self[interaction.guild_id])

    @app_commands.command(name="play", description="🎶 | 想聽音樂？來這邊點歌吧~")
    @app_commands.describe(
        search="欲播放之影片網址或關鍵字 (支援 SoundCloud / Spotify / BiliBili(單曲))"
    )
    @app_commands.rename(search="影片網址或關鍵字")
    @discord.app_commands.autocomplete(search=get_search_suggest)
    async def _i_play(self, interaction: discord.Interaction, search: str):
        await self.ui.Changelogs.SendChangelogs(interaction)
        if "sid=>" in search:
            tracks = await self.track_helper.get_track(interaction, search)
            await self.play(interaction, tracks)
        elif validators.url(search):
            if (
                "list" in search
                and "watch" in search
                and ("youtube" in search or "youtu.be" in search)
            ):
                if self[interaction.guild.id].multitype_remembered:
                    tracks = await self.track_helper.get_track(
                        interaction, search, self[interaction.guild.id].multitype_choice
                    )
                else:
                    await self.ui.PlayerControl.MultiTypeNotify(interaction, search)
                    return
            else:
                tracks = await self.track_helper.get_track(interaction, search)
                if isinstance(tracks, Exception) or tracks is [None] or tracks is None:
                    await self.ui.Search.SearchFailed(interaction, search)
            await self.play(interaction, tracks)
        else:
            tracks = await self.track_helper.get_track(interaction, search)
            await self.ui.PlayerControl.SearchResultSelection(interaction, tracks)

    ##############################

    @commands.Cog.listener(name="on_voice_state_update")
    async def end_session(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.id != self.bot.user.id or not (
            before.channel is not None and after.channel is None
        ):
            return
        guild = member.guild
        if after.channel is None:
            await self._leave(member.guild)
        self._cleanup(guild)

    async def _get_current_stats(self):
        active_player = len(self.bot.voice_clients)

        logging.info(f"[Stats] Currently playing in {active_player}/{len(self.bot.guilds)} guilds ({round(active_player/len(self.bot.guilds), 3) * 100}% Usage)")
        dotenv.set_key("../.env", "GUILD_COUNT", str(len(self.bot.guilds)))

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        channel = self[player.guild.id].text_channel
        await self._leave(player.guild)
        await self.ui.Leave.LeaveOnTimeout(channel)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        await self._get_current_stats()
        try:
            guild = discord.Object(payload.track.extras.requested_guild)
            if self.ui_guild_info(guild.id).playinfo is None:
                await self.ui.PlayerControl.PlayingMsg(self[guild.id].text_channel)
            else:
                await self.ui._InfoGenerator._UpdateSongInfo(guild.id)
            await self[guild.id].song_played(payload.track)
            
            if self.guild_info(guild.id).lastskip:
                self.guild_info(guild.id).lastskip = False
        except Exception as e:
            logging.error(f"Error on_wavelink_track_start: {e}")
            capture_exception(e)

    async def _refresh_after_suggested(self, guild: discord.Guild):
        if self.ui_guild_info(guild.id).music_suggestion:
            while self.ui_guild_info(guild.id).suggestion_processing:
                await asyncio.sleep(0.01)
            
            try:
                await self.ui._InfoGenerator._UpdateSongInfo(guild.id)
            except:
                self._refresh_after_suggested(guild)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        await self._get_current_stats()
        guild: discord.Guild = self.bot.get_guild(payload.track.extras.requested_guild)
        self._playlist.rule(guild.id, self.ui_guild_info(guild.id).skip)
        await asyncio.sleep(0.5)

        if len(self._playlist[guild.id].order) == 0:
            if not (
                (self.ui_guild_info(guild.id).leaveoperation)
            ):
                self.ui_guild_info(guild.id).leaveoperation = False
                await self.ui.PlayerControl.DonePlaying(self[guild.id].text_channel)
            return
        else:
            player: wavelink.Player = guild.voice_client

            self.bot.loop.create_task(self.track_helper.process_suggestion(guild, self.ui_guild_info(guild.id)))

            song = self._playlist[guild.id].current()
            try:
                await player.play(song)
                self.ui_guild_info(guild.id).previous_title = song.title
            except Exception as e:
                await self.ui.PlayerControl.PlayingError(self[guild.id].text_channel, e)
                pass

            self.bot.loop.create_task(self._refresh_after_suggested(guild))

    # @commands.Cog.listener()
    # async def on_wavelink_node_disconnected(self, payload: wavelink.NodeDisconnectedEventPayload) -> None:
    #     node: wavelink.Node = payload.node
    #     new_node: wavelink.Node = wavelink.Pool.get_node()  # You can get a specific node if you want...
    #     if not new_node:
    #         return
        
    #     players: dict[int, wavelink.Player] = node.players
    #     for guild_id, player in players.items():
    #         try:
    #             await player.switch_node(new_node)
    #         except RuntimeError:
    #             await player.disconnect()

    # Error handler
    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            return
        logging.error(error)
        await ctx.send(
            f"""
            **:no_entry: | 失敗 | UNKNOWNERROR**
            執行指令時發生了一點未知問題，請稍候再嘗試一次
            --------
            技術資訊:
            {error}
            --------
            *若您覺得有Bug或錯誤，請參照上方資訊及代碼，並到我們的群組回報*
        """,
            view=self.groupbutton,
        )

    @commands.Cog.listener()
    async def on_wavelink_player_update(
        self,
        payload: wavelink.PlayerUpdateEventPayload
    ):
        try:
            if len(self._playlist[payload.player.guild.id].order) == 0:
                if not (
                    (self.ui_guild_info(payload.player.guild.id).leaveoperation)
                ):
                    self.ui_guild_info(payload.player.guild.id).leaveoperation = False
                await self.ui.PlayerControl.DonePlaying(self[payload.player.guild.id].text_channel)
            return
        except Exception as e:
            logging.error(f"Error on_wavelink_player_update: {e}")
            capture_exception(e)
            

    async def _alone_timer(self, time: int, voice_client: wavelink.Player):
        await asyncio.sleep(time)
        await self.on_wavelink_inactive_player(voice_client)

    @commands.Cog.listener("on_voice_state_update")
    async def _pause_on_being_alone(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        try:
            voice_client: wavelink.Player = member.guild.voice_client
            if len(voice_client.channel.members) == 1 and member != self.bot.user \
                and len(self._playlist[member.guild.id].order) > 0:
                
                if not self.ui_guild_info(member.guild.id).playinfo is None:
                    await self.ui._InfoGenerator._UpdateSongInfo(member.guild.id)
                else:
                    await self.ui.PlayerControl.PlayingMsg(self[member.guild.id].text_channel)

                self.ui_guild_info(member.guild.id).playinfo_view.playorpause.emoji = Emoji.play_emoji
                self.ui_guild_info(member.guild.id).playinfo_view.playorpause.disabled = True
                self.ui_guild_info(member.guild.id).playinfo_view.playorpause.style = discord.ButtonStyle.gray
                
                self.ui_guild_info(member.guild.id).playinfo_view.skip.disabled = True
                self.ui_guild_info(member.guild.id).playinfo_view.skip.style = discord.ButtonStyle.gray
                
                self.ui_guild_info(member.guild.id).playinfo_view.suggest.disabled = True
                self.ui_guild_info(member.guild.id).playinfo_view.suggest.style = discord.ButtonStyle.gray
                
                await self.ui_guild_info(member.guild.id).playinfo.edit(view=self.ui_guild_info(member.guild.id).playinfo_view)
                
                if not voice_client.paused:
                    await self._pause(member.guild)

                if not self.ui_guild_info(member.guild.id).timer_task is None:
                    self.ui_guild_info(member.guild.id).timer_task.cancel()
                    self.ui_guild_info(member.guild.id).timer_task = None
                self.ui_guild_info(member.guild.id).timer_task = self.bot.loop.create_task(self._alone_timer(voice_client.inactive_timeout, voice_client))
            elif (
                len(voice_client.channel.members) > 1
                and voice_client.paused
                and member != self.bot.user
                and self.ui_guild_info(member.guild.id).playinfo_view.playorpause.disabled
            ):
                if not self.ui_guild_info(member.guild.id).playinfo is None:
                    await self.ui._InfoGenerator._UpdateSongInfo(member.guild.id)
                else:
                    await self.ui.PlayerControl.PlayingMsg(self[member.guild.id].text_channel)
                
                self.ui_guild_info(member.guild.id).playinfo_view.playorpause.disabled = False
                self.ui_guild_info(member.guild.id).playinfo_view.playorpause.style = discord.ButtonStyle.blurple
                
                if not len(self._playlist[member.guild.id].order) == 1:
                    self.ui_guild_info(member.guild.id).playinfo_view.skip.disabled = False
                    self.ui_guild_info(member.guild.id).playinfo_view.skip.style = discord.ButtonStyle.blurple
                
                self.ui_guild_info(member.guild.id).playinfo_view.suggest.disabled = False
                
                if self.ui_guild_info(member.guild.id).music_suggestion:
                    self.ui_guild_info(member.guild.id).playinfo_view.suggest.style = discord.ButtonStyle.green
                else:
                    self.ui_guild_info(member.guild.id).playinfo_view.suggest.style = discord.ButtonStyle.danger

                await self.ui_guild_info(member.guild.id).playinfo.edit(view=self.ui_guild_info(member.guild.id).playinfo_view)

                if not self.ui_guild_info(member.guild.id).timer_task is None:
                    self.ui_guild_info(member.guild.id).timer_task.cancel()
                    self.ui_guild_info(member.guild.id).timer_task = None
        except Exception as e:
            logging.debug(f"Error on_voice_state_update: {e}")

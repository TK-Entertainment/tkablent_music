from typing import *
import asyncio

import discord
from discord.ext import commands
from discord import app_commands

import wavelink
from wavelink.ext import spotify
from .playlist import SpotifyAlbum, SpotifyPlaylist
from .command import Command

from .player import GuildInfo, Player
from .command import Command

INF = int(1e18)

class MusicCog(Player, commands.Cog):
    def __init__(self, bot: commands.Bot, bot_version):
        Player.__init__(self, bot)
        commands.Cog.__init__(self)
        self.bot: commands.Bot = bot
        self.bot_version = bot_version

    async def resolve_ui(self):   
        from .ui import UI
        self.ui = UI(self, self.bot_version)
        
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
        auto_stage_vaildation = self.ui[command.guild.id].auto_stage_available
        
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

    async def nowplaying(self, command):
        if not isinstance(command, Command):
            command: Command = Command(command)
        await self.ui.NowPlaying(command)

    @commands.command(name='np')
    async def _c_nowplaying(self, ctx: commands.Context):
        await self.nowplaying(ctx)

    @app_commands.command(name='np', description='▶️ | 查看現在在播放什麼!')
    async def _i_nowplaying(self, interaction: discord.Interaction):
        await self.nowplaying(interaction)

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
            if self._playlist[command.guild.id].order[idx].suggested:
                await self.ui.RemoveFailed(command, '不能移除建議歌曲')
                return
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

    async def swap(self, command: Union[Command, Any], idx1: Union[int, str], idx2: Union[int, str]):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            if self._playlist[command.guild.id].order[idx1].suggested or self._playlist[command.guild.id].order[idx2].suggested:
                await self.ui.SwapFailed(command, '不能移動建議歌曲')
                return
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

    async def move_to(self, command: Union[Command, Any], origin: Union[int, str], new: Union[int, str]):
        if not isinstance(command, Command):
            command: Command = Command(command)
        try:
            if self._playlist[command.guild.id].order[origin].suggested or self._playlist[command.guild.id].order[new].suggested:
                await self.ui.MoveToFailed(command, '不能移動建議歌曲')
                return
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
    
    async def play(self, command: Command, trackinfo: Union[
                                wavelink.YouTubeTrack,
                                wavelink.YouTubeMusicTrack,
                                wavelink.SoundCloudTrack,
                                wavelink.YouTubePlaylist,
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
    @app_commands.describe(search='欲播放之影片網址或關鍵字 (支援 Youtube / SoundCloud / Spotify)')
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

    async def spotify_info_process(self, search, trackinfo, type: spotify.SpotifySearchType):
        if type == spotify.SpotifySearchType.track:
            #backup
            trackinfo.yt_title = trackinfo.title
            trackinfo.yt_url = trackinfo.uri
            # replace with spotify data
            spotify_data = self.spotify.track(search)
            trackinfo.title = spotify_data['name']
            trackinfo.uri = search
            trackinfo.author = spotify_data['artists'][0]['name']
            trackinfo.cover = spotify_data['album']['images'][0]['url']
            return trackinfo
        else:
            if type == spotify.SpotifySearchType.album:
                spotify_data = self.spotify.album(search)
                tracks = SpotifyAlbum()
            elif type == spotify.SpotifySearchType.playlist:
                spotify_data = self.spotify.playlist(search)
                tracks = SpotifyPlaylist()

            count = 0

            for track in trackinfo:
                track.yt_title = track.title
                track.yt_url = track.uri

                if type == spotify.SpotifySearchType.album:
                    track.title = spotify_data['tracks']['items'][count]['name']
                    track.uri = spotify_data['tracks']['items'][count]['external_urls']['spotify']
                    track.author = spotify_data['tracks']['items'][count]['artists'][0]['name']
                    track.cover = spotify_data['images'][0]['url']
                else:
                    track.title = spotify_data['tracks']['items'][count]['track']['name']
                    track.uri = spotify_data['tracks']['items'][count]['track']['external_urls']['spotify']
                    track.author = spotify_data['tracks']['items'][count]['track']['artists'][0]['name']
                    track.cover = spotify_data['tracks']['items'][count]['track']['album']['images'][0]['url']
                count += 1

            tracks.name = spotify_data['name']
            tracks.uri = search
            tracks.thumbnail = spotify_data['images'][0]['url']
            tracks.tracks.extend(trackinfo)
            return tracks

    async def _get_track(self, command: Command, search: str, choice: str):
        if 'spotify' in search:
            if 'track' in search:
                searchtype = spotify.SpotifySearchType.track
            elif 'album' in search:
                searchtype = spotify.SpotifySearchType.album
            else:
                searchtype = spotify.SpotifySearchType.playlist
            
            if ('album' in search or 'artist' in search or 'playlist' in search):
                self.ui[command.guild.id].processing_msg = await self.ui.SearchInProgress(command)

            tracks = await spotify.SpotifyTrack.search(search, node=self.searchnode, type=searchtype, return_first=True)
            
            if tracks is None:
                trackinfo = None
            else:
                trackinfo = await self.spotify_info_process(search, tracks, searchtype)
        else:
            extract = search.split('&')
            if choice == 'videoonly':
                url = extract[0]
            elif choice == 'playlist':
                url = f'https://www.youtube.com/playlist?{extract[1]}'
            else:
                url = search
            if choice == 'playlist' or 'list' in search:
                # SearchableTrack.convert(ctx, query)
                # command here actually useless 
                trackinfo = await wavelink.YouTubePlaylist.convert(command, url)
            else:
                for trackmethod in [
                                        wavelink.YouTubeMusicTrack,
                                        wavelink.LocalTrack,
                                        wavelink.YouTubeTrack,
                                        wavelink.SoundCloudTrack,
                                    ]: 
                    try:
                        # SearchableTrack.search(query, node, return_first)
                        trackinfo = await trackmethod.search(url, node=self.searchnode, return_first=True)
                    except Exception:
                        # When there is no result for provided method
                        # Then change to next method to search
                        trackinfo = None
                        pass
                    if trackinfo is not None:
                        break
        
        if trackinfo is None:
            await self.ui.SearchFailed(command, search)
            return

        if isinstance(trackinfo, wavelink.YouTubePlaylist):
            trackinfo.uri = url

        if 'youtube' in trackinfo.uri or 'spotify' in trackinfo.uri:
            trackinfo.audio_source = 'youtube'
        elif 'soundcloud' in trackinfo.uri:
            trackinfo.audio_source = 'soundcloud'

        trackinfo.suggested = False

        await self.play(command, trackinfo)

    ##############################

    async def _process_resuggestion(self, guild: discord.Guild, suggestion):
        if len(self.ui[guild.id].suggestions) != 0:
            # check first one first
            if self.ui[guild.id].suggestions[0].title in self.ui[guild.id].previous_titles:
                print(f'[Suggestion] {self.ui[guild.id].suggestions[0].title} has played before in {guild.id}, resuggested')
                self.ui[guild.id].suggestions.pop(0)
                for trackmethod in [wavelink.YouTubeMusicTrack, wavelink.YouTubeTrack]:
                    try:
                        suggested_track = await trackmethod.search(suggestion['tracks']['index']['videoId'], node=self.searchnode, return_first=True)
                    except:
                        suggested_track = None
                        pass
                    if suggested_track is not None:
                        suggested_track.suggested = True
                        suggested_track.audio_source = 'youtube'
                        self.ui[guild.id].suggestions.append(suggested_track)
                        suggestion['index'] += 1
                        break

        # wait for rest of suggestions to be processed, and check them
        await asyncio.sleep(7)
        for i, track in enumerate(self.ui[guild.id].suggestions):
            if track.title in self.ui[guild.id].previous_titles:
                print(f'[Suggestion] {track.title} has played before in {guild.id}, resuggested')
                self.ui[guild.id].suggestions.pop(i)
                for trackmethod in [wavelink.YouTubeMusicTrack, wavelink.YouTubeTrack]:
                    try:
                        suggested_track = await trackmethod.search(suggestion['tracks']['index']['videoId'], node=self.searchnode, return_first=True)
                    except:
                        suggested_track = None
                        
                    if suggested_track is not None:
                        suggested_track.suggested = True
                        suggested_track.audio_source = 'youtube'
                        self.ui[guild.id].suggestions.append(suggested_track)
                        suggestion['index'] += 1
                        break
                

    async def _search_for_suggestion(self, guild, suggestion):
        indexlist = [2, 3, 4, 5, 6]
        for index in indexlist:
            for trackmethod in [wavelink.YouTubeMusicTrack, wavelink.YouTubeTrack]:
                try:
                    suggested_track = await trackmethod.search(suggestion['tracks'][index]['videoId'], node=self.searchnode, return_first=True)
                except:
                    suggested_track = None
                    pass
                if suggested_track is not None:
                    break
            suggested_track.suggested = True
            suggested_track.audio_source = 'youtube'
            self.ui[guild.id].suggestions.append(suggested_track)

    async def process_suggestion(self, guild: discord.Guild):
        if self.ui[guild.id].music_suggestion \
                and len(self._playlist[guild.id].order) == 1 \
                and self._playlist[guild.id].current().audio_source == 'youtube':
            if self._playlist[guild.id].current().title not in self.ui[guild.id].previous_titles:
                self.ui[guild.id].previous_titles.append(self._playlist[guild.id].current().title)
            if len(self.ui[guild.id].suggestions) == 0:
                suggestion = self.ui[guild.id].suggestions_source = self.ytapi.get_watch_playlist(videoId=self._playlist[guild.id].current().identifier, limit=1)
                self.ui[guild.id].suggestions_source['index'] = 7
                for trackmethod in [wavelink.YouTubeMusicTrack, wavelink.YouTubeTrack]:
                    try:
                        suggested_track = await trackmethod.search(suggestion['tracks'][1]['videoId'], node=self.searchnode, return_first=True)
                    except:
                        suggested_track = None
                        pass
                    if suggested_track is not None:
                        break
                suggested_track.suggested = True
                suggested_track.audio_source = 'youtube'
                self.ui[guild.id].suggestions.append(suggested_track)
                self.bot.loop.create_task(self._search_for_suggestion(guild, suggestion))
                print(f'[Suggestion] Started to fetch 6 suggestions for {guild.id}')
            
            self.bot.loop.create_task(self._process_resuggestion(guild, self.ui[guild.id].suggestions_source))

            if len(self.ui[guild.id].previous_titles) > 64:
                self.ui[guild.id].previous_titles.pop(0)
                print(f'[Suggestion] The history storage of {guild.id} was full, removed the first item')
            
            await asyncio.sleep(0.7)

            self.ui[guild.id].previous_titles.append(self.ui[guild.id].suggestions[0].title)
            print(f'[Suggestion] Suggested {self.ui[guild.id].suggestions[0].title} for {guild.id} in next song, added to history storage')
            await self._playlist.add_songs(guild.id, self.ui[guild.id].suggestions.pop(0), '自動推薦歌曲')
            
    async def _refresh_msg(self, guild):
        await asyncio.sleep(3)
        await self.ui._UpdateSongInfo(guild.id)

    async def _mainloop(self, guild: discord.Guild):
        task = None
        while len(self._playlist[guild.id].order):
            voice_client: wavelink.Player = guild.voice_client
            await asyncio.sleep(1.2)
            song = self._playlist[guild.id].current()
            try:
                try:
                    await voice_client.play(song)
                    self.ui[guild.id].previous_title = song.title
                    await self.ui.PlayingMsg(self[guild.id].text_channel)
                    task = self.bot.loop.create_task(self._refresh_msg(guild))
                except Exception as e:
                    await self.ui.PlayingError(self[guild.id].text_channel, e)

                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(0.01)
            finally:
                self._playlist.rule(guild.id)
                self.bot.loop.create_task(self.process_suggestion(guild))
                task.cancel()
                task = None
        await self.ui.DonePlaying(self[guild.id].text_channel)
        
    @commands.Cog.listener(name='on_voice_state_update')
    async def end_session(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.id != self.bot.user.id or not (before.channel is not None and after.channel is None):
            return 
        guild = member.guild
        channel = self[guild.id].text_channel
        if self[guild.id]._timer is not None and self[guild.id]._timer.done():
            await self.ui.LeaveOnTimeout(channel)
        elif after.channel is None:
            await self._leave(member.guild)
        self._cleanup(guild)
    

    # Error handler
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            return
        print(error)
        await ctx.send(f'''
            **:no_entry: | 失敗 | UNKNOWNERROR**
            執行指令時發生了一點未知問題，請稍候再嘗試一次
            --------
            技術資訊:
            {error}
            --------
            *若您覺得有Bug或錯誤，請參照上方資訊及代碼，並使用 /reportbug 回報*
        ''') 

    @commands.Cog.listener('on_voice_state_update')
    async def _pause_on_being_alone(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        try:
            voice_client: wavelink.Player = member.guild.voice_client
            if len(voice_client.channel.members) == 1 and member != self.bot.user:
                if not voice_client.is_paused():
                    await self.ui.PauseOnAllMemberLeave(self[member.guild.id].text_channel, member.guild.id)
                    await self._pause(member.guild)
                else:
                    self.ui[member.guild.id].playinfo_view.playorpause.disabled = True
                    self.ui[member.guild.id].playinfo_view.playorpause.style = discord.ButtonStyle.gray
                    await self.ui[member.guild.id].playinfo.edit(view=self.ui[member.guild.id].playinfo_view)
            elif len(voice_client.channel.members) > 1 and voice_client.is_paused() and member != self.bot.user and self.ui[member.guild.id].playinfo_view.playorpause.disabled:
                self.ui[member.guild.id].playinfo_view.playorpause.disabled = False
                self.ui[member.guild.id].playinfo_view.playorpause.style = discord.ButtonStyle.blurple
                await self.ui[member.guild.id].playinfo.edit(view=self.ui[member.guild.id].playinfo_view)
        except: 
            pass
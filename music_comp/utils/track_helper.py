from typing import TYPE_CHECKING, Optional, Union, Dict, List, Literal
if TYPE_CHECKING:
    from typing import *

import bilibili_api as bilibili
from ytmusicapi import YTMusic
import wavelink
import discord
from discord import app_commands
import validators
import asyncio
import time
import os
from enum import Enum, auto

from music_comp.ui import UI, _sec_to_hms
from music_comp.playlist import LoopState, Playlist, PlaylistBase
from .storage import GuildUIInfo
from .cache import CacheWorker

class SpotifySearchType(Enum):
    TRACK = auto()
    ALBUM = auto()
    PLAYLIST = auto()

class SearchType(Enum):
    SPOTIFY = "spsearch"

    @classmethod
    def Spotify(cls) -> str:
        return cls.SPOTIFY.value

class TrackHelper():
    def __init__(self, ui_comp: UI, playlist: Playlist):
        # bilibili needed value
        SESSDATA = os.getenv("SESSDATA")
        BILI_JCT = os.getenv("BILI_JCT")
        BUVID3 = os.getenv("BUVID3")
        DEDEUSERID = os.getenv("DEDEUSERID")
        AC_TIME_VALUE = os.getenv("AC_TIME_VALUE")

        self.ui = ui_comp
        self._cacheworker: CacheWorker = CacheWorker()
        self._cache: dict = self._cacheworker._cache
        self._playlist = playlist
        self.ytapi: YTMusic = YTMusic(requests_session=False)

        # Bilibili API init
        self._bilibilic = bilibili.Credential(
            sessdata=SESSDATA,
            bili_jct=BILI_JCT,
            buvid3=BUVID3,
            dedeuserid=DEDEUSERID,
            ac_time_value=AC_TIME_VALUE,
        )

    def __getitem__(self, guild_id: int) -> PlaylistBase:
        return self._playlist[guild_id]

    def check_current_suggest_support(self, guild_id) -> bool:
        current = self[guild_id].current()

        return (
            current.source == "youtube"
        )
# ================================================================================================= #
#   Search Suggestion Process (Quick Search)
        
    # Processing track information for search suggestion
    async def _search_suggest_processing(self, result: list, track, data: dict):
        try:
            if self._cache.get(track.identifier) is not None:
                expired = (
                    int(time.time())
                    - self._cache.get(track.identifier)["timestamp"]
                ) >= 2592000

                if not expired:
                    result.append(
                        app_commands.Choice(
                            name=f"{self._cache[track.identifier]['title']} | {self._cache[track.identifier]['length']}",
                            value=f"sid=>{track.identifier}",
                        )
                    )
                    return

            if isinstance(track, str):
                return

            length = _sec_to_hms(
                seconds=(track.length) / 1000, format="symbol"
            )

            left_name_length = 70 - len(f" | {length}")

            if len(track.title) >= left_name_length + len(" ..."):
                track.title = track.title[:left_name_length] + " ..."

            result.append(
                app_commands.Choice(
                    name=f"{track.title} | {length}",
                    value=f"sid=>{track.identifier}",
                )
            )

            timestamp = int(time.time())
            data[track.identifier] = dict(
                title=track.title, length=length, timestamp=timestamp
            )
        finally:
            return

    # Main part for search suggestion system
    async def get_search_suggest(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        if validators.url(current) or current == "":
            return []
        else:
            tracks = await self.get_track(interaction, current, quick_search=True)
            result = []
            data = {}

            async with asyncio.TaskGroup() as taskgroup:
                for i in range(len(tracks)):
                    if i == 16:
                        break
                    
                    # WTF IS THIS, THIS IS WAY FASTER?
                    # EDIT: This is faster than past versions
                    # EDIT: BUT it isn't because of the usage of asyncio
                    # EDIT: It's because the shit coding (put asyncio.sleep inside for loop)
                    taskgroup.create_task(self._search_suggest_processing(result, tracks[i], data))

            asyncio.create_task(self._cacheworker.update_cache(data))

            return result
            
# ================================================================================================= #
#   Track Fetching System        

    # Getting songs via bilibili api
    async def _get_bilibili_track(self, interaction: discord.Interaction, search: str) -> Union[wavelink.Playable, Exception]:
        if "BV" in search and "https://www.bilibili.com/" not in search:
            vid = search
        else:
            try:
                int(search)
                is_aid = True
            except:
                is_aid = False
            if is_aid:
                vid = bilibili.aid2bvid(search)
            else:
                if "b23.tv" in search:
                    search = bilibili.get_real_url(search, self._bilibilic)

                url_split = search.split("/")
                vid = url_split[4]

        v_data = bilibili.video.Video(bvid=vid, credential=self._bilibilic)
        download_url_data = await v_data.get_download_url(page_index=0)
        detector = bilibili.video.VideoDownloadURLDataDetecter(download_url_data)

        data = detector.detect_all()
        for t in data:
            if isinstance(t, bilibili.video.AudioStreamDownloadURL):
                raw_url = t.url.replace("&", "%26")
                try:
                    trackinfo = await wavelink.Pool.fetch_tracks(raw_url)
                except Exception as e:
                    raw_url = None
                    continue
                break
            else:
                raw_url = None

        if raw_url == None:
            return None

        try:
            trackinfo = await wavelink.Pool.fetch_tracks(raw_url)
        except Exception as e:
            return e

        track = trackinfo[0]
        vinfo = await v_data.get_info()
        track.author = vinfo["owner"]["name"]
        track.duration = vinfo["duration"] * 1000
        track.identifier = vinfo["bvid"]
        track.is_seekable = True
        track.title = vinfo["title"]

        return track

    # Parsing url for different cases
    def _parse_url(self, raw_url: str, choice: Literal["videoonly", "playlist"]) -> str:
        if "https://www.youtube.com/" in raw_url or "https://youtu.be/" in raw_url:
            if "list" in raw_url:
                extract = raw_url.split("&")
                if choice == "videoonly":
                    url = extract[0]
                elif choice == "playlist":
                    url = f"https://www.youtube.com/playlist?{extract[1]}"
                else:
                    url = raw_url
            else:
                url = raw_url
        elif "sid=>" in raw_url:
            vid = raw_url.split("=>")[1]
            url = f"https://www.youtube.com/watch?v={vid}"
        else:
            url = raw_url

        return url

    # Main part for track fetching system
    async def get_track(
        self,
        interaction: discord.Interaction,
        search: str,
        choice="videoonly",
        quick_search=False,
    ) -> list[Union[wavelink.Playable, wavelink.Playlist, None]]:
        if not quick_search:
            await interaction.response.defer(ephemeral=True, thinking=True)

        tracks = []

        if ("bilibili" in search or "b23.tv" in search) and validators.url(search):
            track = await self._get_bilibili_track(interaction, search)
            if isinstance(track, Exception):
                return track
            elif track is None:
                return [None]
            else:
                tracks.extend(track)

        elif (validators.url(search)) or ("sid=>" in search):
            url = self._parse_url(search, choice)
            callback = await wavelink.Playable.search(url)
            if isinstance(callback, list):
                tracks.extend(callback)
            elif isinstance(callback, wavelink.Playlist):
                tracks.append(callback)

        else:
            if quick_search:
                sources = [
                    wavelink.TrackSource.YouTube,
                ]
            else:
                sources = [
                    wavelink.TrackSource.YouTubeMusic, 
                    wavelink.TrackSource.YouTube,
                    SearchType.Spotify(),
                    wavelink.TrackSource.SoundCloud,
                ]

            for source in sources:
                try:
                    data = await wavelink.Playable.search(search, source=source)
                    if data is not None:
                        tracks.extend(data)
                except Exception:
                    # When there is no result for provided method
                    # Then change to next method to search
                    continue

        if len(tracks) == 0:
            if not quick_search:
                await self.ui.Search.SearchFailed(interaction, search)
            return [None]
        
        return tracks

# ================================================================================================= #
#   Auto Suggestion Processing System

    async def _get_suggest_track(
        self,
        suggestion: Dict[str, List[Dict]],
        index: int,
        ui_guild_info: GuildUIInfo,
        pre_process: bool,
    ) -> Optional[wavelink.Playable]:
        suggested_track = None

        try:
            suggested_track = await wavelink.Playable.search(
                "https://www.youtube.com/watch?v={}".format(suggestion["tracks"][index]["videoId"])
            )
            suggested_track = suggested_track[0]
        except:
            suggested_track = None
            pass

        if suggested_track is not None:
            suggested_track.suggested = True
            suggested_track.requested_guild = ui_guild_info.guild_id
            ui_guild_info.suggestions.append(suggested_track)

            if pre_process:
                suggestion["index"] += 1

        return suggested_track

    async def _get_suggest_list(
        self, guild: discord.Guild, playlist_index: int
    ) -> Dict[str, List[Dict]]:
        suggestion = self.ytapi.get_watch_playlist(
            videoId=self[guild.id].order[playlist_index].identifier, limit=5
        )

        suggestion["index"] = 13

        return suggestion

    # This part maintain if suggestion is not vaild(e.g: has already played before)
    async def _process_resuggestion(
        self, guild, suggestion, ui_guild_info: GuildUIInfo
    ) -> None:
        playlist_index = 1
        suggested_track = None

        if len(ui_guild_info.suggestions) != 0:
            # check first one first
            if ui_guild_info.suggestions[0].title in ui_guild_info.previous_titles:
                print(
                    f"[Suggestion] {ui_guild_info.suggestions[0].title} has played before in {guild.id}, resuggested"
                )
                ui_guild_info.suggestions.pop(0)

                while suggested_track is None:
                    suggested_track = await self._get_suggest_track(
                        suggestion, suggestion["index"], ui_guild_info, pre_process=True
                    )

                    if suggested_track is not None:
                        break
                    else:
                        suggestion = await self._get_suggest_list(guild, playlist_index)
                        playlist_index += 1

        self[guild.id]._suggest_search_task = await asyncio.wait_for(
            self._search_for_suggestion(guild, suggestion, ui_guild_info), None
        )
        suggested_track = None

        # wait for rest of suggestions to be processed, and check them
        for i, track in enumerate(ui_guild_info.suggestions):
            if track.title in ui_guild_info.previous_titles:
                print(
                    f"[Suggestion] {track.title} has played before in {guild.id}, resuggested"
                )
                ui_guild_info.suggestions.pop(i)
                while suggested_track is None:
                    suggested_track = await self._get_suggest_track(
                        suggestion, suggestion["index"], ui_guild_info, pre_process=True
                    )

                    if suggested_track is not None:
                        break
                    else:
                        suggestion = await self._get_suggest_list(guild, playlist_index)
                        playlist_index += 1

    # This part maintain suggestion fetching
    async def _search_for_suggestion(
        self, guild, suggestion, ui_guild_info: GuildUIInfo
    ):
        playlist_index = 1
        suggested_track = None

        if len(ui_guild_info.suggestions) == 0:
            print(f"[Suggestion] Started to fetch 12 suggestions for {guild.id}")

            while suggested_track is None:
                for index in range(2, 13, 1):
                    suggested_track = await self._get_suggest_track(
                        suggestion, index, ui_guild_info, pre_process=False
                    )

                    if suggested_track is not None:
                        break
                    else:
                        suggestion = await self._get_suggest_list(guild, playlist_index)
                        playlist_index += 1

    # Main core of suggestion processing system
    # Which decides whether enable suggestion or not in different cases
    async def process_suggestion(
        self, guild: discord.Guild, ui_guild_info: GuildUIInfo
    ):
        # Check whether current song is supported in suggestion system or not
        if (
            (ui_guild_info.music_suggestion)
            and self.check_current_suggest_support(guild.id)
            and len(self[guild.id].order) <= 2
        ):
            # If next song is user specific, then don't suggest anything
            if (
                len(self[guild.id].order) == 2
                and not self[guild.id].order[-1].suggested
            ):
                return

            if self[guild.id].loop_state != LoopState.NOTHING:
                # If loop state is singleloop, then don't add suggested song into cache
                # Since it even hasn't been played yet
                # Also won't return any suggestion
                if self[guild.id].loop_state != LoopState.PLAYLIST:
                    if len(self[guild.id].order) == 2 and (
                        self[guild.id].order[-1].suggested
                    ):
                        ui_guild_info.previous_titles.remove(
                            self[guild.id].order[-1].title
                        )
                        self.pop(guild.id, -1)
                    return
                # Case of playlist loop
                else:
                    if self[guild.id].current().suggested:
                        # Suggestion system here will ignore playlist loop
                        # Acting like loop not enabled 
                        # if current song is a song suggested
                        if len(self[guild.id].order) == 2 and (
                            self[guild.id].order[-1].suggested
                        ):
                            return
                    else:
                        # Same thing like single loop
                        if len(self[guild.id].order) == 2 and (
                            self[guild.id].order[-1].suggested
                        ):
                            ui_guild_info.previous_titles.remove(
                                self[guild.id].order[-1].title
                            )
                            self.pop(guild.id, -1)
                            return

            # Flag suggestion is in progress
            ui_guild_info.suggestion_processing = True

            suggested_track = None

            # Prevent resuggest same song
            if self[guild.id].current().title not in ui_guild_info.previous_titles:
                ui_guild_info.previous_titles.append(self[guild.id].current().title)

            if len(ui_guild_info.suggestions) == 0:
                index = 1
                suggestion = (
                    ui_guild_info.suggestions_source
                ) = self.ytapi.get_watch_playlist(
                    videoId=self[guild.id].current().identifier, limit=5
                )
                ui_guild_info.suggestions_source["index"] = 13

                while suggested_track is None:
                    suggested_track = await self._get_suggest_track(
                        suggestion, index, ui_guild_info, pre_process=False
                    )

                    if suggested_track is None:
                        index += 1

            if self[guild.id]._resuggest_task is not None:
                self[guild.id]._resuggest_task.cancel()
                self[guild.id]._resuggest_task = None

            if len(ui_guild_info.previous_titles) > 64:
                ui_guild_info.previous_titles.pop(0)
                print(
                    f"[Suggestion] The history storage of {guild.id} was full, removed the first item"
                )

            self[guild.id]._resuggest_task = await asyncio.wait_for(
                self._process_resuggestion(
                    guild, ui_guild_info.suggestions_source, ui_guild_info
                ),
                None,
            )

            ui_guild_info.previous_titles.append(ui_guild_info.suggestions[0].title)
            print(
                f"[Suggestion] Suggested {ui_guild_info.suggestions[0].title} for {guild.id} in next song, added to history storage"
            )
            await self._playlist.add_songs(guild.id, [ui_guild_info.suggestions.pop(0)], "自動推薦歌曲")
            ui_guild_info.suggestion_processing = False
            if ui_guild_info.skip:
                ui_guild_info.skip = False
            await self.ui._InfoGenerator._UpdateSongInfo(guild.id)
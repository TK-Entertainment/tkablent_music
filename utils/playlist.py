import random
from re import S
from typing import *
from enum import Enum, auto

import asyncio

import discord
import wavelink
import spotipy
from spotipy import SpotifyClientCredentials
from wavelink.ext import spotify
from ytmusicapi import YTMusic

INF = int(1e18)


class SeekError(Exception):
    ...


class OutOfBound(Exception):
    ...


class GuildUIInfo:
    def __init__(self):
        self.guild_id: int
        self.auto_stage_available: bool
        self.stage_topic_exist: bool
        self.stage_topic_checked: bool
        self.skip: bool
        self.lastskip: bool
        self.search: bool
        self.leaveoperation: bool
        self.music_suggestion: bool
        self.suggestion_processing: bool
        self.lasterrorinfo: dict
        self.playinfo: Coroutine[Any, Any, discord.Message]
        self.playinfo_view: discord.ui.View
        self.processing_msg: discord.Message
        self.searchmsg: Coroutine[Any, Any, discord.Message]
        self.suggestions_source 
        self.previous_titles: list[str]
        self.suggestions: list


class SpotifyAlbum:
    def __init__(self):
        self.name: str = ""
        self.uri: str = ""
        self.artists: str = ""
        self.requester: str = ""
        self.thumbnail: str = ""
        self.tracks: list = []


class SpotifyPlaylist:
    def __init__(self):
        self.name: str = ""
        self.uri: str = ""
        self.artists: str = ""
        self.requester: str = ""
        self.thumbnail: str = ""
        self.tracks: list = []

class SpotifySearchType(Enum):
    TRACK = auto()
    ALBUM = auto()
    PLAYLIST = auto()

class SearchType(Enum):
    SPOTIFY = "spsearch"

    @classmethod
    def Spotify(cls) -> str:
        return cls.SPOTIFY.value

class LoopState(Enum):
    NOTHING = auto()
    SINGLE = auto()
    PLAYLIST = auto()
    SINGLEINF = auto()


class PlaylistBase:
    """maintain some info in a playlist for single guild"""

    def __init__(self):
        self.order: list[wavelink.Playable] = []  # maintain the song order in a playlist
        self.loop_state: LoopState = LoopState.NOTHING
        self.times: int = 0  # use to indicate the times left to play current song
        self.text_channel: discord.TextChannel = (
            None  # where to show information to user
        )
        self._resuggest_task: asyncio.Task = None
        self._suggest_search_task: asyncio.Task = None
        self._refresh_msg_task: asyncio.Task = None
        # self._playlisttask: dict[str, asyncio.Task] = {}

    def __getitem__(self, idx) -> Optional[wavelink.Playable]:
        if len(self.order) == 0:
            return None
        return self.order[idx]

    def clear(self):
        self.order.clear()
        self.loop_state = LoopState.NOTHING
        self.times = 0

    def current(self) -> Optional[wavelink.Playable]:
        return self[0]

    def swap(self, idx1: int, idx2: int):
        self.order[idx1], self.order[idx2] = self.order[idx2], self.order[idx1]

    def move_to(self, origin: int, new: int):
        self.order.insert(new, self.order.pop(origin))

    def rule(self, is_skipped: bool):
        if len(self.order) == 0:
            return
        if self.loop_state == LoopState.SINGLEINF:
            return
        if self.loop_state == LoopState.SINGLE:
            self.times -= 1
        elif (
            self.loop_state == LoopState.PLAYLIST
            and (not self.order[0].suggested)
            and not is_skipped
        ):
            self.order.append(self.order.pop(0))
        else:
            self.order.pop(0)

        if self.loop_state == LoopState.SINGLE and self.times == 0:
            self.loop_state = LoopState.NOTHING

    def single_loop(self, times: int = INF):
        if (
            self.loop_state != LoopState.SINGLE
            and self.loop_state != LoopState.SINGLEINF
        ):
            self.loop_state = LoopState.SINGLE
            self.times = times  # "times" value only availible in Single Loop mode
            if self.times == INF:
                self.loop_state = LoopState.SINGLEINF
        else:
            self.loop_state = LoopState.NOTHING
            self.times = 0

    def playlist_loop(self):
        if self.loop_state == LoopState.PLAYLIST:
            self.loop_state = LoopState.NOTHING
        else:
            self.loop_state = LoopState.PLAYLIST

    def shuffle(self):
        for i in range(1, len(self.order) - 1):
            idx = random.randrange(i + 1, len(self.order))
            self.swap(i, idx)


class Playlist:
    def __init__(self):
        self._guilds_info: Dict[int, PlaylistBase] = dict()
        self.spotify = None
        self.ytapi: YTMusic = YTMusic(requests_session=False)

    def __delitem__(self, guild_id: int):
        if self._guilds_info.get(guild_id) is None:
            return
        del self._guilds_info[guild_id]

    def __getitem__(self, guild_id) -> PlaylistBase:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = PlaylistBase()
        return self._guilds_info[guild_id]

    def init_spotify(self, spotify_id, spotify_secret):
        self.spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=spotify_id, client_secret=spotify_secret
            )
        )

    # async def get_best_searchnode(self) -> wavelink.Node:
    #     searchnode_1 = wavelink.NodePool.get_node(id="SearchNode_1")
    #     searchnode_2 = wavelink.NodePool.get_node(id="SearchNode_2")

    #     # decide from the cpu usage
    #     node_1_stats = await searchnode_1._send(method="GET", path="stats")
    #     node_2_stats = await searchnode_2._send(method="GET", path="stats")

    #     node_1_avgload = (
    #         node_1_stats["cpu"]["systemLoad"] + node_1_stats["cpu"]["lavalinkLoad"]
    #     ) / 2
    #     node_2_avgload = (
    #         node_2_stats["cpu"]["systemLoad"] + node_2_stats["cpu"]["lavalinkLoad"]
    #     ) / 2

    #     if node_1_avgload > node_2_avgload:
    #         return searchnode_2
    #     elif node_1_avgload < node_2_avgload:
    #         return searchnode_1
    #     else:
    #         return random.choice([searchnode_1, searchnode_2])

    def check_current_suggest_support(self, guild_id) -> bool:
        current = self[guild_id].current()

        return (
            current.source == "youtube" or current.source == "spotify"
        )

    async def add_songs(
        self,
        guild_id,
        trackinfo: list[Union[wavelink.Playable, wavelink.Playlist]],
        requester,
    ):
        if len(self[guild_id].order) == 2 and self[guild_id].order[1].suggested:
            if isinstance(trackinfo, list):
                self[guild_id].order.pop(1)
            elif not trackinfo.suggested:
                self[guild_id].order.pop(1)

        if isinstance(trackinfo[0], wavelink.Playlist):
            for track in trackinfo[0].tracks:
                track.requester = requester
                track.requested_guild = guild_id
                try:
                    if isinstance(track.suggested, None):
                        track.suggested = False
                except:
                    track.suggested = False
            self[guild_id].order.extend(trackinfo[0].tracks)
        else:
            for track in trackinfo:
                track.requester = requester
                track.requested_guild = guild_id
                try:
                    if track.suggested != True or track.suggested is None:
                        track.suggested = False
                except:
                    track.suggested = False
            self[guild_id].order.extend(trackinfo)

    # To be deprecated
    # def spotify_info_process(self, search, tracks: list[wavelink.Playable], type: SpotifySearchType):
    #     if type == SpotifySearchType.TRACK:
    #         track = tracks[0]
    #         # backup
    #         track.yt_title = track.title
    #         track.yt_url = track.uri
    #         # replace with spotify data
    #         spotify_data = self.spotify.track(search)
    #         track.title = spotify_data["name"]
    #         track.uri = search
    #         track.author = spotify_data["artists"][0]["name"]
    #         track.cover = spotify_data["album"]["images"][0]["url"]
    #         return tracks
    #     else:
    #         if type == SpotifySearchType.ALBUM:
    #             spotify_data = self.spotify.album(search)
    #             tracks = SpotifyAlbum()
    #         elif type == SpotifySearchType.PLAYLIST:
    #             spotify_data = self.spotify.playlist(search)
    #             tracks = SpotifyPlaylist()

    #         count = 0

    #         for track in tracks:
    #             track.yt_title = track.title
    #             track.yt_url = track.uri

    #             if type == SpotifySearchType.ALBUM:
    #                 track.title = spotify_data["tracks"]["items"][count]["name"]
    #                 track.uri = spotify_data["tracks"]["items"][count]["external_urls"][
    #                     "spotify"
    #                 ]
    #                 track.author = spotify_data["tracks"]["items"][count]["artists"][0][
    #                     "name"
    #                 ]
    #                 track.cover = spotify_data["images"][0]["url"]
    #             else:
    #                 track.title = spotify_data["tracks"]["items"][count]["track"][
    #                     "name"
    #                 ]
    #                 track.uri = spotify_data["tracks"]["items"][count]["track"][
    #                     "external_urls"
    #                 ]["spotify"]
    #                 track.author = spotify_data["tracks"]["items"][count]["track"][
    #                     "artists"
    #                 ][0]["name"]
    #                 track.cover = spotify_data["tracks"]["items"][count]["track"][
    #                     "album"
    #                 ]["images"][0]["url"]
    #             track.suggested = False
    #             count += 1

    #         tracks.name = spotify_data["name"]
    #         tracks.uri = search
    #         tracks.thumbnail = spotify_data["images"][0]["url"]
    #         tracks.tracks.extend(tracks)
    #         return tracks

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

                    if suggested_track is not None:
                        if self[guild.id]._refresh_msg_task is not None:
                            self[guild.id]._refresh_msg_task.cancel()
                            self[guild.id]._refresh_msg_task = None
                        break
                    else:
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
            await self.add_songs(guild.id, [ui_guild_info.suggestions.pop(0)], "自動推薦歌曲")
            ui_guild_info.suggestion_processing = False
        
    def get_music_info(self, guild_id, index):
        return self[guild_id].order[index]

    def nowplaying(self, guild_id: int) -> dict:
        return self[guild_id].current()

    def swap(self, guild_id: int, idx1: int, idx2: int):
        self[guild_id].swap(idx1, idx2)

    def move_to(self, guild_id: int, origin: int, new: int):
        self[guild_id].move_to(origin, new)

    def pop(self, guild_id: int, idx: int):
        self[guild_id].order.pop(idx)

    def rule(self, guild_id: int, is_skipped: bool):
        self[guild_id].rule(is_skipped)

    def single_loop(self, guild_id: int, times: int = INF):
        self[guild_id].single_loop(times)

    def playlist_loop(self, guild_id: int):
        self[guild_id].playlist_loop()

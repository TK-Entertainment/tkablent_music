import random
from re import S
from typing import *
from enum import Enum, auto

import asyncio

import discord
import wavelink

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

    def __delitem__(self, guild_id: int):
        if self._guilds_info.get(guild_id) is None:
            return
        del self._guilds_info[guild_id]

    def __getitem__(self, guild_id: int) -> PlaylistBase:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = PlaylistBase()
        return self._guilds_info[guild_id]

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
                track.extras = {"requested_guild": guild_id}
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
                track.extras = {"requested_guild": guild_id}
                try:
                    if track.suggested != True or track.suggested is None:
                        track.suggested = False
                except:
                    track.suggested = False
            self[guild_id].order.extend(trackinfo)
        
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

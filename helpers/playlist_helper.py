from utils.playlist import Playlist, LoopState, PlaylistBase
from typing import *
from wavelink import Track

_playlist: Playlist = Playlist()

def get_current_track(guild_id) -> Optional[Track]:
    return _playlist[guild_id].current()

def get_now_playing(guild_id):
    return _playlist

def get_loop_state(guild_id) -> LoopState:
    return _playlist[guild_id].loop_state

def get_playlist(guild_id) -> PlaylistBase:
    return _playlist[guild_id]

def process_suggestion(guild, ui_guild_info):
    return _playlist.process_suggestion(guild, ui_guild_info)
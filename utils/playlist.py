import random
from re import S
from typing import *
from enum import Enum, auto

import asyncio

import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer, TextChannel, VoiceClient
import wavelink
import spotipy
from spotipy import SpotifyClientCredentials
from wavelink.ext import spotify
from ytmusicapi import YTMusic

INF = int(1e18)

class SeekError(Exception): ...
class OutOfBound(Exception): ...

class GuildUIInfo():
    def __init__(self):
        self.processing_msg: discord.Message
        self.music_suggestion: bool
        self.suggestions_source: dict
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

class LoopState(Enum):
    NOTHING = auto()
    SINGLE = auto()
    PLAYLIST = auto()
    SINGLEINF = auto()

class PlaylistBase:
    '''maintain some info in a playlist for single guild'''
    def __init__(self):
        self.order: list[wavelink.Track] = [] # maintain the song order in a playlist
        self.loop_state: LoopState = LoopState.NOTHING
        self.times: int = 0 # use to indicate the times left to play current song
        self.text_channel: discord.TextChannel = None # where to show information to user
        self._resuggest_task: asyncio.Task = None
        self._suggest_search_task: asyncio.Task = None
        self._refresh_msg_task: asyncio.Task = None
        # self._playlisttask: dict[str, asyncio.Task] = {}

    def __getitem__(self, idx):
        if len(self.order) == 0:
            return None
        return self.order[idx]

    def clear(self):
        self.order.clear()
        self.loop_state = LoopState.NOTHING
        self.times = 0

    def current(self) -> Optional[wavelink.Track]:
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
        elif self.loop_state == LoopState.PLAYLIST and (not self.order[0].suggested) and not is_skipped:
            self.order.append(self.order.pop(0))
        else:
            self.order.pop(0)

        if self.loop_state == LoopState.SINGLE and self.times == 0:
            self.loop_state = LoopState.NOTHING
            
    def single_loop(self, times: int = INF):
        if self.loop_state != LoopState.SINGLE and self.loop_state != LoopState.SINGLEINF:
            self.loop_state = LoopState.SINGLE
            self.times = times # "times" value only availible in Single Loop mode
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
        self.searchnode = None

    def __delitem__(self, guild_id: int):
        if self._guilds_info.get(guild_id) is None:
            return
        del self._guilds_info[guild_id]
        
    def __getitem__(self, guild_id) -> PlaylistBase:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = PlaylistBase()
        return self._guilds_info[guild_id]

    def init_spotify(self, spotify_id, spotify_secret):
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=spotify_id, client_secret=spotify_secret))

    async def add_songs(self, guild_id, trackinfo: Union[wavelink.YouTubeTrack, wavelink.SoundCloudTrack, wavelink.YouTubePlaylist], requester):
        if (not trackinfo.suggested) and len(self[guild_id].order) == 2 and self[guild_id].order[1].suggested:
            self[guild_id].order.pop(1)

        if isinstance(trackinfo, Union[wavelink.YouTubePlaylist, SpotifyAlbum, SpotifyPlaylist]):
            for track in trackinfo.tracks:
                track.requester = requester
                track.audio_source = 'youtube'
                track.suggested = False
            self[guild_id].order.extend(trackinfo.tracks)
        else:
            trackinfo.requester = requester
            self[guild_id].order.append(trackinfo)

    def spotify_info_process(self, search, trackinfo, type: spotify.SpotifySearchType):
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
                track.suggested = False
                count += 1

            tracks.name = spotify_data['name']
            tracks.uri = search
            tracks.thumbnail = spotify_data['images'][0]['url']
            tracks.tracks.extend(trackinfo)
            return tracks

    async def _process_resuggestion(self, guild, suggestion, ui_guild_info: GuildUIInfo):
        playlist_index = 1
        suggested_track = None

        if len(ui_guild_info.suggestions) != 0:
            # check first one first
            if ui_guild_info.suggestions[0].title in ui_guild_info.previous_titles:
                print(f'[Suggestion] {ui_guild_info.suggestions[0].title} has played before in {guild.id}, resuggested')
                ui_guild_info.suggestions.pop(0)
                while suggested_track is None:
                    for trackmethod in [wavelink.YouTubeMusicTrack, wavelink.YouTubeTrack]:
                        try:
                            suggested_track = await trackmethod.search(suggestion['tracks'][suggestion['index']]['videoId'], node=self.searchnode, return_first=True)
                        except:
                            suggested_track = None
                            pass
                        if suggested_track is not None:
                            suggested_track.suggested = True
                            suggested_track.audio_source = 'youtube'
                            ui_guild_info.suggestions.append(suggested_track)
                            suggestion['index'] += 1
                            break
                    if suggested_track is None:
                        suggestion = self.ytapi.get_watch_playlist(videoId=self[guild.id].order[playlist_index].identifier, limit=5)
                        suggestion['index'] = 7
                        playlist_index += 1

        self[guild.id]._suggest_search_task = await asyncio.wait_for(self._search_for_suggestion(guild, suggestion, ui_guild_info), None)
        suggested_track = None

        # wait for rest of suggestions to be processed, and check them
        for i, track in enumerate(ui_guild_info.suggestions):
            if track.title in ui_guild_info.previous_titles:
                print(f'[Suggestion] {track.title} has played before in {guild.id}, resuggested')
                ui_guild_info.suggestions.pop(i)
                while suggested_track is None:
                    for trackmethod in [wavelink.YouTubeMusicTrack, wavelink.YouTubeTrack]:
                        try:
                            suggested_track = await trackmethod.search(suggestion['tracks'][suggestion['index']]['videoId'], node=self.searchnode, return_first=True)
                        except:
                            suggested_track = None
                            pass
                        if suggested_track is not None:
                            suggested_track.suggested = True
                            suggested_track.audio_source = 'youtube'
                            ui_guild_info.suggestions.append(suggested_track)
                            suggestion['index'] += 1
                            break
                    if suggested_track is None:
                        suggestion = self.ytapi.get_watch_playlist(videoId=self[guild.id].order[playlist_index].identifier, limit=5)
                        suggestion['index'] = 7
                        playlist_index += 1

    async def _search_for_suggestion(self, guild, suggestion, ui_guild_info: GuildUIInfo):
        indexlist = [2, 3, 4, 5, 6]
        playlist_index = 1
        suggested_track = None

        if len(ui_guild_info.suggestions) == 0:

            print(f'[Suggestion] Started to fetch 6 suggestions for {guild.id}')

            while suggested_track is None:
                for index in indexlist:
                    for trackmethod in [wavelink.YouTubeMusicTrack, wavelink.YouTubeTrack]:
                        try:
                            suggested_track = await trackmethod.search(suggestion['tracks'][index]['videoId'], node=self.searchnode, return_first=True)
                        except:
                            suggested_track = None
                            pass
                        if suggested_track is not None:
                            suggested_track.suggested = True
                            suggested_track.audio_source = 'youtube'
                            ui_guild_info.suggestions.append(suggested_track)
                    if suggested_track is None:
                        suggestion = self.ytapi.get_watch_playlist(videoId=self[guild.id].order[playlist_index].identifier, limit=5)
                        suggestion['index'] = 7
                        playlist_index += 1
        
    async def process_suggestion(self, guild: discord.Guild, ui_guild_info: GuildUIInfo):
        if (ui_guild_info.music_suggestion) and self[guild.id].current().audio_source == 'youtube' and len(self[guild.id].order) <= 2:
            if (self[guild.id].loop_state == LoopState.SINGLE or self[guild.id].loop_state == LoopState.SINGLEINF) \
                    or (self[guild.id].loop_state == LoopState.PLAYLIST and not self[guild.id].current().suggested):
                if len(self[guild.id].order) == 2 and self[guild.id].order[-1].suggested:
                    ui_guild_info.previous_titles.remove(self[guild.id].order[-1].title)
                    self.pop(guild.id, -1)
                return
            suggested_track = None

            if self[guild.id].current().title not in ui_guild_info.previous_titles:
                ui_guild_info.previous_titles.append(self[guild.id].current().title)
            
            if len(ui_guild_info.suggestions) == 0:
                index = 1
                while suggested_track is None:
                    suggestion = ui_guild_info.suggestions_source = self.ytapi.get_watch_playlist(videoId=self[guild.id].current().identifier, limit=5)
                    ui_guild_info.suggestions_source['index'] = 7
                    for trackmethod in [wavelink.YouTubeMusicTrack, wavelink.YouTubeTrack]:
                        try:
                            suggested_track = await trackmethod.search(suggestion['tracks'][1]['videoId'], node=self.searchnode, return_first=True)
                        except:
                            suggested_track = None
                            pass
                        if suggested_track is not None:
                            suggested_track.suggested = True
                            suggested_track.audio_source = 'youtube'
                            ui_guild_info.suggestions.append(suggested_track)
                            if self[guild.id]._refresh_msg_task is not None:
                                self[guild.id]._refresh_msg_task.cancel()
                                self[guild.id]._refresh_msg_task = None
                            break
                    if suggested_track is None:
                        index += 1

            if self[guild.id]._resuggest_task is not None:
                self[guild.id]._resuggest_task.cancel()
                self[guild.id]._resuggest_task = None

            if len(ui_guild_info.previous_titles) > 64:
                ui_guild_info.previous_titles.pop(0)
                print(f'[Suggestion] The history storage of {guild.id} was full, removed the first item')
            
            self[guild.id]._resuggest_task = await asyncio.wait_for(self._process_resuggestion(guild, ui_guild_info.suggestions_source, ui_guild_info), None)

            ui_guild_info.previous_titles.append(ui_guild_info.suggestions[0].title)
            print(f'[Suggestion] Suggested {ui_guild_info.suggestions[0].title} for {guild.id} in next song, added to history storage')
            await self.add_songs(guild.id, ui_guild_info.suggestions.pop(0), '自動推薦歌曲')

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
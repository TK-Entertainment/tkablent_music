import random
from typing import *
import asyncio
import discord
import wavelink
import spotipy
from spotipy import SpotifyClientCredentials
from wavelink.ext import spotify
from ytmusicapi import YTMusic

from ..Helper.PlaylistHelper import PlaylistHelper
from .GuildUIInfo import GuildUIInfo
from ..Misc.Enums import SpotifyAlbum, SpotifyPlaylist, LoopState

INF = int(1e18)

class SeekError(Exception): ...
class OutOfBound(Exception): ...

class PlaylistStorage:
    def __init__(self):
        self._guilds_info: Dict[int, PlaylistHelper] = dict()
        self.spotify = None
        self.ytapi: YTMusic = YTMusic(requests_session=False)
        
    def __getitem__(self, guild_id) -> PlaylistHelper:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = PlaylistHelper()
        return self._guilds_info[guild_id]

    def delete(self, guild_id):
        if self._guilds_info.get(guild_id) is not None:
            self._guilds_info.pop(guild_id, None)

    def init_spotify(self, spotify_id, spotify_secret):
        self.spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(client_id=spotify_id, client_secret=spotify_secret)
        )

    def check_current_suggest_support(self, guild_id: int) -> bool:
        current = self[guild_id].current()
        unsupported_source = [
            'soundcloud',
            'bilibili'
        ]

        return not (current.audio_source in unsupported_source)

    async def add_songs(self, guild_id, trackinfo: Union[wavelink.YouTubeTrack, wavelink.SoundCloudTrack, wavelink.YouTubePlaylist], requester):
        if len(self[guild_id].order) == 2 and self[guild_id].order[1].suggested:
            if isinstance(trackinfo, list):
                self[guild_id].order.pop(1)
            elif (not trackinfo.suggested):
                self[guild_id].order.pop(1)

        if isinstance(trackinfo, Union[SpotifyAlbum, SpotifyPlaylist, wavelink.YouTubePlaylist, list]):
            if isinstance(trackinfo, Union[SpotifyAlbum, SpotifyPlaylist, wavelink.YouTubePlaylist]):
                for track in trackinfo.tracks:
                    track.requester = requester
                    track.audio_source = 'youtube'
                    track.suggested = False
                self[guild_id].order.extend(trackinfo.tracks)
            else:
                for track in trackinfo:
                    track.requester = requester
                self[guild_id].order.extend(trackinfo)
            
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

playlist_storage = PlaylistStorage()
from typing import *

import bilibili_api as bilibili
import wavelink
import discord
import validators
from enum import Enum, auto

from .ui import UI

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
    def __init__(self, ui_comp: UI, ):
        self.ui = ui_comp
        
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
                    trackinfo = await wavelink.Playable.search(query=raw_url)
                except Exception as e:
                    raw_url = None
                    continue
                break
            else:
                raw_url = None

        if raw_url == None:
            return None

        try:
            trackinfo = await wavelink.Playable.search(raw_url)
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
        else:
            url = raw_url

        return url

    async def _get_track(
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
            else:
                tracks.extend(track)

        elif validators.url(search):
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
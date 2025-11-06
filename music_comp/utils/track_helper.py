from typing import TYPE_CHECKING, Optional, Union, Dict, List, Literal
if TYPE_CHECKING:
    from typing import *

import bilibili_api as bilibili
from ytmusicapi import YTMusic
import wavelink
import discord
import logging
from sentry_sdk import capture_exception
from discord import app_commands
import validators
import asyncio
import time
import os
import random
from difflib import SequenceMatcher
import queue

from music_comp.ui import UI, _sec_to_hms
from music_comp.playlist import LoopState, Playlist, PlaylistBase
from .storage import GuildUIInfo, GuildInfo
from .cache import CacheWorker
from music_comp.enums import SearchType

class TrackHelper():
    def __init__(self, ui_comp: UI, playlist: Playlist):
        # bilibili needed value
        SESSDATA = os.getenv("SESSDATA")
        BILI_JCT = os.getenv("BILI_JCT")
        BUVID3 = os.getenv("BUVID3")
        DEDEUSERID = os.getenv("DEDEUSERID")
        AC_TIME_VALUE = os.getenv("AC_TIME_VALUE")

        self.ui = ui_comp
        self._cachequeue = queue.Queue()
        self._cache_worker: CacheWorker = CacheWorker(self._cachequeue)
        self._cache: dict = self._cache_worker._cache
        self._playlist = playlist
        self.ytapi: YTMusic = YTMusic(requests_session=False, language="zh_TW")

        # Bilibili API init
        self._bilibilic = bilibili.Credential(
            sessdata=SESSDATA,
            bili_jct=BILI_JCT,
            buvid3=BUVID3,
            dedeuserid=DEDEUSERID,
            ac_time_value=AC_TIME_VALUE
        )

        self._cache_worker.start()

    def __getitem__(self, guild_id: int=None) -> PlaylistBase:
        return self._playlist[guild_id]

    def check_current_suggest_support(self, guild_id) -> Optional[bool]:
        current = self[guild_id].current()

        if current is None:
            return None

        return (
            current.source == "youtube"
        )
# ================================================================================================= #
#   Search Suggestion Process (Quick Search)
        
    # Processing track information for search suggestion
    async def _search_suggest_processing(self, result: list, track: wavelink.Playable, data: dict, with_arrow=False):
        try:
            if track.source == "http":
                vtitle = track.extras.title
                duration = track.extras.duration
                identifier = track.extras.identifier
            else:
                vtitle = track.title
                duration = track.length
                identifier = track.identifier

            if self._cache.get(identifier) is not None:
                expired = (
                    int(time.time())
                    - self._cache.get(identifier)["timestamp"]
                ) >= 2592000

                if not expired:
                    result.append(
                        app_commands.Choice(
                            name="{}{} | {}".format(">> " if with_arrow else "", self._cache[identifier]['title'], self._cache[identifier]['length']),
                            value=f"sid=>{identifier}",
                        )
                    )
                    return

            if isinstance(track, str):
                return

            length = _sec_to_hms(
                seconds=(duration) / 1000, format="symbol"
            )

            left_name_length = 70 - len(f" | {length}")
            if with_arrow:
                left_name_length -= len(">> ")
                

            if len(vtitle) >= left_name_length + len(" ..."):
                title = vtitle[:left_name_length] + " ..."
            else:
                title = vtitle

            result.append(
                app_commands.Choice(
                    name="{}{} | {}".format(">> " if with_arrow else "", title, length),
                    value=f"sid=>{identifier}",
                )
            )

            timestamp = int(time.time())
            data[identifier] = dict(
                title=title, length=length, timestamp=timestamp
            )
        except Exception as e:
            logging.error(f"Error in search suggestion processing: {e}")
            capture_exception(e)
            return None

    async def _fetch_fast_suggestion(self, interaction: discord.Interaction, trackid: Union[list, str], result: list, data: dict):
        try:
            if not isinstance(trackid, str):
                trackid = trackid[0]
            
            if self._cache.get(trackid) is None or (int(time.time()) - self._cache.get(trackid)["timestamp"] >= 2592000):
                try:
                    track = await self.get_track(interaction, f"sid=>{trackid}", quick_search=True)
                except Exception:
                    return
                if track is not None:
                    await self._search_suggest_processing(result, track[0], data, with_arrow=True)
            else:
                result.append(
                    app_commands.Choice(
                        name="{}{} | {}".format(">> ", self._cache[trackid]["title"], self._cache[trackid]["length"]),
                        value=f"sid=>{trackid}",
                    )
                ) 
        except wavelink.exceptions.LavalinkLoadException as e:
            logging.error(f"Error in fetching fast suggestion: {e}")
            capture_exception(e)
            return None
        
    async def fetch_all_tracks(self, interaction: discord.Interaction, trackid: Union[list, str], result: list):
        if not isinstance(trackid, str):
            trackid = trackid[0]
        try:
            result.extend(await self.get_track(interaction, f"sid=>{trackid}", quick_search=True))
        except Exception:
            return

    # Main part for search suggestion system
    async def get_search_suggest(
        self, interaction: discord.Interaction, current: str, guild_info: GuildInfo
    ) -> List[app_commands.Choice[str]]:
        data = {}
        if current == "":
            choicelist = []
            if len(guild_info.favorite) != 0:
                choicelist.append(app_commands.Choice(
                    name="❤️【這群ㄉ最愛】(請點擊前方有 >> 的項目)",
                    value="",
                ))
                choicelist.append(app_commands.Choice(
                    name=">> 播放全部最愛歌曲",
                    value="sid=>playallfav",
                ))
                tracks = []
                result = []
                async with asyncio.TaskGroup() as taskgroup:
                    for i, trackid in enumerate(guild_info.favorite):
                        if i > 2:
                            choicelist.append(app_commands.Choice(
                                name=">> 列出所有最愛歌曲",
                                value="sid=>showallfav",
                            ))
                            break
                        taskgroup.create_task(self._fetch_fast_suggestion(interaction, trackid, result, data))
                choicelist.extend(result)
                choicelist.append(app_commands.Choice(
                    name="=====================",
                    value=""))
            choicelist.append(app_commands.Choice(
                name="💖【好聽一直聽】(請點擊前方有 >> 的項目)",
                value="",
            ))
            if len(guild_info.mostly_played) <= 10:
                choicelist.append(app_commands.Choice(
                    name="== ❌ | 目前此項資料不足，暫時不可用。",
                    value="",
                ))
            else:
                tracks = []
                result = []
                async with asyncio.TaskGroup() as taskgroup:
                    for i, trackid in enumerate(guild_info.mostly_played):
                        if i >= 4:
                            break
                        taskgroup.create_task(self._fetch_fast_suggestion(interaction, trackid, result, data))
                choicelist.extend(result)
            
            choicelist.extend([
                app_commands.Choice(
                name="=====================",
                value=""),
                app_commands.Choice(
                name="🕒【最近播放】(請點擊前方有 >> 的項目)",
                value="")
                ])
            if len(guild_info.recently_played) == 0:
                choicelist.append(app_commands.Choice(
                    name="== ❌ | 最近這個群組沒放過啥歌 (*°∀°)",
                    value="",
                ))
            else:
                tracks = []
                result = []
                async with asyncio.TaskGroup() as taskgroup:
                    for trackid in guild_info.recently_played:
                        taskgroup.create_task(self._fetch_fast_suggestion(interaction, trackid, result, data))
                choicelist.extend(result)

            self._cachequeue.put(data)

            return choicelist
        elif validators.url(current):
            if ("spotify" in current):
                follow_text = " Spotify 曲目"
            elif ("bilibili" in current) or ("b23.tv" in current):
                follow_text = " Bilibili 曲目"
            elif ("soundcloud" in current):
                follow_text = " SoundCloud 曲目"
            else:
                follow_text = "曲目"

            return [app_commands.Choice(
                name=f">> 透過 URL 點播{follow_text}",
                value=f"{current}",
            )]
        else:
            try:
                tracks = await self.get_track(interaction, current, quick_search=True)

                if tracks is None:
                    return [app_commands.Choice(name="❌ | 沒有找到曲目", value="")]
            except bilibili.ArgsException:
                return [app_commands.Choice(name="❌ | Bilibili VID/AID 格式錯誤", value="")]
            except wavelink.LavalinkLoadException as e:
                logging.error(f"Error in search suggestion in wavelink: {e}")
                capture_exception(e)
                return [app_commands.Choice(name="❌ | 抓取曲目時發生問題", value="")]
            except Exception as e:
                logging.error(f"Generic error in search suggestion: {e}")
                capture_exception(e)
                return [app_commands.Choice(name="❌ | 抓取曲目時發生問題", value="")]
            result = []

            async with asyncio.TaskGroup() as taskgroup:
                for i in range(len(tracks)):
                    if i == 16:
                        break
                    
                    # WTF IS THIS, THIS IS WAY FASTER?
                    # EDIT: This is faster than past versions
                    # EDIT: BUT it isn't because of the usage of asyncio
                    # EDIT: It's because the shit coding (put asyncio.sleep inside for loop)
                    taskgroup.create_task(self._search_suggest_processing(result, tracks[i], data))

            current_index = 0
            last_index = 0

            for i, track in enumerate(result):
                if track.name.startswith("(🕒)") or track.name.startswith("(⭐)"):
                    continue
                index = -1
                if track.value[5:] in guild_info.favorite:
                    index = 0
                    result.pop(i)
                    if len(track.name + "(❤️) ") >= 100:
                        track.name = "(❤️) " + track.name.split(" | ")[0][:-10] + " ..." + " | " + track.name.split(" | ")[1]
                    else:
                        track.name = "(❤️) " + track.name
                    result.insert(0, track)
                else:
                    for j, trackinfo in enumerate(guild_info.mostly_played):
                        if trackinfo[0] == track.value[5:]:
                            index = j
                            break
                    if index == -1:
                        continue
                    result.pop(i)
                    if len(track.name + "(🕒) ") >= 100:
                        track.name = "(🕒) " + track.name.split(" | ")[0][:-10] + " ..." + " | " + track.name.split(" | ")[1]
                    else:
                        track.name = "(🕒) " + track.name
                    if index < last_index:
                        result.insert(0, track)
                    else:
                        result.insert(current_index, track)
                last_index = index
                current_index += 1

            self._cachequeue.put(data)
            return result
            
# ================================================================================================= #
#   Track Fetching System        

    # Getting songs via bilibili api
    async def _get_bilibili_track(self, interaction: discord.Interaction, vid_or_aid: str, quick_search: bool = False) -> Union[wavelink.Playable, wavelink.LavalinkLoadException, None]:
        logging.info(f"BiliBili Cookie validity: {await self._bilibilic.check_valid()}")
        
        if "BV" in vid_or_aid:
            vid = vid_or_aid
        else:
            vid = bilibili.aid2bvid(int(vid_or_aid))

        try:
            logging.debug(f"[Bili] Fetching video data for {vid}")
            v_data = bilibili.video.Video(bvid=vid, credential=self._bilibilic)
            logging.debug(f"[Bili] Fetching video data for {vid} done")
        except bilibili.ArgsException as e:
            logging.debug(f"Error in fetching bilibili video data: {e}")
            raise e
        download_url_data = await v_data.get_download_url(0)
        detector = bilibili.video.VideoDownloadURLDataDetecter(download_url_data)

        data = detector.detect_all()
        data.reverse()

        raw_url = None

        for t in data:
            logging.debug(f"[Bili] Detected stream: {t}")
            #raw_url = t.url.replace("&", "%26")
            if isinstance(t, bilibili.video.AudioStreamDownloadURL):
                raw_url = t.url
                try:
                    logging.debug(f"[Bili] Fetching track for {vid}")
                    await wavelink.Pool.fetch_tracks(raw_url, node=wavelink.Pool.get_node("BilibiliNode"))
                    logging.debug(f"[Bili] Fetching track for {vid} done")
                except wavelink.LavalinkLoadException as e:
                    logging.debug(f"Error in fetching track: {e}")
                    raw_url = None
                    continue
                break
            else:
                continue

        if raw_url is None:
            logging.warning(f"No audio stream found for {vid}")
            raise Exception("No audio stream found")

        try:
            trackinfo = await wavelink.Pool.fetch_tracks(raw_url, node=wavelink.Pool.get_node("BilibiliNode"))
        except wavelink.LavalinkLoadException as e:
            raise e

        track = trackinfo[0]
        vinfo = await v_data.get_info()
        track.extras = {
            "title": vinfo["title"],
            "author": vinfo["owner"]["name"], 
            "identifier": vinfo["bvid"],
            "duration": vinfo["duration"] * 1000,
        }

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
        elif "https://www.bilibili.com/" in raw_url or "https://b23.tv/" in raw_url:
            url = raw_url.split("/")[4]
        elif "sid=>" in raw_url:
            vid = raw_url.split("=>")[1]
            if vid.startswith("BV") or isinstance(vid, int):
                url = vid
            else:
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
    ) -> list[Union[wavelink.Playable, wavelink.Playlist]]:
        if not quick_search:
            await interaction.response.defer(ephemeral=True, thinking=True)

        tracks = []
        nodes = [
            wavelink.Pool.get_node("SearchNode_1"),
            wavelink.Pool.get_node("SearchNode_2"),
        ]

        if (("bilibili" in search or "b23.tv" in search) and validators.url(search)) or (search.startswith("sid=>BV")):
            url = self._parse_url(search, choice)
            try:
                track = await self._get_bilibili_track(interaction, url)
            except Exception as track_exception:
                if not quick_search:
                    raise track_exception
                return
            tracks.append(track)

        elif (validators.url(search)) or ("sid=>" in search):
            url = self._parse_url(search, choice)
            try:
                callback = await wavelink.Playable.search(url, node=random.choice(nodes))
            except wavelink.exceptions.LavalinkLoadException as e:
                logging.error(f"Error in fetching track: {e}")
                capture_exception(e)
                callback = None
            if callback is None:
                if not quick_search:
                    raise Exception("No result found")
                return
            elif isinstance(callback, list):
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
                    wavelink.TrackSource.YouTube,
                    wavelink.TrackSource.YouTubeMusic, 
                    SearchType.spotify(),
                    wavelink.TrackSource.SoundCloud,
                ]

            for source in sources:
                try:
                    data = await wavelink.Playable.search(search, source=source, node=random.choice(nodes))
                    if data is not None:
                        tracks.extend(data)
                except Exception:
                    # When there is no result for provided method
                    # Then change to next method to search
                    continue

        if len(tracks) == 0 and not quick_search:
            raise Exception("No result found")
        
        return tracks

# ================================================================================================= #
#   Auto Suggestion Processing System

    async def _get_suggest_track(
        self,
        suggestion: Dict[str, List[Dict]],
        index: int, # 用於產生推薦的目標歌曲 index
        ui_guild_info: GuildUIInfo,
        pre_process: bool,
    ) -> Optional[wavelink.Playable]:
        suggested_track = None

        nodes = [
            wavelink.Pool.get_node("SearchNode_1"),
            wavelink.Pool.get_node("SearchNode_2"),
        ]

        try:
            suggested_track = await wavelink.Playable.search(
                "https://www.youtube.com/watch?v={}".format(suggestion["tracks"][index]["videoId"]),
                node=random.choice(nodes),
            )
            suggested_track = suggested_track[0]
        except:
            suggested_track = None
            pass

        if suggested_track is not None:
            suggested_track.extras = {"suggested": True, "requested_guild": ui_guild_info.guild_id, **dict(suggested_track.extras)}
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
            resuggested_required = False
            # check first one first
            if ui_guild_info.suggestions[0].title in ui_guild_info.previous_titles:
                logging.info(
                    f"[{guild.id} | Suggestion] {ui_guild_info.suggestions[0].title} has played before, resuggested"
                )
                ui_guild_info.suggestions.pop(0)
                resuggested_required = True
            else:
                for previous_titles in ui_guild_info.previous_titles:
                    match_ratio = SequenceMatcher(None, ui_guild_info.suggestions[0].title, previous_titles).ratio()
                    if match_ratio >= 0.92:
                        logging.info(
                            f"[{guild.id} | Suggestion] {ui_guild_info.suggestions[0].title} has played before, resuggested"
                        )
                        logging.debug("[DEBUG ONLY] ", ui_guild_info.previous_titles)
                        logging.debug(f"[DEBUG ONLY] {previous_titles} is detected match with {ui_guild_info.suggestions[0].title} with ratio {match_ratio}")
                        ui_guild_info.suggestions.pop(0)
                        resuggested_required = True

            if resuggested_required:
                tried = 0
                while suggested_track is None and tried < 20:
                    suggested_track = await self._get_suggest_track(
                        suggestion, suggestion["index"], ui_guild_info, pre_process=True
                    )

                    if suggested_track is not None:
                        break
                    else:
                        suggestion = await self._get_suggest_list(guild, playlist_index)
                        playlist_index += 1
                        tried += 1
                if suggested_track is None:
                    ui_guild_info.suggestion_failure = True
                    await self.ui._InfoGenerator._UpdateSongInfo(guild.id)
                    return
                    

        self[guild.id]._suggest_search_task = await asyncio.wait_for(
            self._search_for_suggestion(guild, suggestion, ui_guild_info), None
        )
        suggested_track = None

        # wait for rest of suggestions to be processed, and check them
        for i, track in enumerate(ui_guild_info.suggestions):
            resuggested_required = False
            if track.title in ui_guild_info.previous_titles:
                logging.info(
                    f"[{guild.id} | Suggestion] {track.title} has played before, resuggested"
                )
                ui_guild_info.suggestions.pop(i)
                resuggested_required = True
            else:
                for previous_titles in ui_guild_info.previous_titles:
                    match_ratio = SequenceMatcher(None, track.title, previous_titles).ratio()
                    if match_ratio >= 0.92:
                        logging.info(
                            f"[{guild.id} | Suggestion] {track.title} has played before, resuggested"
                        )
                        logging.debug("[DEBUG ONLY] ", ui_guild_info.previous_titles)
                        logging.debug(f"[DEBUG ONLY] {previous_titles} is detected match with {track.title} with ratio {match_ratio}")
                        ui_guild_info.suggestions.pop(i)
                        resuggested_required = True

            if resuggested_required:
                tried = 0
                while suggested_track is None and tried < 20:
                    suggested_track = await self._get_suggest_track(
                        suggestion, suggestion["index"], ui_guild_info, pre_process=True
                    )

                    if suggested_track is not None:
                        break
                    else:
                        suggestion = await self._get_suggest_list(guild, playlist_index)
                        playlist_index += 1
                        tried += 1
                if suggested_track is None:
                    ui_guild_info.suggestion_failure = True
                    await self.ui._InfoGenerator._UpdateSongInfo(guild.id)
                    return

    # This part maintain suggestion fetching
    async def _search_for_suggestion(
        self, guild, suggestion, ui_guild_info: GuildUIInfo
    ):
        playlist_index = 1
        suggested_track = None

        if len(ui_guild_info.suggestions) == 0:
            logging.info(f"[{guild.id} | Suggestion] Started to fetch 12 suggestions")

            tried = 0

            while suggested_track is None and tried < 20:
                for index in range(2, 13, 1):
                    suggested_track = await self._get_suggest_track(
                        suggestion, index, ui_guild_info, pre_process=False
                    )

                    if suggested_track is not None:
                        break
                    else:
                        suggestion = await self._get_suggest_list(guild, playlist_index)
                        playlist_index += 1
                        tried += 1

            if suggested_track is None:
                ui_guild_info.suggestion_failure = True
                await self.ui._InfoGenerator._UpdateSongInfo(guild.id)
                return

            logging.info(f"[{guild.id} | Suggestion] Fetched 12 suggestions\n{suggested_track}")

    # Main core of suggestion processing system
    # Which decides whether enable suggestion or not in different cases
    async def process_suggestion(
        self, guild: discord.Guild, ui_guild_info: GuildUIInfo
    ):
        ui_guild_info.suggestion_failure = False
        # Check whether current song is supported in suggestion system or not
        if (
            (ui_guild_info.music_suggestion)
            and self.check_current_suggest_support(guild.id)
            and len(self[guild.id].order) <= 2
        ):
            # If next song is user specific, then don't suggest anything
            if (
                len(self[guild.id].order) == 2
                and not self[guild.id].order[-1].extras.suggested
            ):
                return

            # Flag suggestion is in progress
            ui_guild_info.suggestion_processing = True

            if self[guild.id].loop_state != LoopState.NOTHING:
                # If loop state is singleloop, then don't add suggested song into cache
                # Since it even hasn't been played yet
                # Also won't return any suggestion
                if self[guild.id].loop_state != LoopState.PLAYLIST:
                    if len(self[guild.id].order) == 2 and (
                        self[guild.id].order[-1].extras.suggested
                    ):
                        ui_guild_info.previous_titles.remove(
                            self[guild.id].order[-1].title
                        )
                        self._playlist.pop(guild.id, -1)
                    return
                # Case of playlist loop
                else:
                    if self[guild.id].current().extras.suggested:
                        # Suggestion system here will ignore playlist loop
                        # Acting like loop not enabled 
                        # if current song is a song suggested
                        if len(self[guild.id].order) == 2 and (
                            self[guild.id].order[-1].extras.suggested
                        ):
                            return
                    else:
                        # Same thing like single loop
                        if len(self[guild.id].order) == 2 and (
                            self[guild.id].order[-1].extras.suggested
                        ):
                            ui_guild_info.previous_titles.remove(
                                self[guild.id].order[-1].title
                            )
                            self._playlist.pop(guild.id, -1)
                            return

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

                tried = 0

                while suggested_track is None and tried < 20:
                    suggested_track = await self._get_suggest_track(
                        suggestion, index, ui_guild_info, pre_process=False
                    )

                    if suggested_track is None:
                        index += 1
                        tried += 1
                
                if suggested_track is None:
                    ui_guild_info.suggestion_failure = True
                    try:
                        await self.ui._InfoGenerator._UpdateSongInfo(guild.id)
                    finally:
                        return

            if self[guild.id]._resuggest_task is not None:
                self[guild.id]._resuggest_task.cancel()
                self[guild.id]._resuggest_task = None

            if len(ui_guild_info.previous_titles) > 64:
                ui_guild_info.previous_titles.pop(0)
                logging.info(
                    f"[{guild.id} | Suggestion] The history storage was full, removed the first item"
                )

            self[guild.id]._resuggest_task = await asyncio.wait_for(
                self._process_resuggestion(
                    guild, ui_guild_info.suggestions_source, ui_guild_info
                ),
                None,
            )

            ui_guild_info.previous_titles.append(ui_guild_info.suggestions[0].title)
            logging.info(
                f"[{guild.id} | Suggestion] Suggested {ui_guild_info.suggestions[0].title} in next song, added to history storage"
            )
            await self._playlist.add_songs(guild.id, [ui_guild_info.suggestions.pop(0)], "NO_ID_AS_BOT_SUGGESTED")
            
            if ui_guild_info.skip:
                ui_guild_info.skip = False
            ui_guild_info.suggestion_processing = False
           
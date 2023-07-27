from typing import *
import wavelink
import discord
import asyncio

from Helper.NodeHelper import node_helper

from Storage.GuildPlayerInfo import GuildInfo_Storage
from Misc.Enums import LoopState
from Storage.PlaylistStorage import playlist_storage

class SuggestionHelper:
    async def _get_suggest_track(
            self, 
            suggestion: Dict[str, List[Dict]], 
            index: int, 
            guild_info: GuildInfo_Storage, 
            pre_process: bool
        ) -> Optional[Union[wavelink.YouTubeMusicTrack, wavelink.YouTubeTrack]]:
        
        searchnode = await node_helper.get_best_searchnode()
        suggested_track = None

        for trackmethod in [wavelink.YouTubeMusicTrack, wavelink.YouTubeTrack]:
            try:
                suggested_track = await trackmethod.search(suggestion['tracks'][index]['videoId'], node=searchnode)
                suggested_track = suggested_track[0]
            except:
                suggested_track = None
                pass
            if suggested_track is not None:
                suggested_track.suggested = True
                suggested_track.audio_source = 'youtube'
                guild_info.suggestions.append(suggested_track)

                if pre_process:
                    suggestion['index'] += 1

                break
        
        return suggested_track

    async def _get_suggest_list(self, guild: discord.Guild, playlist_index: int) -> Dict[str, List[Dict]]:
        suggestion = self.ytapi.get_watch_playlist(
            videoId=playlist_storage[guild.id].order[playlist_index].identifier, 
            limit=5
        )
        
        suggestion['index'] = 13

        return suggestion

    async def _process_resuggestion(self, guild, suggestion, guild_info: GuildInfo_Storage) -> None:
        playlist_index = 1
        suggested_track = None
        

        if len(guild_info.suggestions) != 0:
            # check first one first
            if guild_info.suggestions[0].title in guild_info.previous_titles:
                print(f'[Suggestion] {guild_info.suggestions[0].title} has played before in {guild.id}, resuggested')
                guild_info.suggestions.pop(0)

                while suggested_track is None:
                    suggested_track = await self._get_suggest_track(
                        suggestion, 
                        suggestion['index'], 
                        guild_info, 
                        pre_process=True
                    )

                    if suggested_track is not None:
                        break
                    else:
                        suggestion = await self._get_suggest_list(guild, playlist_index)
                        playlist_index += 1

        guild_info._suggest_search_task = await asyncio.wait_for(self._search_for_suggestion(guild, suggestion, guild_info), None)
        suggested_track = None

        # wait for rest of suggestions to be processed, and check them
        for i, track in enumerate(guild_info.suggestions):
            if track.title in guild_info.previous_titles:
                print(f'[Suggestion] {track.title} has played before in {guild.id}, resuggested')
                guild_info.suggestions.pop(i)
                while suggested_track is None:
                    suggested_track = await self._get_suggest_track(
                            suggestion, 
                            suggestion['index'], 
                            guild_info, 
                            pre_process=True
                        )
                    
                    if suggested_track is not None:
                        break
                    else:
                        suggestion = await self._get_suggest_list(guild, playlist_index)
                        playlist_index += 1

    async def _search_for_suggestion(self, guild, suggestion, guild_info: GuildInfo_Storage):
        playlist_index = 1
        suggested_track = None

        if len(guild_info.suggestions) == 0:

            print(f'[Suggestion] Started to fetch 12 suggestions for {guild.id}')

            while suggested_track is None:
                for index in range(2, 13, 1):
                    suggested_track = await self._get_suggest_track(
                            suggestion, 
                            index, 
                            guild_info, 
                            pre_process=False
                        )
                    
                    if suggested_track is not None:
                        break
                    else:
                        suggestion = await self._get_suggest_list(guild, playlist_index)
                        playlist_index += 1
        
    async def process_suggestion(self, guild: discord.Guild, guild_info: GuildInfo_Storage):
        if (guild_info.music_suggestion) and playlist_storage[guild.id].current().audio_source == 'youtube' and len(playlist_storage[guild.id].order) <= 2:
            if len(playlist_storage[guild.id].order) == 2 and not playlist_storage[guild.id].order[-1].suggested:
                return

            # If bot 
            if (playlist_storage[guild.id].loop_state != LoopState.NOTHING):
                if playlist_storage[guild.id].loop_state != LoopState.PLAYLIST:
                    if len(playlist_storage[guild.id].order) == 2 and (playlist_storage[guild.id].order[-1].suggested):
                        guild_info.previous_titles.remove(playlist_storage[guild.id].order[-1].title)
                        playlist_storage.pop(guild.id, -1)
                    return
                else:
                    if playlist_storage[guild.id].current().suggested:
                        if len(playlist_storage[guild.id].order) == 2 and (playlist_storage[guild.id].order[-1].suggested):
                            return
                    else:
                        if len(playlist_storage[guild.id].order) == 2 and (playlist_storage[guild.id].order[-1].suggested):
                            guild_info.previous_titles.remove(playlist_storage[guild.id].order[-1].title)
                            playlist_storage.pop(guild.id, -1)
                            return

            suggested_track = None

            if playlist_storage[guild.id].current().title not in guild_info.previous_titles:
                guild_info.previous_titles.append(playlist_storage[guild.id].current().title)
            
            if len(guild_info.suggestions) == 0:
                index = 1
                suggestion = guild_info.suggestions_source = self.ytapi.get_watch_playlist(videoId=playlist_storage[guild.id].current().identifier, limit=5)
                guild_info.suggestions_source['index'] = 13

                while suggested_track is None:
                    suggested_track = await self._get_suggest_track(
                            suggestion, 
                            index, 
                            guild_info, 
                            pre_process=False
                        )
                    
                    if suggested_track is not None:
                        if guild_info._refresh_msg_task is not None:
                            guild_info._refresh_msg_task.cancel()
                            guild_info._refresh_msg_task = None
                        break
                    else:
                        index += 1

            if guild_info._resuggest_task is not None:
                guild_info._resuggest_task.cancel()
                guild_info._resuggest_task = None

            if len(guild_info.previous_titles) > 64:
                guild_info.previous_titles.pop(0)
                print(f'[Suggestion] The history storage of {guild.id} was full, removed the first item')
            
            guild_info._resuggest_task = await asyncio.wait_for(self._process_resuggestion(guild, guild_info.suggestions_source, guild_info), None)

            guild_info.previous_titles.append(guild_info.suggestions[0].title)
            print(f'[Suggestion] Suggested {guild_info.suggestions[0].title} for {guild.id} in next song, added to history storage')
            await playlist_storage.add_songs(guild.id, guild_info.suggestions.pop(0), '自動推薦歌曲')

suggestion_helper = SuggestionHelper()
from typing import *
import discord
import requests
import random
import datetime
import copy

import wavelink
from wavelink.ext import spotify
from ..playlist import LoopState, SpotifyAlbum, SpotifyPlaylist
from ..ui import LeaveType, StopType
from ..ui import caution_emoji, spotify_emoji, skip_emoji, search_emoji, repeat_emoji

class InfoGenerator:
    def __init__(self):
        from ..ui import musicbot, bot, _sec_to_hms, embed_opt,\
                        auto_stage_available, guild_info

        self.musicbot = musicbot
        self.bot = bot
        self._sec_to_hms = _sec_to_hms
        self.embed_opt = embed_opt
        self.auto_stage_available = auto_stage_available
        self.guild_info = guild_info



    def _PlaylistInfo(self, playlist: Union[SpotifyAlbum, wavelink.YouTubePlaylist], requester: discord.User):
        # Generate Embed Body
        if isinstance(playlist, list):
            title = f"{search_emoji} | 選取的搜尋歌曲"
            url = None
        elif isinstance(playlist, wavelink.YouTubePlaylist):
            title = f":newspaper: | 音樂播放清單"
            url = None
        else:
            title = f"{spotify_emoji} | {playlist.name}"
            url = playlist.uri

        color = discord.Colour.from_rgb(97, 219, 83)
        embed = discord.Embed(title=title, url=url, colour=color)
        if requester.discriminator == "0":
            embed.set_author(name=f"此播放清單由 {requester.name} 點播", icon_url=requester.display_avatar)
        else:
            embed.set_author(name=f"此播放清單由 {requester.name}#{requester.discriminator} 點播", icon_url=requester.display_avatar)

        pllist: str = ""
        if isinstance(playlist, list):
            tracklist = playlist
        else:
            tracklist = playlist.tracks
        for i, track in enumerate(tracklist):
            pllist += f"{i+1}. {track.title}\n"
            if i == 1: 
                break
        if len(tracklist) > 2:
            pllist += f"...還有 {len(tracklist)-2} 首歌"
        
        embed.add_field(name=f"歌曲清單 | 已新增 {len(tracklist)} 首歌", value=pllist, inline=False)
        if isinstance(playlist, Union[SpotifyPlaylist, SpotifyAlbum]):
            embed.set_thumbnail(url=playlist.thumbnail)
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))

        return embed

    async def _UpdateSongInfo(self, guild_id: int):
        if len(self.musicbot._playlist[guild_id].order) == 0:
            await self.guild_info(guild_id).playinfo.edit(embed=self._SongInfo(guild_id), view=None)
        else:
            self.guild_info(guild_id).playinfo_view.skip.emoji = skip_emoji
            if len(self.musicbot._playlist[guild_id].order) == 1:
                self.guild_info(guild_id).playinfo_view.skip.style = discord.ButtonStyle.gray
                self.guild_info(guild_id).playinfo_view.skip.disabled = True
            else:
                self.guild_info(guild_id).playinfo_view.skip.style = discord.ButtonStyle.blurple
                self.guild_info(guild_id).playinfo_view.skip.disabled = False

            if self.musicbot._playlist[guild_id].loop_state == LoopState.SINGLE:
                self.guild_info(guild_id).playinfo_view.loop_control.label = f"ₛ {self.musicbot._playlist[guild_id].times} 次"
            elif self.musicbot._playlist[guild_id].loop_state == LoopState.NOTHING:
                self.guild_info(guild_id).playinfo_view.loop_control.emoji = repeat_emoji
                self.guild_info(guild_id).playinfo_view.loop_control.label = ''
                self.guild_info(guild_id).playinfo_view.loop_control.style = discord.ButtonStyle.danger

            if not self.musicbot._playlist.check_current_suggest_support(guild_id):
                self.guild_info(guild_id).playinfo_view.suggest.style = discord.ButtonStyle.gray
                self.guild_info(guild_id).playinfo_view.suggest.disabled = True
            else:
                self.guild_info(guild_id).playinfo_view.suggest.disabled = False
                if self.guild_info(guild_id).music_suggestion:
                    self.guild_info(guild_id).playinfo_view.suggest.style = discord.ButtonStyle.green
                else:
                    self.guild_info(guild_id).playinfo_view.suggest.style = discord.ButtonStyle.danger

            await self.guild_info(guild_id).playinfo.edit(embed=self._SongInfo(guild_id), view=self.guild_info(guild_id).playinfo_view)

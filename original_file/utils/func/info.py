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

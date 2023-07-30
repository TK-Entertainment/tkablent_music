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







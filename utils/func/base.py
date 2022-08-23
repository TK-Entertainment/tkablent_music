from typing import *

import discord

from utils.player import MusicCog

class GuildUIInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.auto_stage_available: bool = True
        self.stage_topic_exist: bool = False
        self.stage_topic_checked: bool = False
        self.skip: bool = False
        self.mute: bool = False
        self.search: bool = False
        self.lasterrorinfo: dict = {}
        self.playinfo: Coroutine[Any, Any, discord.Message] = None
        self.playinfo_view: discord.ui.View = None
        self.processing_msg: discord.Message = None

class UIBase:
    def __init__(self, bot: MusicCog):
        self._guild_ui_info = dict()
        self.bot = bot

    def __getitem__(self, guild_id) -> GuildUIInfo:
        if self._guild_ui_info.get(guild_id) is None:
            self._guild_ui_info[guild_id] = GuildUIInfo(guild_id)
        return self._guild_ui_info[guild_id]
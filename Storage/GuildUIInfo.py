from typing import *
import discord

class GuildUIInfo_Storage:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.auto_stage_available: bool = True
        self.stage_topic_exist: bool = False
        self.stage_topic_checked: bool = False
        self.search: bool = False
        self.lasterrorinfo: dict = {}
        self.processing_msg: discord.Message = None
        self.searchmsg: Coroutine[Any, Any, discord.Message] = None

class GuildUIInfo:
    def __init__(self):
        self._guilds_info: dict[int, GuildUIInfo_Storage] = {}

    def __getitem__(self, guild_id) -> GuildUIInfo_Storage:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = GuildUIInfo_Storage(guild_id)
        return self._guilds_info[guild_id] 
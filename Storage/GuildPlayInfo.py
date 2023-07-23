from typing import *
import discord

class GuildPlayInfo_Storage:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.skip: bool = False
        self.lastskip: bool = False
        self.leaveoperation: bool = False
        self.playinfo: Coroutine[Any, Any, discord.Message] = None
        self.playinfo_view: discord.ui.View = None

class GuildPlayInfo:
    def __init__(self):
        self._guilds_info: dict[int, GuildPlayInfo_Storage] = {}

    def __getitem__(self, guild_id) -> GuildPlayInfo_Storage:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = GuildPlayInfo(guild_id)
        return self._guilds_info[guild_id] 
    
    def delete(self, guild_id):
        if self._guilds_info.get(guild_id) is not None:
            self._guilds_info.pop(guild_id, None)

guild_play_info = GuildPlayInfo()
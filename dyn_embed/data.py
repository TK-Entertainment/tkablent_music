import discord
from typing import *
from enum import Enum, auto

class DynEmbedOperation(Enum):
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    PLAY = auto()
    RESUME = auto()
    PAUSE = auto()
    STOP = auto()
    SKIP = auto()
    ADDTOQUEUE = auto()
    REMOVEFROMQUEUE = auto()
    LEAVE = auto()
    NONE = auto()

class GuildUIInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.dyn_embed_msg: discord.Message = None
        self.auto_stage_available: bool = True
        self.stage_topic_exist: bool = False
        self.stage_topic_checked: bool = False
        self.operation: DynEmbedOperation = DynEmbedOperation.NONE
        self.skipper: discord.Member = None
        self.lastskip: bool = False
        self.mute: bool = False
        self.search: bool = False
        self.lasterrorinfo: dict = {}
        self.processing_msg: discord.Message = None
        self.music_suggestion: bool = False
        self.suggestions_source = None
        self.previous_titles: list[str] = []
        self.suggestions: list = []

_guild_ui_info = dict()

def guild_info(guild_id) -> GuildUIInfo:
    if _guild_ui_info.get(guild_id) is None:
        _guild_ui_info[guild_id] = GuildUIInfo(guild_id)
    return _guild_ui_info[guild_id]

def auto_stage_available(guild_id: int):
    return guild_info(guild_id).auto_stage_available

def reset_value(guild_id):
    guild = guild_info(guild_id)

    guild.auto_stage_available = True
    guild.stage_topic_checked = False
    guild.stage_topic_exist = False
    guild.skip = False
    guild.music_suggestion = False
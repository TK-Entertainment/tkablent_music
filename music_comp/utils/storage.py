from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import *

import discord
import asyncio
import json
import os

class GuildInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.text_channel: discord.TextChannel = None
        self._database: str = rf"{os.getcwd()}/music_comp/data.json"
        self._task: asyncio.Task = None
        self._timer: asyncio.Task = None
        self._dsa: bool = None
        self._multitype_remembered: bool = None
        self._multitype_choice: str = None
        self._timer_done: bool = None
        self._changelogs_latestversion: str = None

    @property
    def data_survey_agreement(self):
        if self._dsa is None:
            self._dsa = self.fetch("dsa")
        return self._dsa

    @data_survey_agreement.setter
    def data_survey_agreement(self, value: bool):
        self._dsa = value
        self.update("dsa", value)

    @property
    def multitype_remembered(self):
        if self._multitype_remembered is None:
            self._multitype_remembered = self.fetch("multitype_remembered")
        return self._multitype_remembered

    @multitype_remembered.setter
    def multitype_remembered(self, value: bool):
        self._multitype_remembered = value
        self.update("multitype_remembered", value)

    @property
    def multitype_choice(self):
        if self._multitype_choice is None:
            self._multitype_choice = self.fetch("multitype_choice")
        return self._multitype_choice

    @multitype_choice.setter
    def multitype_choice(self, value: str):
        self._multitype_choice = value
        self.update("multitype_choice", value)

    @property
    def changelogs_latestversion(self):
        if self._changelogs_latestversion is None:
            self._changelogs_latestversion = self.fetch("changelogs_latestversion")
        return self._changelogs_latestversion
    
    @changelogs_latestversion.setter
    def changelogs_latestversion(self, value: str):
        self._changelogs_latestversion = value
        self.update("changelogs_latestversion", value)

    def fetch(self, key: str) -> None:
        """fetch from database"""
        with open(self._database, "r") as f:
            data: dict = json.load(f)
        if (
            data.get(str(self.guild_id)) is None
            or data[str(self.guild_id)].get(key) is None
        ):
            return data["default"][key]
        return data[str(self.guild_id)][key]

    def update(self, key: str, value: str) -> None:
        """update database"""

        with open(self._database, "r") as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None:
            data[str(self.guild_id)] = dict()
        data[str(self.guild_id)][key] = value
        with open(self._database, "w") as f:
            json.dump(data, f)

class GuildUIInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id

        # Booleans
        # Determine whether auto stage modification available in this server
        # Currently deprecated 
        self.auto_stage_available: bool = True
        # Stage topic existance
        # Bot won't start another stage instance if this is True
        self.stage_topic_exist: bool = False
        # Stage topic checking
        # True if bot already checked the topic
        self.stage_topic_checked: bool = False
        # Indicate the bot has skip the song
        # Will be reseted to False after next song played
        self.skip: bool = False
        # Indicate the last song is skipped or not
        self.lastskip: bool = False
        self.search: bool = False
        self.leaveoperation: bool = False
        self.music_suggestion: bool = False
        # Indicate that the suggestion is under processing
        # Will be reseted to False after process is done
        self.suggestion_processing: bool = False

        self.lasterrorinfo: dict = {}

        self.playinfo: Coroutine[Any, Any, discord.Message] = None
        self.playinfo_view: discord.ui.View = None
        self.processing_msg: discord.Message = None
        self.searchmsg: Coroutine[Any, Any, discord.Message] = None

        self.suggestions_source = None
        self.previous_titles: list[str] = []
        self.suggestions: list = []
from typing import *

import discord
import asyncio
import json
import os

class GuildInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.text_channel: discord.TextChannel = None
        self._task: asyncio.Task = None
        self._refresh_msg_task: asyncio.Task = None
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

    def fetch(self, key: str) -> not None:
        """fetch from database"""
        with open(rf"{os.getcwd()}/utils/data.json", "r") as f:
            data: dict = json.load(f)
        if (
            data.get(str(self.guild_id)) is None
            or data[str(self.guild_id)].get(key) is None
        ):
            return data["default"][key]
        return data[str(self.guild_id)][key]

    def update(self, key: str, value: str) -> None:
        """update database"""

        with open(rf"{os.getcwd()}/utils/data.json", "r") as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None:
            data[str(self.guild_id)] = dict()
        data[str(self.guild_id)][key] = value
        with open(rf"{os.getcwd()}/utils/data.json", "w") as f:
            json.dump(data, f)

class GuildUIInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.auto_stage_available: bool = True
        self.stage_topic_exist: bool = False
        self.stage_topic_checked: bool = False
        self.skip: bool = False
        self.lastskip: bool = False
        self.search: bool = False
        self.lasterrorinfo: dict = {}
        self.leaveoperation: bool = False
        self.playinfo: Coroutine[Any, Any, discord.Message] = None
        self.playinfo_view: discord.ui.View = None
        self.processing_msg: discord.Message = None
        self.music_suggestion: bool = False
        self.suggestions_source = None
        self.searchmsg: Coroutine[Any, Any, discord.Message] = None
        self.previous_titles: list[str] = []
        self.suggestions: list = []
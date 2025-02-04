from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import *

import discord
import asyncio
import os
import wavelink
from msgspec.json import decode as json_decode
from msgspec import DecodeError
from msgspec.json import encode as json_encode

class GuildInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self._text_channel: int = None

        self._database: str = rf"{os.getcwd()}/music_comp/data.json"
        self._task: asyncio.Task = None
        self._multitype_remembered: bool = None
        self._multitype_choice: str = None
        self._changelogs_latestversion: str = None
        self._recently_played: list = None
        self._mostly_played: dict = None
        self._favorite: list = None

    @property
    def text_channel(self):
        if self._text_channel is None:
            self._text_channel = self.fetch("text_channel")
        return self._text_channel
    
    @text_channel.setter
    def text_channel(self, value: int):
        self._text_channel = value
        self.update("text_channel", value)

    @property
    def recently_played(self):
        if self._recently_played is None:
            self._recently_played = self.fetch("recently_played")
        return self._recently_played
    
    @recently_played.setter
    def recently_played(self, value: list):
        self._recently_played = value
        self.update("recently_played", value)

    @property
    def mostly_played(self):
        if self._mostly_played is None:
            self._mostly_played = self.fetch("mostly_played")
        return sorted(self._mostly_played.items(), key=lambda item: item[1], reverse=True)
    
    @mostly_played.setter
    def mostly_played(self, value: list):
        self._mostly_played = value
        self.update("mostly_played", value)

    def song_played(self, song: wavelink.Playable):
        if song.source == "http":
            identifier = song.extras.identifier
        else:
            identifier = song.identifier

        # Initialize the song count to 0 if not present
        if self._recently_played is None:
            self._recently_played = self.fetch("recently_played")
        if self._mostly_played is None:
            self._mostly_played = self.fetch("mostly_played")

        # Update the recently played list
        if identifier in self._recently_played:
            self._recently_played.remove(identifier)
        self._recently_played.insert(0, identifier)
        while len(self._recently_played) > 5:
            self._recently_played.pop()

        if song.extras.requester_id is not None:
            self._mostly_played[identifier] = self._mostly_played.get(identifier, 0) + 1
        self.update("recently_played", self._recently_played)
        self.update("mostly_played", self._mostly_played)

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

    @property
    def favorite(self):
        if self._favorite is None:
            self._favorite = self.fetch("favorite")
        return self._favorite
    
    def add_favorite(self, song: wavelink.Playable):
        if song.source == "http":
            identifier = song.extras.identifier
        else:
            identifier = song.identifier

        if self._favorite is None:
            self._favorite = self.fetch("favorite")
        if identifier not in self._favorite:
            self._favorite.append(identifier)
            self.update("favorite", self._favorite)
    
    def remove_favorite(self, song: wavelink.Playable):
        if song.source == "http":
            identifier = song.extras.identifier
        else:
            identifier = song.identifier

        if self._favorite is None:
            self._favorite = self.fetch("favorite")
        if identifier in self._favorite:
            self._favorite.remove(identifier)
            self.update("favorite", self._favorite)

    def fetch(self, key: str) -> None:
        """fetch from database"""
        with open(self._database, "rb") as f:
            data: dict = json_decode(f.read())
        if (
            data.get(str(self.guild_id)) is None
            or data[str(self.guild_id)].get(key) is None
        ):
            return data["default"][key]
        return data[str(self.guild_id)][key]

    def update(self, key: str, value: str) -> None:
        """update database"""

        with open(self._database, "rb") as f:
            data: dict = json_decode(f.read())
        if data.get(str(self.guild_id)) is None:
            data[str(self.guild_id)] = dict()
        data[str(self.guild_id)][key] = value
        with open(self._database, "wb") as f:
            f.write(json_encode(data))

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
        self.suggestion_failure: bool = False

        self.lasterrorinfo: dict = {}

        self.playinfo: Coroutine[Any, Any, discord.Message] = None
        self.playinfo_view: discord.ui.View = None
        self.processing_msg: discord.Message = None
        self.searchmsg: Coroutine[Any, Any, discord.Message] = None

        self.suggestions_source = None
        self.previous_titles: list[str] = []
        self.suggestions: list = []

        self.timer_task: asyncio.Task = None
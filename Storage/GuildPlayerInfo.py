import discord
import asyncio
import json
import os

from ..Misc.Enums import MultiType
from ..UI.Generic.Enums import Language

class GuildInfo_Storage:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.text_channel: discord.TextChannel = None
        self._task: asyncio.Task = None

        # If user skipped the song or a song finish playing
        # This should be not None (To refresh the message)
        self._refresh_msg_task: asyncio.Task = None

        self._resuggest_task: asyncio.Task = None

        self._suggest_search_task: asyncio.Task = None

        # Leave timeout timer
        self._timer: asyncio.Task = None

        # Needed if we have to do something related to data collecting
        # According to Privacy Policy
        self._dsa: bool = None

        # /playwith command related
        # Mark if the multitype link settings is set
        self._multitype_remembered: bool = None
        # Mark multitype link choice
        # Should be None if self._multitype_remembered is False
        self._multitype_choice: MultiType = None

        self._language: Language = Language.zh_tw

        # Mark leave timeout timer is finished or not
        self._timer_done: bool = None

        # Music suggestion
        self.music_suggestion: bool = False
        self.suggestions_source = None
        self.previous_titles: list[str] = []
        self.suggestions: list = []

    @property
    def data_survey_agreement(self):
        if self._dsa is None:
            self._dsa = self._fetch('dsa')
        return self._dsa

    @data_survey_agreement.setter
    def data_survey_agreement(self, value: bool):
        self._dsa = value
        self._update("dsa", value)

    @property
    def multitype_remembered(self) -> bool:
        '''
        /playwith command related

        Mark if the multitype link settings is set, returns Boolean

        If this is False, multitype_choice should be None
        '''

        if self._multitype_remembered is None:
            self._multitype_remembered = self._fetch('multitype_remembered')
        return self._multitype_remembered
    
    @multitype_remembered.setter
    def multitype_remembered(self, value: bool):
        self._multitype_remembered = value
        self._update("multitype_remembered", value)

    @property
    def multitype_choice(self) -> MultiType:
        '''
        /playwith command related

        Mark multitype link choice, returns MultiType

        This should be None if multitype_remembered is false
        '''
        if self._multitype_choice is None:
            value = self._fetch('multitype_choice')
            match value:
                case MultiType.VideoOnly:
                    self._multitype_choice = MultiType.VideoOnly
                case MultiType.Playlist:
                    self._multitype_choice = MultiType.Playlist
        
        return self._multitype_choice

    @multitype_choice.setter
    def multitype_choice(self, value: MultiType):
        self._multitype_choice = value
        self._update("multitype_choice", value.value)

    @property
    def language(self) -> Language:
        if self._language is None:
            value = self._fetch('language')
            match value:
                case Language.zh_tw:
                    self._language = Language.zh_tw
                case Language.en_us:
                    self._language = Language.en_us
        
        return self._language

    @language.setter
    def language(self, value: Language):
        self._language = value
        self._update("language", value.value)

    def _fetch(self, key: str) -> not None:
        '''fetch from database'''
        with open(fr"{os.getcwd()}/Storage/Json/data.json", 'r') as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None or data[str(self.guild_id)].get(key) is None:
            return data['default'][key]
        return data[str(self.guild_id)][key]

    def _update(self, key: str, value: str) -> None:
        '''update database'''

        with open(fr"{os.getcwd()}/Storage/Json/data.json", 'r') as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None:
            data[str(self.guild_id)] = dict()
        data[str(self.guild_id)][key] = value
        with open(fr"{os.getcwd()}/Storage/Json/data.json", 'w') as f:
            json.dump(data, f)

class GuildInfo:
    def __init__(self):
        self._guilds_info: dict[int, GuildInfo_Storage] = {}

    def __getitem__(self, guild_id) -> GuildInfo_Storage:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = GuildInfo(guild_id)
        return self._guilds_info[guild_id] 
    
    def delete(self, guild_id):
        if self._guilds_info.get(guild_id) is not None:
            self._guilds_info.pop(guild_id, None)

guild_player_info = GuildInfo()
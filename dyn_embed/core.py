import sys
sys.path.append("..")
from utils.playlist import LoopState
from enum import Enum, auto
import discord
from typing import *
import datetime
import os
from utils.playlist_helper import get_current_track, get_loop_state, get_playlist
from .icons import bot_icon_url, bot_xmasicon_url
from .currentactivity.playinfo_gen import playinfo_generate
import asyncio
from .misc import embed_opt

class HolidayType(Enum):
    XMASEVE = auto()
    XMAS = auto()
    NEWYEAREVE = auto()
    NEWYEAR = auto()
    LUNARNEWYEAR = auto()
    NONE = auto()

class DynEmbedOperation(Enum):
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    PLAY = auto()
    PAUSE = auto()
    STOP = auto()
    SKIP = auto()
    ADDTOQUEUE = auto()
    REMOVEFROMQUEUE = auto()

class DEColourState(Enum):
    DEFAULT = auto()
    ERROR = auto()
    SUCCESS = auto()

class DEActivityState(Enum):
    IDLE = auto()
    PLAYING = auto()
    INOPERATION = auto()

class DERenderer():
    def __init__(self):
        self.ActivityStatusColour: discord.Colour = discord.Colour.from_rgb(255, 255, 255)
        self.ActivityStatus: Optional[str] = "目前無其他動作"
        self.ActivityIcon: Union[str, discord.PartialEmoji] = None
        self.CurrentActivity: DEActivityState = DEActivityState.IDLE
        self.PageIndicator: Optional[str] = None
        self.WarningText: Optional[str] = None

        self.message: dict[discord.InteractionMessage] = {}

    def _isitholiday(self) -> HolidayType:
        holiday = HolidayType.NONE
        month = datetime.datetime.now().month
        day = datetime.datetime.now().day
        if month == 12 and day == 24:
            holiday = HolidayType.XMASEVE
        elif month == 12 and day == 25:
            holiday = HolidayType.XMAS
        elif month == 12 and day == 31:
            holiday = HolidayType.NEWYEAREVE
        elif month == 1 and day == 1:
            holiday = HolidayType.NEWYEAR
        elif (month >= 1 and month < 2 and day >= 21) or (month <= 2 and month > 1 and day <= 20):
            holiday = HolidayType.LUNARNEWYEAR
        
        return holiday

    def _act_additional_msg(self, guild_id):
        playlist = get_playlist(guild_id)

        # Stream Indicator
        if playlist.current().is_stream():
            self.WarningText += " 🔴 此為直播"

        # Loop Icon
        match get_loop_state(guild_id):
            case LoopState.SINGLE:
                self.WarningText += f' | 🔂ₛ 🕗 {playlist.times} 次'
            case LoopState.SINGLEINF:
                self.WarningText += ' | 🔂ₛ'
            case LoopState.PLAYLIST:
                self.WarningText += ' | 🔁'

        # Holiday text
        match self._isitholiday():
            case HolidayType.XMASEVE:
                self.ActivityStatus += " | 🎄 今日聖誕夜"
            case HolidayType.XMAS:
                self.ActivityStatus += " | 🎄 聖誕節快樂！"
            case HolidayType.NEWYEAREVE:
                self.ActivityStatus += " | 🎊 明天就是{}了！".format(datetime.datetime.now().year + 1)
            case HolidayType.NEWYEAR:
                self.ActivityStatus += " | 🎊 {}新年快樂！".format(datetime.datetime.now().year)
            case HolidayType.LUNARNEWYEAR:
                self.ActivityStatus += " | 🧧 過年啦！你是發紅包還是收紅包呢？"
        

    def _generate_currentact(self, guild_id) -> discord.Embed:
        match self.CurrentActivity:
            case DEActivityState.IDLE:
                title = "輸入 /play 來開始播放歌曲"
                embed = discord.Embed(title=title, colour=self.ActivityStatusColour)
            case DEActivityState.PLAYING:
                currentsong = get_current_track(guild_id)
                title = currentsong.title
                embed = playinfo_generate(guild_id, discord.Embed(title=title, colour=self.ActivityStatusColour))
        return embed
                

    def _update_act_text(self, guild_id=None):
        match self.CurrentActivity:
            case DEActivityState.IDLE:
                self.ActivityStatus = "目前無其他動作"
                self.ActivityIcon = bot_icon_url
                self.PageIndicator = ""
                self.WarningText = ""

            case DEActivityState.PLAYING:
                currentsong = get_current_track(guild_id)
                holiday = self._isitholiday()
                self.ActivityStatus = f"此歌曲由 {currentsong.requester.name}#{currentsong.requester.discriminator} 點播"
                if currentsong.suggested:
                    self.ActivityStatus = "這首歌為 自動推薦歌曲"
                    if holiday == HolidayType.XMAS or holiday == HolidayType.XMASEVE:
                        self.ActivityIcon = bot_xmasicon_url
                    else:
                        self.ActivityIcon = bot_icon_url
                else:
                    self.ActivityStatus = f"此歌曲由 {currentsong.requester.name}#{currentsong.requester.discriminator} 點播"
                    self.ActivityIcon = currentsong.requester.display_avatar
                self._act_additional_msg(guild_id)
    
    async def init_msg(self, interaction: discord.Interaction):
        if self.message.get(interaction.guild.id) is None:
            self._update_act_text(interaction.guild.id)
            embed = self._generate_currentact(interaction.guild.id)
            embed.set_author(name=self.ActivityStatus, icon_url=self.ActivityIcon)
            embed.set_footer(text=f"{self.PageIndicator}\n{self.WarningText}\n{embed_opt['copyright_text']}", icon_url=embed_opt['icon_url'])
            await interaction.send(embed=embed)
            self.message[interaction.guild.id] = await interaction.original_response()

    async def update(self, guild_id):
        self._update_act_text(guild_id)
        embed = self._generate_currentact(guild_id)
        embed.set_author(name=self.ActivityStatus, icon_url=self.ActivityIcon)
        embed.set_footer(text=f"{self.PageIndicator}\n{self.WarningText}\n{embed_opt['copyright_text']}", icon_url=embed_opt['icon_url'])
        await self.message[guild_id].edit(embed=embed)

        

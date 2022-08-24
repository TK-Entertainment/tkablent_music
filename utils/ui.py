from typing import *
import discord
from discord.ext import commands
import datetime

# Just for fetching current year
cdt = datetime.datetime.now().date()
year = cdt.strftime("%Y")

from .player import MusicCog

bot_version: str = None
musicbot: MusicCog = None
bot: commands.Bot = None
embed_opt = None

from .func.base import UIBase

class UI(UIBase):
    # _guild_ui_info: dict
    # def __getitem__(self, guild_id) -> GuildUIInfo:
    #     if self._guild_ui_info.get(guild_id) is None:
    #         self._guild_ui_info[guild_id] = GuildUIInfo(guild_id)
    #     return _guild_ui_info[guild_id]

    def __init__(self, music_bot, botversion):
        super().__init__(music_bot)
        self._guild_ui_info = dict()

        global bot_version, musicbot, bot, embed_opt
        bot_version = botversion

        musicbot = music_bot
        bot = musicbot.bot
        from .func.misc import _generate_embed_option
        embed_opt = _generate_embed_option(bot, bot_version)

        ########
        # Info #
        ########
        from .func.info import InfoGenerator
        self._InfoGenerator = InfoGenerator(musicbot, embed_opt)

        ############################
        # General Warning Messages #
        ############################
        from .func.exception_handler import ExceptionHandler
        self.ExceptionHandler = ExceptionHandler(musicbot=musicbot, embed_opt=embed_opt)

        ########
        # Help #
        ########
        from .func.help import Help
        self.Help = Help(bot, embed_opt)

        ########
        # Join #
        ########
        from .func.join import Join
        self.Join = Join(musicbot=musicbot, embed_opt=embed_opt)
    
        #########
        # Stage #
        #########
        from .func.stage import Stage
        self.Stage = Stage(musicbot=musicbot, embed_opt=embed_opt)

        #########
        # Leave #
        #########
        from .func.leave import Leave
        self.Leave = Leave(musicbot=musicbot, embed_opt=embed_opt)
    
        ##########
        # Search #
        ##########
        from .func.search import Search
        self.Search = Search(musicbot=musicbot, embed_opt=embed_opt)

        #########
        # Queue #
        #########
        from .func.queue import Queue
        self.Queue = Queue(musicbot, embed_opt)

        from .func.queue_control import QueueControl
        self.QueueControl = QueueControl(musicbot=musicbot, embed_opt=embed_opt)

        ########
        # Play #
        ########
        #########
        # Pause #
        ######### 
        ##########
        # Resume #
        ##########
        ########
        # Skip #
        ########
        ########
        # Stop #
        ########
        ########
        # Seek #
        ########
        ##########
        # Replay #
        ##########
        ########
        # Loop #
        ########
        from .func.player_control import PlayerControl
        self.PlayerControl = PlayerControl(musicbot=musicbot, embed_opt=embed_opt)

        ##########
        # Volume # Deprecated for now (might be used in the future)
        ##########
        # async def VolumeAdjust(self, command: Command, percent: Union[float, str]):
        #     if percent == 0:
        #         return
        #     # If percent = None, show current volume
        #     if percent == None: 
        #         await command.send(f'''
        #         **:loud_sound: | 音量調整**
        #         目前音量為 {self.musicbot[command.guild.id].volume_level}%
        #     ''')

        #     # Volume unchanged
        #     if (percent) == self.musicbot[command.guild.id].volume_level:
        #         await command.send(f'''
        #         **:loud_sound: | 音量調整**
        #         音量沒有變更，仍為 {percent}%
        #     ''')

        #     # Volume up
        #     elif (percent) > self.musicbot[command.guild.id].volume_level:
        #         await command.send(f'''
        #         **:loud_sound: | 調高音量**
        #         音量已設定為 {percent}%
        #     ''')
        #         self[command.guild.id].mute = False
        #     # Volume down
        #     elif (percent) < self.musicbot[command.guild.id].volume_level:
        #         await command.send(f'''
        #         **:sound: | 降低音量**
        #         音量已設定為 {percent}%
        #     ''')
        #         self[command.guild.id].mute = False

        #     if self[command.guild.id].playinfo is not None:
        #         await self._UpdateSongInfo(command.guild.id)
        
        # async def Mute(self, command: Command, percent: Union[float, str]) -> bool:
        #     mute = self[command.guild.id].mute
        #     if mute and percent != 0:
        #         await command.send(f'''
        #         **:speaker: | 解除靜音**
        #         音量已設定為 {percent}%，目前已解除靜音模式
        #     ''')
        #     elif percent == 0: 
        #         await command.send(f'''
        #         **:mute: | 靜音**
        #         音量已設定為 0%，目前處於靜音模式
        #     ''')
        #     if self[command.guild.id].playinfo is not None:
        #         await self._UpdateSongInfo(command.guild.id)
        #     self[command.guild.id].mute = percent == 0

        # async def VolumeAdjustFailed(self, command: Command) -> None:
        #     await self._CommonExceptionHandler(command, "VOLUMEADJUSTFAIL")
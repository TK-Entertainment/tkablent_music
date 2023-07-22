from typing import *
import discord
from discord.ext import commands
import datetime
from enum import Enum, auto

# Just for fetching current year
cdt = datetime.datetime.now().date()
year = cdt.strftime("%Y")



from .player import MusicCog

bot_version: str = None
musicbot: MusicCog = None
bot: commands.Bot = None
embed_opt = None
_guild_ui_info = dict()




class UI:
    def __init__(self, music_bot, botversion):
        global bot_version, musicbot, bot, embed_opt, groupbutton
        bot_version = botversion

        musicbot = music_bot
        bot = musicbot.bot

        groupbutton = GroupButton()

        embed_opt = {
            'footer': {
                'text': f"{bot.user.name} | 版本: {bot_version}\nCopyright @ {year} TK Entertainment",
                'icon_url': "https://i.imgur.com/wApgX8J.png"
            },
        }

        ########
        # Info #
        ########
        from .func.info import InfoGenerator
        self._InfoGenerator = InfoGenerator()

        ############################
        # General Warning Messages #
        ############################
        from .func.exception_handler import ExceptionHandler
        self.ExceptionHandler = ExceptionHandler(self._InfoGenerator)

        ########
        # Help #
        ########
        from .func.help import Help
        self.Help = Help()

        ########
        # Join #
        ########
        from .func.join import Join
        self.Join = Join(self.ExceptionHandler)
    
        #########
        # Stage #
        #########
        from .func.stage import Stage
        self.Stage = Stage()

        #########
        # Leave #
        #########
        from .func.leave import Leave
        self.Leave = Leave(self.ExceptionHandler, self._InfoGenerator)
    
        ##########
        # Search #
        ##########
        from .func.search import Search
        self.Search = Search(self.ExceptionHandler)

        #########
        # Queue #
        #########
        from .func.queue import Queue
        self.Queue = Queue(self._InfoGenerator)

        from .func.queue_control import QueueControl
        self.QueueControl = QueueControl(self.ExceptionHandler, self._InfoGenerator)

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
        self.PlayerControl = PlayerControl(self.ExceptionHandler, self._InfoGenerator, self.Stage, self.Queue, self.Leave)

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
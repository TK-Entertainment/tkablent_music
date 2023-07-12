from typing import *
import discord
from discord.ext import commands
import datetime

# Just for fetching current year
cdt = datetime.datetime.now().date()
year = cdt.strftime("%Y")

def _sec_to_hms(seconds, format) -> str:
    sec = int(seconds%60); min = int(seconds//60%60); hr = int(seconds//60//60%24); day = int(seconds//86400)
    if format == "symbol":
        if day != 0:
            return "{}{}:{}{}:{}{}:{}{}".format("0" if day < 10 else "", day, "0" if hr < 10 else "", hr, "0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
        if hr != 0:
            return "{}{}:{}{}:{}{}".format("0" if hr < 10 else "", hr, "0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
        else:
            return "{}{}:{}{}".format("0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
    elif format == "zh":
        if day != 0:
            return f"{day} 天 {hr} 小時 {min} 分 {sec} 秒"
        elif hr != 0: 
            return f"{hr} 小時 {min} 分 {sec} 秒"
        elif min != 0:
            return f"{min} 分 {sec} 秒"
        elif sec != 0:
            return f"{sec} 秒"

from .player import MusicCog

class GuildUIInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.auto_stage_available: bool = True
        self.stage_topic_exist: bool = False
        self.stage_topic_checked: bool = False
        self.skip: bool = False
        self.lastskip: bool = False
        self.mute: bool = False
        self.search: bool = False
        self.lasterrorinfo: dict = {}
        self.playinfo: Coroutine[Any, Any, discord.Message] = None
        self.playinfo_view: discord.ui.View = None
        self.processing_msg: discord.Message = None
        self.music_suggestion: bool = False
        self.suggestions_source = None
        self.searchmsg: Coroutine[Any, Any, discord.Message] = None
        self.previous_titles: list[str] = []
        self.suggestions: list = []

bot_version: str = None
musicbot: MusicCog = None
bot: commands.Bot = None
embed_opt = None
_guild_ui_info = dict()

firstpage_emoji = discord.PartialEmoji.from_str('⏪')
prevpage_emoji = discord.PartialEmoji.from_str('⬅️')
nextpage_emoji = discord.PartialEmoji.from_str('➡️')
skip_emoji = lastpage_emoji = discord.PartialEmoji.from_str('⏩')
pause_emoji = discord.PartialEmoji.from_str('⏸️')
play_emoji = discord.PartialEmoji.from_str('▶️')
stop_emoji = discord.PartialEmoji.from_str('⏹️')
skip_emoji = discord.PartialEmoji.from_str('⏩')
repeat_emoji = discord.PartialEmoji.from_str('🔁')
repeat_sing_emoji = discord.PartialEmoji.from_str('🔂')
shuffle_emoji = discord.PartialEmoji.from_str('🔀')
bulb_emoji = discord.PartialEmoji.from_str('💡')
queue_emoji = discord.PartialEmoji.from_str('🗒️')
leave_emoji = discord.PartialEmoji.from_str("📤")
search_emoji = discord.PartialEmoji.from_str("🔎")
end_emoji = discord.PartialEmoji.from_str('❎')
done_emoji = discord.PartialEmoji.from_str('✅')
loading_emoji = discord.PartialEmoji.from_str('<a:loading:696701361504387212>')
caution_emoji = discord.PartialEmoji.from_str('⚠️')
youtube_emoji = discord.PartialEmoji.from_str('<:youtube:1010812724009242745>')
soundcloud_emoji = discord.PartialEmoji.from_str('<:soundcloud:1010812662155837511>')
spotify_emoji = discord.PartialEmoji.from_str('<:spotify:1010844746647883828>')
rescue_emoji = discord.PartialEmoji.from_str('🛟')

@staticmethod
def guild_info(guild_id) -> GuildUIInfo:
    if _guild_ui_info.get(guild_id) is None:
        _guild_ui_info[guild_id] = GuildUIInfo(guild_id)
    return _guild_ui_info[guild_id]

def auto_stage_available(guild_id: int):
    return guild_info(guild_id).auto_stage_available

class GroupButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        Button = discord.ui.Button(emoji=rescue_emoji, style=discord.ButtonStyle.link, url="https://discord.gg/9qrpGh4e7V", label="支援群組")
        self.add_item(Button)

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
        self.Leave = Leave(self.ExceptionHandler)
    
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
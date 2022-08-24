from typing import *
from discord.ext import commands

from ..player import Command
from .exception_handler import ExceptionHandler

class Leave(ExceptionHandler): # inherit ExceptionHandler and UIBase
    def reset_value(self, guild):
        guild_info = self[guild.id]

        guild_info.auto_stage_available = True
        guild_info.stage_topic_checked = False
        guild_info.stage_topic_exist = False
        guild_info.skip = False
        guild_info.music_suggestion = False

    async def LeaveSucceed(self, command: Command) -> None:
        self.reset_value(command.guild)
        await command.send(f'''
            **:outbox_tray: | 已離開語音/舞台頻道**
            已停止所有音樂並離開目前所在的語音/舞台頻道
            ''')
    
    async def LeaveOnTimeout(self, ctx: commands.Context) -> None:
        await ctx.send(f'''
            **:outbox_tray: | 等待超時**
            機器人已閒置超過 10 分鐘
            已停止所有音樂並離開目前所在的語音/舞台頻道
            ''')
    
    async def LeaveFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "LEAVEFAIL", exception)
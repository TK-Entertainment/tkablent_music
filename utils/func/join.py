from typing import *
import discord

from ..player import Command
from .exception_handler import ExceptionHandler

class Join:
    def __init__(self, exception_handler):
        from ..ui import guild_info, bot
        
        self.exception_handler: ExceptionHandler = exception_handler
        self.guild_info = guild_info
        self.bot = bot

    async def RejoinNormal(self, command: Command) -> None:
        await command.send(f'''
            **:inbox_tray: | 已更換語音頻道**
            已更換至 {command.author.voice.channel.name} 語音頻道
            ''')
    
    async def JoinNormal(self, command: Command) -> None:
        try:
            await command.send(f'''
                **:inbox_tray: | 已加入語音頻道**
                已成功加入 {command.author.voice.channel.name} 語音頻道
                    ''')
        except discord.InteractionResponded:
            channel = command.channel
            await channel.send(f'''
            **:inbox_tray: | 已加入語音頻道**
            已成功加入 {command.author.voice.channel.name} 語音頻道
                ''')

    async def JoinStage(self, command: Command, guild_id: int) -> None:
        channel = command.channel
        botitself: discord.Member = await command.guild.fetch_member(self.bot.user.id)
        if botitself not in command.author.voice.channel.moderators and self[guild_id].auto_stage_available == True:
            if not botitself.guild_permissions.manage_channels or not botitself.guild_permissions.administrator:
                try:
                    await command.send(f'''
                **:inbox_tray: | 已加入舞台頻道**
                已成功加入 {command.author.voice.channel.name} 舞台頻道
                -----------
                *已偵測到此機器人沒有* `管理頻道` *或* `管理員` *權限*
                *亦非該語音頻道之* `舞台版主`*，自動化舞台音樂播放功能將受到限制*
                *請啟用以上兩點其中一種權限(建議啟用 `舞台版主` 即可)以獲得最佳體驗*
                *此警告僅會出現一次*
                        ''')
                except discord.InteractionResponded:
                    await channel.send(f'''
                **:inbox_tray: | 已加入舞台頻道**
                已成功加入 {command.author.voice.channel.name} 舞台頻道
                -----------
                *已偵測到此機器人沒有* `管理頻道` *或* `管理員` *權限*
                *亦非該語音頻道之* `舞台版主`*，自動化舞台音樂播放功能將受到限制*
                *請啟用以上兩點其中一種權限(建議啟用 `舞台版主` 即可)以獲得最佳體驗*
                *此警告僅會出現一次*
                        ''')
                self.guild_info(guild_id).auto_stage_available = False
                return
            else:
                self.guild_info(guild_id).auto_stage_available = True
                try:
                    await command.send(f'''
                **:inbox_tray: | 已加入舞台頻道**
                已成功加入 {command.author.voice.channel.name} 舞台頻道
                    ''')
                except discord.InteractionResponded:
                    await channel.send(f'''
                **:inbox_tray: | 已加入舞台頻道**
                已成功加入 {command.author.voice.channel.name} 舞台頻道
                    ''')
                return
        else:
            try:
                await command.send(f'''
                **:inbox_tray: | 已加入舞台頻道**
                已成功加入 {command.author.voice.channel.name} 舞台頻道
                    ''')
            except discord.InteractionResponded:
                await channel.send(f'''
                **:inbox_tray: | 已加入舞台頻道**
                已成功加入 {command.author.voice.channel.name} 舞台頻道
                    ''')
            self.guild_info(guild_id).auto_stage_available = True
            return
    
    async def JoinAlready(self, command: Command) -> None:
        await command.send(f'''
            **:hushed: | 我已經加入頻道囉**
            不需要再把我加入同一個頻道囉
            *若要更換頻道
            輸入 **{self.bot.command_prefix}leave** 以離開原有頻道
            然後使用 **{self.bot.command_prefix}join 加入新的頻道***
                ''')
        return
    
    async def JoinFailed(self, command: Command, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(command, "JOINFAIL", exception)
        return
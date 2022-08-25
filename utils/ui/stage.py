from typing import *
import discord
from discord.ext import commands

from ..command import Command
from .exception_handler import ExceptionHandler

class Stage(ExceptionHandler): # inherit ExceptionHandler and UIBase
    async def CreateStageInstance(self, command: Command, guild_id: int) -> None:
        if isinstance(command.author.voice.channel.instance, discord.StageInstance) or self[guild_id].auto_stage_available == False:
            return
        channel: discord.StageChannel = command.author.voice.channel
        await channel.create_instance(topic='🕓 目前無歌曲播放 | 等待指令')
    
    async def EndStage(self, guild_id: int) -> None:
        if not self[guild_id].auto_stage_available: 
            return
        if not isinstance(self.bot.get_guild(guild_id).voice_client.channel.instance, discord.StageInstance):
            return
        channel: discord.StageChannel = self.bot.get_guild(guild_id).voice_client.channel
        instance: discord.StageInstance = channel.instance
        await instance.delete()
    
    async def _UpdateStageTopic(self, guild_id: int, mode: str='update') -> None:
        playlist = self.musicbot._playlist[guild_id]
        if self[guild_id].auto_stage_available == False \
                or isinstance(self.bot.get_guild(guild_id).voice_client.channel, discord.VoiceChannel):
            return
        instance: discord.StageInstance = self.bot.get_guild(guild_id).voice_client.channel.instance
        if (instance.topic != '🕓 目前無歌曲播放 | 等待指令') \
            and self[guild_id].stage_topic_exist == False \
            and self[guild_id].stage_topic_checked == False:
            self[guild_id].stage_topic_exist = True
        if self[guild_id].stage_topic_checked == False:
            self[guild_id].stage_topic_checked = True
        if not self[guild_id].stage_topic_exist:
            if mode == "done":
                await instance.edit(topic='🕓 目前無歌曲播放 | 等待指令')
            else:
                await instance.edit(topic='{}{} {}{}'.format(
                    "⏸️" if mode == "pause" else "▶️",
                    "|🔴" if playlist[0].is_stream() else "",
                    playlist[0].title[:40] if len(playlist[0].title) >= 40 else playlist[0].title,
                    "..." if len(playlist[0].title) >= 40 else ""))
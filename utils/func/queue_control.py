from typing import *
import discord

from ..player import Command
from .exception_handler import ExceptionHandler
from .info import InfoGenerator

class QueueControl(ExceptionHandler): # inherit InfoGenerator and ExceptionHandler and UIBase
    # Remove an entity from queue
    async def RemoveSucceed(self, command: Command, idx: int) -> None:
        await command.send(f'''
            **:wastebasket: | 已刪除指定歌曲**
            已刪除 **第 {idx} 順位** 的歌曲，詳細資料如下
            ''', embed=self._SongInfo(command.guild.id, 'red', idx))
    
    async def RemoveFailed(self, command: Command, exception):
        await self._CommonExceptionHandler(command, "REMOVEFAIL", exception)
    
    # Swap entities in queue
    async def Embed_SwapSucceed(self, command: Command, idx1: int, idx2: int) -> None:
        playlist = self.musicbot._playlist[command.guild.id]
        embed = discord.Embed(title=":arrows_counterclockwise: | 調換歌曲順序", description="已調換歌曲順序，以下為詳細資料", colour=0xF2F3EE)
        
        embed.add_field(name=f"第 ~~{idx2}~~ -> **{idx1}** 順序", value='{}\n{}\n{} 點歌\n'
            .format(
                playlist[idx1].info['title'],
                playlist[idx1].info['author'],
                playlist[idx1].requester
            ), inline=True)
        
        embed.add_field(name=f"第 ~~{idx1}~~ -> **{idx2}** 順序", value='{}\n{}\n{} 點歌\n'
            .format(
                playlist[idx2].info['title'],
                playlist[idx2].info['author'],
                playlist[idx2].requester
            ), inline=True)

        await command.send(embed=embed)

    async def SwapFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "SWAPFAIL", exception)
    
    # Move entity to other place in queue
    async def MoveToSucceed(self, command: Command, origin: int, new: int) -> None:
        playlist = self.musicbot._playlist[command.guild.id]
        embed = discord.Embed(title=":arrows_counterclockwise: | 移動歌曲順序", description="已移動歌曲順序，以下為詳細資料", colour=0xF2F3EE)
        
        embed.add_field(name=f"第 ~~{origin}~~ -> **{new}** 順序", value='{}\n{}\n{} 點歌\n'
            .format(
                playlist[new].info['title'],
                playlist[new].info['author'],
                playlist[new].requester
            ), inline=True)
        
        await command.send(embed=embed)

    async def MoveToFailed(self, command: Command, exception) -> None:
        await self._CommonExceptionHandler(command, "MOVEFAIL", exception)
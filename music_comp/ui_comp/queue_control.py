from typing import *
import discord

from .exception_handler import ExceptionHandler
from .info import InfoGenerator


class QueueControl:
    def __init__(self, exception_handler, info_generator):
        from ..ui import musicbot

        self.musicbot = musicbot
        self.exception_handler: ExceptionHandler = exception_handler
        self.info_generator: InfoGenerator = info_generator

    # Remove an entity from queue
    async def RemoveSucceed(
        self, interaction: discord.Interaction, removed, idx
    ) -> None:
        await interaction.response.send_message(
            f"""
            **:wastebasket: | 已刪除指定歌曲**
            已刪除 **第 {idx} 順位** 的歌曲，詳細資料如下
            """,
            embed=self.info_generator._SongInfo(
                interaction.guild.id, "red", removed=removed
            ),
        )
        if len(self.musicbot._playlist[interaction.guild.id].order) == 1:
            await self.musicbot._playlist.process_suggestion(
                interaction.guild, self.musicbot.ui_guild_info(interaction.guild.id)
            )
        try:
            await self.info_generator._UpdateSongInfo(interaction.guild.id)
        except:
            pass

    async def RemoveFailed(self, interaction: discord.Interaction, exception):
        await self.exception_handler._CommonExceptionHandler(
            interaction, "REMOVEFAIL", exception
        )

    # Swap entities in queue
    async def Embed_SwapSucceed(
        self, interaction: discord.Interaction, idx1: int, idx2: int
    ) -> None:
        playlist = self.musicbot._playlist[interaction.guild.id]
        embed = discord.Embed(
            title=":arrows_counterclockwise: | 調換歌曲順序",
            description="已調換歌曲順序，以下為詳細資料",
            colour=0xF2F3EE,
        )

        embed.add_field(
            name=f"第 ~~{idx2}~~ -> **{idx1}** 順序",
            value="{}\n{}\n{} 點歌\n".format(
                playlist[idx1].title, playlist[idx1].author, playlist[idx1].requester
            ),
            inline=True,
        )

        embed.add_field(
            name=f"第 ~~{idx1}~~ -> **{idx2}** 順序",
            value="{}\n{}\n{} 點歌\n".format(
                playlist[idx2].title, playlist[idx2].author, playlist[idx2].requester
            ),
            inline=True,
        )

        await interaction.response.send_message(embed=embed)

    async def SwapFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(
            interaction, "SWAPFAIL", exception
        )

    # Move entity to other place in queue
    async def MoveToSucceed(
        self, interaction: discord.Interaction, origin: int, new: int
    ) -> None:
        playlist = self.musicbot._playlist[interaction.guild.id]
        embed = discord.Embed(
            title=":arrows_counterclockwise: | 移動歌曲順序",
            description="已移動歌曲順序，以下為詳細資料",
            colour=0xF2F3EE,
        )

        embed.add_field(
            name=f"第 ~~{origin}~~ -> **{new}** 順序",
            value="{}\n{}\n{} 點歌\n".format(
                playlist[new].title, playlist[new].author, playlist[new].requester
            ),
            inline=True,
        )

        await interaction.response.send_message(embed=embed)

    async def MoveToFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(
            interaction, "MOVEFAIL", exception
        )

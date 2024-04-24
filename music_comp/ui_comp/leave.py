from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import *
import discord
import asyncio

from .exception_handler import ExceptionHandler
from .info import InfoGenerator
from ..ui import LeaveType


class Leave:
    def __init__(self, exception_handler, info_generator):
        from ..ui import guild_info, bot, musicbot

        self.guild_info = guild_info
        self.exception_handler: ExceptionHandler = exception_handler
        self.info_generator: InfoGenerator = info_generator
        self.bot = bot
        self.musicbot = musicbot

    async def refresh_and_reset(self, guild: discord.Guild):
        await asyncio.sleep(3)
        await self.info_generator._UpdateSongInfo(guild.id)
        self.reset_value(guild)

    def reset_value(self, guild):
        guild_info = self.guild_info(guild.id)

        self.musicbot[guild.id]._timer_done = False
        guild_info.auto_stage_available = True
        guild_info.stage_topic_checked = False
        guild_info.stage_topic_exist = False
        guild_info.skip = False
        guild_info.music_suggestion = False
        guild_info.processing_msg = None
        guild_info.suggestions = []
        if self.musicbot._playlist[guild.id]._resuggest_task is not None:
            self.musicbot._playlist[guild.id]._resuggest_task.cancel()
            self.musicbot._playlist[guild.id]._resuggest_task = None
        if self.musicbot._playlist[guild.id]._suggest_search_task is not None:
            self.musicbot._playlist[guild.id]._suggest_search_task.cancel()
            self.musicbot._playlist[guild.id]._suggest_search_task = None
        guild_info.playinfo_view = None
        guild_info.playinfo = None

    async def LeaveSucceed(self, interaction: discord.Interaction) -> None:
        self.guild_info(interaction.guild.id).leaveoperation = True
        if self.guild_info(interaction.guild.id).playinfo is not None:
            try:
                self.guild_info(interaction.guild.id).playinfo_view.clear_items()
                self.guild_info(interaction.guild.id).playinfo_view.stop()
                await self.guild_info(interaction.guild.id).playinfo.edit(
                    embed=self.info_generator._SongInfo(
                        guild_id=interaction.guild.id, operation=LeaveType.ByCommand
                    ),
                    view=None,
                )
            except:
                self.guild_info(interaction.guild.id).playinfo_view = None
                self.guild_info(interaction.guild.id).playinfo = None
            await interaction.response.send_message("ㅤ", ephemeral=True)
        else:
            await interaction.response.send_message(
                embed=self.info_generator._SongInfo(
                    guild_id=interaction.guild.id, operation=LeaveType.ByCommand
                )
            )
        self.bot.loop.create_task(self.refresh_and_reset(interaction.guild))

    async def LeaveOnTimeout(self, channel: discord.TextChannel) -> None:
        self.guild_info(channel.guild.id).leaveoperation = True
        if self.guild_info(channel.guild.id).playinfo is not None:
            try:
                self.guild_info(channel.guild.id).playinfo_view.clear_items()
                self.guild_info(channel.guild.id).playinfo_view.stop()
                await self.guild_info(channel.guild.id).playinfo.edit(
                    embed=self.info_generator._SongInfo(
                        guild_id=channel.guild.id, operation=LeaveType.ByTimeout
                    ),
                    view=None,
                )
            except:
                self.guild_info(channel.guild.id).playinfo_view = None
                self.guild_info(channel.guild.id).playinfo = None
        else:
            await channel.send(
                embed=self.info_generator._SongInfo(
                    guild_id=channel.guild.id, operation=LeaveType.ByTimeout
                )
            )
        self.bot.loop.create_task(self.refresh_and_reset(channel.guild))

    async def LeaveFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(
            interaction, "LEAVEFAIL", exception
        )

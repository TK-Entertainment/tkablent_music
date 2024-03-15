from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import *
import discord

from .exception_handler import ExceptionHandler


class Join:
    def __init__(self, exception_handler):
        from ..ui import guild_info, bot

        self.exception_handler: ExceptionHandler = exception_handler
        self.guild_info = guild_info
        self.bot = bot

    async def RejoinNormal(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"""
            **:inbox_tray: | 已更換語音頻道**
            已更換至 {interaction.user.voice.channel.name} 語音頻道
            """
        )
        self.guild_info(interaction.guild.id).playinfo_view.playorpause.disabled = False
        self.guild_info(
            interaction.guild.id
        ).playinfo_view.playorpause.style = discord.ButtonStyle.blurple
        await self.guild_info(interaction.guild.id).playinfo.edit(
            view=self.guild_info(interaction.guild.id).playinfo_view
        )

    async def JoinNormal(self, interaction: discord.Interaction) -> None:
        msg = f"""
            **:inbox_tray: | 已加入語音頻道**
            已成功加入 {interaction.user.voice.channel.name} 語音頻道"""
        if self.guild_info(interaction.guild.id).searchmsg is not None:
            await self.guild_info(interaction.guild.id).searchmsg.edit(content=msg)
            self.guild_info(interaction.guild.id).searchmsg = None
        else:
            try:
                await interaction.response.send_message(msg)
            except discord.InteractionResponded:
                await interaction.followup.send(content=msg)

    async def JoinStage(self, interaction: discord.Interaction, guild_id: int) -> None:
        channel = interaction.channel
        botitself: discord.Member = await interaction.guild.fetch_member(
            self.bot.user.id
        )
        errormsg = f"""
                **:inbox_tray: | 已加入舞台頻道**
                已成功加入 {interaction.user.voice.channel.name} 舞台頻道
                -----------
                *已偵測到此機器人沒有* `管理頻道` *或* `管理員` *權限*
                *亦非該語音頻道之* `舞台版主`*，自動化舞台音樂播放功能將受到限制*
                *請啟用以上兩點其中一種權限(建議啟用 `舞台版主` 即可)以獲得最佳體驗*
                *此警告僅會出現一次*
                        """
        msg = f"""
                **:inbox_tray: | 已加入舞台頻道**
                已成功加入 {interaction.user.voice.channel.name} 舞台頻道
                    """
        if (
            botitself not in interaction.user.voice.channel.moderators
            and self.guild_info(guild_id).auto_stage_available == True
        ):
            if (
                not botitself.guild_permissions.manage_channels
                or not botitself.guild_permissions.administrator
            ):
                self.guild_info(guild_id).auto_stage_available = False
                final_msg = errormsg
            else:
                self.guild_info(guild_id).auto_stage_available = True
                final_msg = msg
        else:
            self.guild_info(guild_id).auto_stage_available = True
            final_msg = msg
        try:
            if self.guild_info(interaction.guild.id).processing_msg is not None:
                await self.guild_info(interaction.guild.id).processing_msg.delete()
                self.guild_info(interaction.guild.id).processing_msg = None
            await interaction.response.send_message(final_msg)
        except discord.InteractionResponded:
            await channel.send(final_msg)
        return

    async def JoinAlready(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"""
            **:hushed: | 我已經加入頻道囉**
            不需要再把我加入同一個頻道囉
            *若要更換頻道
            輸入 **{self.bot.command_prefix}leave** 以離開原有頻道
            然後使用 **{self.bot.command_prefix}join 加入新的頻道***
                """,
            ephemeral=True,
        )
        return

    async def JoinFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(
            interaction, "JOINFAIL", exception
        )
        return

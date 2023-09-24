import discord
import wavelink
import asyncio

from UI.Generic.Emojis import Emoji
from UI.Generic.Enums import LeaveType
from UI.InfoGenerator.SongInfoEmbed import SongInfo

from Storage.GuildUIInfo import guild_ui_info
from Storage.GuildPlayInfo import guild_play_info
from Storage.GuildPlayerInfo import guild_player_info
from Storage.PlaylistStorage import playlist_storage

from Misc.Enums import LoopState

class UICore:
    def __init__(self, bot):
        self.Info = InfoCommand()
        self.Join = JoinCommand() 

    async def refresh_and_reset(self, guild: discord.Guild, player: wavelink.Player) -> None:
        await asyncio.sleep(3)
        await self.Info.UpdateSongInfo(guild.id, player)
        self.reset_value(guild)

    def reset_value(self, guild) -> None:
        ui_info = guild_ui_info[guild.id]
        play_info = guild_play_info[guild.id]
        player_info = guild_player_info[guild.id]

        if player_info._resuggest_task is not None:
            player_info._resuggest_task.cancel()
        if player_info._suggest_search_task is not None:
            player_info._suggest_search_task.cancel()
        player_info._timer_done = False
        player_info.music_suggestion = False
        player_info.suggestions = []
        player_info._resuggest_task = None
        player_info._suggest_search_task = None


        play_info.skip = False
        play_info.playinfo = None
        play_info.playinfo_view = None

        ui_info.auto_stage_available = True
        ui_info.stage_topic_checked = False
        ui_info.stage_topic_exist = False
        ui_info.processing_msg = None

class InfoCommand:
    async def UpdateSongInfo(self, guild_id: int, voice_client: wavelink.Player) -> None:
        playlist = playlist_storage[guild_id]
        guild_info = guild_play_info[guild_id]

        if len(playlist.order) == 0:
            await guild_info.playinfo.edit(embed=SongInfo(), view=None)
        else:
            guild_info.playinfo_view.skip.emoji = Emoji.Skip
            if len(playlist.order) == 1:
                guild_info.playinfo_view.skip.style = discord.ButtonStyle.gray
            else:
                guild_info.playinfo_view.skip.style = discord.ButtonStyle.blurple       
            guild_info.playinfo_view.skip.disabled = (len(playlist.order) == 1)

            if playlist.loop_state == LoopState.SINGLE:
                guild_info.playinfo_view.loop_control.label = f"ₛ {playlist.times} 次"
            elif playlist.loop_state == LoopState.NOTHING:
                guild_info.playinfo_view.loop_control.emoji = Emoji.Repeat
                guild_info.playinfo_view.loop_control.label = ''
                guild_info.playinfo_view.loop_control.style = discord.ButtonStyle.danger

            if not playlist_storage.check_current_suggest_support(guild_id):
                guild_info.playinfo_view.suggest.style = discord.ButtonStyle.gray
            else:
                if guild_info.music_suggestion:
                    self.guild_info.playinfo_view.suggest.style = discord.ButtonStyle.green
                else:
                    self.guild_info(guild_id).playinfo_view.suggest.style = discord.ButtonStyle.danger
            guild_info.playinfo_view.suggest.disabled = (not playlist_storage.check_current_suggest_support(guild_id))

            await self.guild_info(guild_id).playinfo.edit(embed=self._SongInfo(guild_id), view=self.guild_info(guild_id).playinfo_view)

class JoinCommand:
    async def RejoinNormal(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f'''
            **:inbox_tray: | 已更換語音頻道**
            已更換至 {interaction.user.voice.channel.name} 語音頻道
            ''')
        self.guild_info(interaction.guild.id).playinfo_view.playorpause.disabled = False
        self.guild_info(interaction.guild.id).playinfo_view.playorpause.style = discord.ButtonStyle.blurple
        await self.guild_info(interaction.guild.id).playinfo.edit(view=self.guild_info(interaction.guild.id).playinfo_view)
    
    async def JoinNormal(self, interaction: discord.Interaction) -> None:
        msg = f'''
            **:inbox_tray: | 已加入語音頻道**
            已成功加入 {interaction.user.voice.channel.name} 語音頻道'''
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
        botitself: discord.Member = await interaction.guild.fetch_member(self.bot.user.id)
        errormsg = f'''
                **:inbox_tray: | 已加入舞台頻道**
                已成功加入 {interaction.user.voice.channel.name} 舞台頻道
                -----------
                *已偵測到此機器人沒有* `管理頻道` *或* `管理員` *權限*
                *亦非該語音頻道之* `舞台版主`*，自動化舞台音樂播放功能將受到限制*
                *請啟用以上兩點其中一種權限(建議啟用 `舞台版主` 即可)以獲得最佳體驗*
                *此警告僅會出現一次*
                        '''
        msg = f'''
                **:inbox_tray: | 已加入舞台頻道**
                已成功加入 {interaction.user.voice.channel.name} 舞台頻道
                    '''
        if botitself not in interaction.user.voice.channel.moderators and self.guild_info(guild_id).auto_stage_available == True:
            if not botitself.guild_permissions.manage_channels or not botitself.guild_permissions.administrator:
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
        await interaction.response.send_message(f'''
            **:hushed: | 我已經加入頻道囉**
            不需要再把我加入同一個頻道囉
            *若要更換頻道
            輸入 **/leave** 以離開原有頻道
            然後使用 **/join 加入新的頻道***
                ''', ephemeral=True)
        return
    
    async def JoinFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(interaction, "JOINFAIL", exception)
        return
    
class LeaveCommand:
    async def LeaveSucceed(self, interaction: discord.Interaction) -> None:
        self.guild_info(interaction.guild.id).leaveoperation = True
        if self.guild_info(interaction.guild.id).playinfo is not None:
            self.guild_info(interaction.guild.id).playinfo_view.clear_items()
            self.guild_info(interaction.guild.id).playinfo_view.stop()
            await interaction.response.send_message("ㅤ", ephemeral=True)
            await self.guild_info(interaction.guild.id).playinfo.edit(embed=self.info_generator._SongInfo(guild_id=interaction.guild.id, operation=LeaveType.ByCommand), view=None)
        else:
            await interaction.response.send_message(embed=self.info_generator._SongInfo(guild_id=interaction.guild.id, operation=LeaveType.ByCommand))
        self.bot.loop.create_task(self.refresh_and_reset(interaction.guild))

    async def LeaveOnTimeout(self, channel: discord.TextChannel) -> None:
        self.guild_info(channel.guild.id).leaveoperation = True
        if self.guild_info(channel.guild.id).playinfo is not None:
            self.guild_info(channel.guild.id).playinfo_view.clear_items()
            self.guild_info(channel.guild.id).playinfo_view.stop()
            await self.guild_info(channel.guild.id).playinfo.edit(embed=self.info_generator._SongInfo(guild_id=channel.guild.id, operation=LeaveType.ByTimeout), view=None)
        else:
            await channel.send(embed=self.info_generator._SongInfo(guild_id=channel.guild.id, operation=LeaveType.ByTimeout))
        self.bot.loop.create_task(self.refresh_and_reset(channel.guild))
    
    async def LeaveFailed(self, interaction: discord.Interaction, exception) -> None:
        await self.exception_handler._CommonExceptionHandler(interaction, "LEAVEFAIL", exception)
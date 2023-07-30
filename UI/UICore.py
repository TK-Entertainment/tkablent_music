import discord
import wavelink

from UI.Generic.Emojis import Emoji
from UI.InfoGenerator.SongInfoEmbed import SongInfo

from Storage.GuildUIInfo import guild_ui_info
from Storage.PlaylistStorage import playlist_storage

class UICore:
    async def _UpdateSongInfo(self, guild_id: int, voice_client: wavelink.Player):
        playlist = playlist_storage[guild_id]
        guild_info = guild_ui_info[guild_id]

        if len(playlist.order) == 0:
            await guild_info.playinfo.edit(embed=SongInfo(), view=None)
        else:
            self.guild_info(guild_id).playinfo_view.skip.emoji = Emoji.Skip
            if len(self.musicbot._playlist[guild_id].order) == 1:
                self.guild_info(guild_id).playinfo_view.skip.style = discord.ButtonStyle.gray
                self.guild_info(guild_id).playinfo_view.skip.disabled = True
            else:
                self.guild_info(guild_id).playinfo_view.skip.style = discord.ButtonStyle.blurple
                self.guild_info(guild_id).playinfo_view.skip.disabled = False

            if self.musicbot._playlist[guild_id].loop_state == LoopState.SINGLE:
                self.guild_info(guild_id).playinfo_view.loop_control.label = f"ₛ {self.musicbot._playlist[guild_id].times} 次"
            elif self.musicbot._playlist[guild_id].loop_state == LoopState.NOTHING:
                self.guild_info(guild_id).playinfo_view.loop_control.emoji = repeat_emoji
                self.guild_info(guild_id).playinfo_view.loop_control.label = ''
                self.guild_info(guild_id).playinfo_view.loop_control.style = discord.ButtonStyle.danger

            if not self.musicbot._playlist.check_current_suggest_support(guild_id):
                self.guild_info(guild_id).playinfo_view.suggest.style = discord.ButtonStyle.gray
                self.guild_info(guild_id).playinfo_view.suggest.disabled = True
            else:
                self.guild_info(guild_id).playinfo_view.suggest.disabled = False
                if self.guild_info(guild_id).music_suggestion:
                    self.guild_info(guild_id).playinfo_view.suggest.style = discord.ButtonStyle.green
                else:
                    self.guild_info(guild_id).playinfo_view.suggest.style = discord.ButtonStyle.danger

            await self.guild_info(guild_id).playinfo.edit(embed=self._SongInfo(guild_id), view=self.guild_info(guild_id).playinfo_view)
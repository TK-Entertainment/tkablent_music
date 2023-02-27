import discord
import asyncio
import wavelink
from ..data import guild_info, reset_value
from ..icons import skip_emoji, leave_emoji, shuffle_emoji, pause_emoji, \
    play_emoji, stop_emoji, done_emoji
from ...utils.playlist_helper import get_playlist

class PlaybackControl(discord.ui.View):

    bot = self.bot
    voice_client: wavelink.Player = channel.guild.voice_client
    musicbot = self.musicbot
    info_generator = self.info_generator
    queue = self.queue
    guild_info = guild_info

    def __init__(self, *, timeout=60, message: discord.InteractionMessage):
        super().__init__(timeout=None)
        self.message = message

    async def restore_skip(self, guild_id):
        await asyncio.sleep(6)
        self.skip.emoji = skip_emoji
        playlist = get_playlist(guild_id)
        if len(playlist[self.message.channel.guild.id].order) != 1:
            self.skip.disabled = False
            self.skip.style = discord.ButtonStyle.blurple
        await self.message.edit(view=self)

    async def restore_shuffle(self):
        await asyncio.sleep(3)
        self.shuffle.emoji = shuffle_emoji
        self.shuffle.disabled = False
        self.shuffle.style = discord.ButtonStyle.blurple
        await self.guild_info(channel.guild.id).playinfo.edit(view=view)

    async def suggestion_control(self, interaction, button):
        if self.guild_info(channel.guild.id).music_suggestion:
            button.label = '⬜ 推薦音樂'
            button.style = discord.ButtonStyle.danger
            print(f'[Suggestion] {channel.guild.id} disabled auto suggestion')
            self.guild_info(channel.guild.id).music_suggestion = False
            if len(self.musicbot._playlist[channel.guild.id].order) == 2 \
                and self.musicbot._playlist[channel.guild.id].order[1].suggested:
                self.musicbot._playlist[channel.guild.id].order.pop(1)
                self.guild_info(channel.guild.id).playinfo_view.skip.emoji = skip_emoji
                self.guild_info(channel.guild.id).playinfo_view.skip.style = discord.ButtonStyle.gray
                self.guild_info(channel.guild.id).playinfo_view.skip.disabled = True
        else:
            button.label = '✅ 推薦音樂'
            button.style = discord.ButtonStyle.success
            print(f'[Suggestion] {channel.guild.id} enabled auto suggestion')
            self.guild_info(channel.guild.id).music_suggestion = True
            await self.musicbot._playlist.process_suggestion(channel.guild, self.guild_info(channel.guild.id))
            if len(self.musicbot._playlist[channel.guild.id].order) == 2 \
                and self.musicbot._playlist[channel.guild.id].order[1].suggested:
                self.guild_info(channel.guild.id).playinfo_view.skip.emoji = skip_emoji
                self.guild_info(channel.guild.id).playinfo_view.skip.style = discord.ButtonStyle.blurple
                self.guild_info(channel.guild.id).playinfo_view.skip.disabled = False
        await self.info_generator._UpdateSongInfo(interaction.guild.id)
        await interaction.response.edit_message(view=view)

    @discord.ui.button(
        emoji=pause_emoji if not voice_client.is_paused() else play_emoji, 
        style=discord.ButtonStyle.blurple)
    async def playorpause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.voice_client.is_paused():
            await self.voice_client.resume()
            button.emoji = pause_emoji
        else:
            await self.voice_client.pause()
            button.emoji = play_emoji

        await self.info_generator._UpdateSongInfo(interaction.guild.id)
        await interaction.response.edit_message(view=view)

    @discord.ui.button(emoji=stop_emoji, style=discord.ButtonStyle.blurple)
    async def stop_action(self, interaction: discord.Interaction, button: discord.ui.Button):            
        await self.musicbot._stop(channel.guild)
        self.guild_info(channel.guild.id).music_suggestion = False
        await interaction.response.send_message(f'''
    **:stop_button: | 停止播放**
    歌曲已由 {interaction.user.mention} 停止播放
    *輸入 **{self.bot.command_prefix}play** 以重新開始播放*
    ''')
        self.stop()

    @discord.ui.button(
        emoji=skip_emoji, 
        style=discord.ButtonStyle.gray if len(musicbot._playlist[channel.guild.id].order) == 1 else discord.ButtonStyle.blurple,
        disabled=len(musicbot._playlist[channel.guild.id].order) == 1
        )
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.guild_info(channel.guild.id).skip = True
        await self.musicbot._skip(channel.guild)

        if len(playlist.order) > 1:
            embed = self.info_generator._SongInfo(guild_id=channel.guild.id, index=1)

            self.guild_info(channel.guild.id).playinfo_view.skip.emoji = loading_emoji
            self.guild_info(channel.guild.id).playinfo_view.skip.disabled = True
            self.guild_info(channel.guild.id).playinfo_view.skip.style = discord.ButtonStyle.gray
            self.bot.loop.create_task(self.guild_info(channel.guild.id).playinfo_view.restore_skip())
            view = self.guild_info(channel.guild.id).playinfo_view
        else:
            embed = self.info_generator._SongInfo(guild_id=channel.guild.id)
            view = None

        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(
        emoji=shuffle_emoji, 
        disabled=len(musicbot._playlist[channel.guild.id].order) < 3,
        style=discord.ButtonStyle.gray if len(musicbot._playlist[channel.guild.id].order) < 3 else discord.ButtonStyle.blurple,
        )
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):            
        self.musicbot._playlist[channel.guild.id].shuffle()
        self.shuffle.emoji = done_emoji
        self.shuffle.disabled = True
        self.shuffle.style = discord.ButtonStyle.success
        await interaction.response.edit_message(view=view)
        await self.info_generator._UpdateSongInfo(interaction.guild.id)
        self.bot.loop.create_task(self.restore_shuffle())

    @discord.ui.button(
        emoji=repeat_emoji if musicbot._playlist[channel.guild.id].loop_state == LoopState.PLAYLIST \
                        or musicbot._playlist[channel.guild.id].loop_state == LoopState.NOTHING \
                        else repeat_sing_emoji,
        label='ₛ' if musicbot._playlist[channel.guild.id].loop_state == LoopState.SINGLEINF else '',
        style=discord.ButtonStyle.danger if musicbot._playlist[channel.guild.id].loop_state == LoopState.NOTHING \
                                            else discord.ButtonStyle.success)
    async def loop_control(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.musicbot._playlist[channel.guild.id].loop_state == LoopState.NOTHING:
            self.musicbot._playlist[channel.guild.id].loop_state = LoopState.PLAYLIST
            button.emoji = repeat_emoji
            button.label = ''
            button.style = discord.ButtonStyle.success
        elif self.musicbot._playlist[channel.guild.id].loop_state == LoopState.PLAYLIST:
            self.musicbot._playlist[channel.guild.id].loop_state = LoopState.SINGLEINF
            button.emoji = repeat_sing_emoji
            button.label = 'ₛ'
            button.style = discord.ButtonStyle.success
        else:
            self.musicbot._playlist[channel.guild.id].loop_state = LoopState.NOTHING
            button.emoji = repeat_emoji
            button.label = ''
            button.style = discord.ButtonStyle.danger

        await self.musicbot._playlist.process_suggestion(channel.guild, self.guild_info(channel.guild.id))

        await self.info_generator._UpdateSongInfo(interaction.guild.id)
        await interaction.response.edit_message(view=view)

    @discord.ui.button(
        label='⬜ 推薦音樂' if not self.guild_info(channel.guild.id).music_suggestion else "✅ 推薦音樂", 
        style=discord.ButtonStyle.danger if not self.guild_info(channel.guild.id).music_suggestion \
                else discord.ButtonStyle.success,
        emoji=bulb_emoji)
    async def suggest(self, interaction: discord.Interaction, button: discord.ui.Button):            
        await self.suggestion_control(interaction, button)

    @discord.ui.button(label='搜尋/新增歌曲', emoji=search_emoji, style=discord.ButtonStyle.green)
    async def new_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(self.queue.new_song_modal_helper()(interaction.user))

    @discord.ui.button(label='列出候播清單', emoji=queue_emoji, style=discord.ButtonStyle.gray, row=2)
    async def listqueue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.queue.ShowQueue(interaction, 'button')

    @discord.ui.button(label='離開語音頻道' if isinstance(channel.guild.voice_client.channel, discord.VoiceChannel) else '離開舞台頻道',
                        emoji=leave_emoji, style=discord.ButtonStyle.gray, row=2)
    async def leavech(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.musicbot._leave(channel.guild)
        reset_value(guild_id)
        self.clear_items()
        await channel.send(f'''
    **:outbox_tray: | 已離開語音/舞台頻道**
    {interaction.user.mention} 已讓我停止所有音樂並離開目前所在的語音/舞台頻道
    ''')
        self.stop()
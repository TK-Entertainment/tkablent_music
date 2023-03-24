import sys
sys.path.append("..")

import discord
import asyncio
import wavelink
from ..data import guild_info, reset_value, DynEmbedOperation
from helpers.player_helper import get_player
from ..icons import skip_emoji, leave_emoji, shuffle_emoji, pause_emoji, \
    play_emoji, stop_emoji, done_emoji, loading_emoji, repeat_emoji, \
    repeat_sing_emoji, search_emoji, queue_emoji, bulb_emoji
from helpers.playlist_helper import get_playlist, process_suggestion
from utils.playlist import LoopState

class PlaybackControl(discord.ui.View):
    def __init__(self, *, timeout=60, message: discord.InteractionMessage):
        super().__init__(timeout=None)
        self.guild_info = guild_info
        self.message = message
        self.guild_id = message.guild.id
        self.setup_button(message.guild)
        
    def setup_button(self, guild: discord.Guild):
        vc: wavelink.Player = guild.voice_client
        playlist = get_playlist(self.guild_id)

        # Play/Pause Button
        if vc.is_paused(): # Emoji Decision
            self.playorpause.emoji = play_emoji
        else:
            self.playorpause.emoji = pause_emoji
    
        # Skip Button
        if len(playlist.order) == 1: # Color Decision
            self.skip.style = discord.ButtonStyle.gray
        else:
            self.skip.style = discord.ButtonStyle.blurple
        self.skip.disabled = len(playlist.order) == 1 # Availablility Decision

        # Shuffle Button
        if len(playlist.order) < 3: # Color Decision
            self.shuffle.style = discord.ButtonStyle.gray
        else:
            self.shuffle.style = discord.ButtonStyle.blurple
        self.shuffle.disabled = len(playlist.order) < 3 # Availablility Decision

        # Repeat Button
        if playlist.loop_state == LoopState.PLAYLIST \
            or playlist.loop_state == LoopState.NOTHING: # Emoji Decision
            self.loop_control.emoji = repeat_emoji
        else:
            self.loop_control.emoji = repeat_sing_emoji
            if playlist.loop_state == LoopState.SINGLEINF:
                self.loop_control.label = 'ₛ'
        if playlist.loop_state == LoopState.NOTHING: # Color Decision
            self.loop_control.style = discord.ButtonStyle.danger
        else:
            self.loop_control.style = discord.ButtonStyle.success

        # Suggest Trigger
        if self.guild_info(self.guild_id).music_suggestion:
            self.suggest.label = "✅ 推薦音樂"
            self.suggest.style = discord.ButtonStyle.success
        else:
            self.suggest.label = '⬜ 推薦音樂'
            self.suggest.style = discord.ButtonStyle.danger
        
        # Leave Trigger
        if isinstance(vc.channel, discord.VoiceChannel):
            self.leavech.label = '離開語音頻道'
        else:
            self.leavech.label = '離開舞台頻道'

    async def restore_skip(self):
        await asyncio.sleep(6)
        self.skip.emoji = skip_emoji
        playlist = get_playlist(self.guild_id)
        if len(playlist.order) != 1:
            self.skip.disabled = False
            self.skip.style = discord.ButtonStyle.blurple
        try:
            await self.message.edit(view=self)
        except:
            pass

    async def restore_shuffle(self):
        await asyncio.sleep(3)
        self.shuffle.emoji = shuffle_emoji
        self.shuffle.disabled = False
        self.shuffle.style = discord.ButtonStyle.blurple
        try:
            await self.message.edit(view=self)
        except:
            pass

    async def suggestion_control(self, interaction: discord.Interaction, button):
        playlist = get_playlist(self.guild_id)
        self.guild_info(self.guild_id).operation = DynEmbedOperation.UPDATE
        if self.guild_info(self.guild_id).music_suggestion:
            button.label = '⬜ 推薦音樂'
            button.style = discord.ButtonStyle.danger
            print(f'[Suggestion] {self.guild_id} disabled auto suggestion')
            self.guild_info(self.guild_id).music_suggestion = False
            if len(playlist.order) == 2 \
                and playlist.order[1].suggested:
                playlist.order.pop(1)
                self.skip.emoji = skip_emoji
                self.skip.style = discord.ButtonStyle.gray
                self.skip.disabled = True
        else:
            button.label = '✅ 推薦音樂'
            button.style = discord.ButtonStyle.success
            print(f'[Suggestion] {self.guild_id} enabled auto suggestion')
            self.guild_info(self.guild_id).music_suggestion = True
            await process_suggestion(interaction.guild, self.guild_info(self.guild_id))
            if len(playlist.order) == 2 \
                and playlist.order[1].suggested:
                self.skip.emoji = skip_emoji
                self.skip.style = discord.ButtonStyle.blurple
                self.skip.disabled = False
        await interaction.response.edit_message(view=self)

    @discord.ui.button(
        emoji=pause_emoji, 
        style=discord.ButtonStyle.blurple)
    async def playorpause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client.is_paused():
            await interaction.guild.voice_client.resume()
            self.guild_info(self.guild_id).operation = DynEmbedOperation.RESUME
            button.emoji = pause_emoji
        else:
            await interaction.guild.voice_client.pause()
            self.guild_info(self.guild_id).operation = DynEmbedOperation.PAUSE
            button.emoji = play_emoji
        await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji=stop_emoji, style=discord.ButtonStyle.blurple)
    async def stop_action(self, interaction: discord.Interaction, button: discord.ui.Button):   
        player = get_player()         
        await player._stop(interaction.guild)
        self.guild_info(self.guild_id).music_suggestion = False
        await interaction.response.edit_message(view=self)
        self.guild_info(self.guild_id).operation = DynEmbedOperation.STOP
        self.stop()

    @discord.ui.button(
        emoji=skip_emoji, 
        style=discord.ButtonStyle.gray,
        disabled=True
        )
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = get_player()
        self.guild_info(self.guild_id).operation = DynEmbedOperation.SKIP
        self.guild_info(self.guild_id).skipper = interaction.user
        await player._skip(interaction.guild)
        playlist = get_playlist(self.guild_id)

        if len(playlist.order) > 1:
            self.skip.emoji = loading_emoji
            self.skip.disabled = True
            self.skip.style = discord.ButtonStyle.gray
            player.bot.loop.create_task(self.restore_skip())
            view = self
        else:
            view = None

        await interaction.response.edit_message(view=view)
        if view is None:
            self.stop()

    @discord.ui.button(
        emoji=shuffle_emoji, 
        disabled=True,
        style=discord.ButtonStyle.gray,
        )
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):            
        playlist = get_playlist(self.guild_id)
        playlist.shuffle()
        self.shuffle.emoji = done_emoji
        self.shuffle.disabled = True
        self.shuffle.style = discord.ButtonStyle.success
        self.guild_info(self.guild_id).operation = DynEmbedOperation.UPDATE
        await interaction.response.edit_message(view=self)
        self.bot.loop.create_task(self.restore_shuffle())

    @discord.ui.button(
        emoji=repeat_emoji,
        label='',
        style=discord.ButtonStyle.danger)
    async def loop_control(self, interaction: discord.Interaction, button: discord.ui.Button):
        playlist = get_playlist(self.guild_id)
        if playlist.loop_state == LoopState.NOTHING:
            playlist.loop_state = LoopState.PLAYLIST
            button.emoji = repeat_emoji
            button.label = ''
            button.style = discord.ButtonStyle.success
        elif playlist.loop_state == LoopState.PLAYLIST:
            playlist.loop_state = LoopState.SINGLEINF
            button.emoji = repeat_sing_emoji
            button.label = 'ₛ'
            button.style = discord.ButtonStyle.success
        else:
            playlist.loop_state = LoopState.NOTHING
            button.emoji = repeat_emoji
            button.label = ''
            button.style = discord.ButtonStyle.danger

        await process_suggestion(interaction.guild, self.guild_info(self.guild_id))
        self.guild_info(self.guild_id).operation = DynEmbedOperation.UPDATE
        await interaction.response.edit_message(view=self)

    @discord.ui.button(
        label='⬜ 推薦音樂', 
        style=discord.ButtonStyle.danger,
        emoji=bulb_emoji)
    async def suggest(self, interaction: discord.Interaction, button: discord.ui.Button):            
        await self.suggestion_control(interaction, button)

    @discord.ui.button(label='搜尋/新增歌曲', emoji=search_emoji, style=discord.ButtonStyle.green)
    async def new_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(self.queue.new_song_modal_helper()(interaction.user))

    @discord.ui.button(label='列出候播清單', emoji=queue_emoji, style=discord.ButtonStyle.gray, row=2)
    async def listqueue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.queue.ShowQueue(interaction, 'button')

    @discord.ui.button(label='離開語音頻道',
                        emoji=leave_emoji, style=discord.ButtonStyle.gray, row=2)
    async def leavech(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = get_player()
        await player._leave(interaction.guild)
        reset_value(self.guild_id)
        self.clear_items()
        self.guild_info(self.guild_id).operation = DynEmbedOperation.LEAVE
        self.stop()
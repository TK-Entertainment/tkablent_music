from discord.ext import commands
import discord
import wavelink
import dotenv
import asyncio
import os

from .NodeHelper import node_helper

from Storage.PlaylistStorage import playlist_storage
from Storage.GuildPlayerInfo import guild_player_info
from Misc.Enums import LoopState

class PlayerHelper:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def _refresh_sessdata(self):
        while True:
            need_refresh = await node_helper._bilibilic.chcek_refresh()
            if need_refresh:
                await node_helper._bilibilic.refresh()
                sessdata = node_helper._bilibilic.sessdata
                bili_jct = node_helper._bilibilic.bili_jct
                dotenv.set_key(dotenv_path=fr"{os.getcwd()}/.env", key_to_set="SESSDATA", value_to_set=sessdata)
                dotenv.set_key(dotenv_path=fr"{os.getcwd()}/.env", key_to_set="BILI_JCT", value_to_set=bili_jct)
            await asyncio.sleep(120)

    async def _join(self, channel: discord.VoiceChannel):
        voice_client = channel.guild.voice_client
        mainplayhost = node_helper.TW_PlaybackNode
        if voice_client is None:
            await channel.connect(cls=wavelink.Player(nodes=[mainplayhost]))

    async def _leave(self, guild: discord.Guild):
        voice_client = guild.voice_client
        if voice_client is not None:
            await self._stop(guild)
            await voice_client.disconnect()
            
    async def _search(self, guild: discord.Guild, trackinfo, requester: discord.Member):
        await playlist_storage.add_songs(guild.id, trackinfo, requester)

    async def _pause(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if not voice_client.is_paused() and voice_client.is_playing():
            await voice_client.pause()
            self._start_timer(guild)

    async def _resume(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client.is_paused():
            if guild_player_info[guild.id]._timer is not None:
                guild_player_info[guild.id]._timer.cancel()
                guild_player_info[guild.id]._timer = None
            await voice_client.resume()

    async def _skip(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            if voice_client.is_paused():
                await voice_client.resume()
            await voice_client.stop()
            self._playlist[guild.id].times = 0
            if self._playlist[guild.id].loop_state == LoopState.SINGLEINF:
                self._playlist[guild.id].loop_state = LoopState.NOTHING
    
    async def _stop(self, guild: discord.Guild):
        self._playlist[guild.id].clear()
        await self._skip(guild)
    
    async def _seek(self, guild: discord.Guild, timestamp: float):
        voice_client: wavelink.Player = guild.voice_client
        if timestamp >= (self._playlist[guild.id].current().length)/1000:
            await voice_client.stop()
        await voice_client.seek(timestamp * 1000)
    
    async def _volume(self, guild: discord.Guild, volume: float):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client is not None:
            mute = volume == 0
            if mute:
                volume = 1e-5
            else:
                guild_player_info[guild.id].volume_level = volume
            await voice_client.set_volume(volume)
            await self.bot.ws.voice_state(guild.id, voice_client.channel.id, self_mute=mute)
            
    async def _play(self, guild: discord.Guild, channel: discord.TextChannel):
        guild_player_info[guild.id].text_channel = channel
        vc: wavelink.Player = guild.voice_client
        if guild_player_info[guild.id]._timer is not None:
            guild_player_info[guild.id]._timer.cancel()
            guild_player_info[guild.id]._timer = None
        self._start_timer(guild)
        
        if not vc.is_playing() and len(self._playlist[guild.id].order) > 0:
            await vc.play(self._playlist[guild.id].current())

    def _start_timer(self, guild: discord.Guild):
        if guild_player_info[guild.id]._timer is not None:
            guild_player_info[guild.id]._timer.cancel()
        coro = self._timer(guild)
        guild_player_info[guild.id]._timer = self.bot.loop.create_task(coro)
    
    async def _timer(self, guild: discord.Guild):
        await asyncio.sleep(600.0)
        guild_player_info[guild.id]._timer_done = True
        await self._leave(guild)
    
    def _cleanup(self, guild: discord.Guild):
        if guild_player_info[guild.id]._task is not None:
            guild_player_info[guild.id]._task = None
        
        playlist_storage.delete(guild.id)
        
        if guild_player_info[guild.id]._timer is not None:
            guild_player_info[guild.id]._timer.cancel()
            guild_player_info[guild.id]._timer = None

        guild_player_info.delete(guild.id)
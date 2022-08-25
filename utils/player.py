from typing import *
import asyncio, json

import discord
from discord.ext import commands

import wavelink
import spotipy
from ytmusicapi import YTMusic
from spotipy.oauth2 import SpotifyClientCredentials
from wavelink.ext import spotify
from .playlist import Playlist

INF = int(1e18)

class GuildInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self.text_channel: discord.TextChannel = None
        self._volume_level: int = None
        self._multitype_remembered: bool = None
        self._multitype_choice: str = None
        self._task: asyncio.Task = None
        self._timer: asyncio.Task = None
    
    @property
    def volume_level(self):
        if self._volume_level is None:
            self._volume_level = self.fetch('volume_level')
        return self._volume_level

    @volume_level.setter
    def volume_level(self, value):
        self._volume_level = value
        self.update('volume_level', value)

    @property
    def multitype_remembered(self):
        if self._multitype_remembered is None:
            self._multitype_remembered = self.fetch('multitype_remembered')
        return self._multitype_remembered

    @multitype_remembered.setter
    def multitype_remembered(self, value):
        self._multitype_remembered = value
        self.update('multitype_remembered', value)

    @property
    def multitype_choice(self):
        if self._multitype_choice is None:
            self._multitype_choice = self.fetch('multitype_choice')
        return self._multitype_choice

    @multitype_choice.setter
    def multitype_choice(self, value):
        self._multitype_choice = value
        self.update('multitype_choice', value)

    def fetch(self, key: str) -> not None:
        '''fetch from database'''

        with open(r'utils\data.json', 'r') as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None or data[str(self.guild_id)].get(key) is None:
            return data['default'][key]
        return data[str(self.guild_id)][key]

    def update(self, key: str, value: str) -> None:
        '''update database'''

        with open(r'utils\data.json', 'r') as f:
            data: dict = json.load(f)
        if data.get(str(self.guild_id)) is None:
            data[str(self.guild_id)] = dict()
        data[str(self.guild_id)][key] = value
        with open(r'utils\data.json', 'w') as f:
            json.dump(data, f)

class Player:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._playlist: Playlist = Playlist()
        self._guilds_info: Dict[int, GuildInfo] = dict()
        self.playnode: wavelink.Node = None
        self.searchnode: wavelink.Node = None
        self.ytapi: YTMusic = YTMusic(requests_session=False)

    def __getitem__(self, guild_id) -> GuildInfo:
        if self._guilds_info.get(guild_id) is None:
            self._guilds_info[guild_id] = GuildInfo(guild_id)
        return self._guilds_info[guild_id] 

    def _start_daemon(self, bot, host, port, password, spotify_id, spotify_secret):
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=spotify_id, client_secret=spotify_secret))
        return wavelink.NodePool.create_node(
            bot=bot,
            host=host,
            port=port,
            password=password,
            identifier="PlaybackServer",
            spotify_client=spotify.SpotifyClient(client_id=spotify_id, client_secret=spotify_secret)
        )

    def _start_search_daemon(self, bot, host, port, password, spotify_id, spotify_secret):
        return wavelink.NodePool.create_node(
            bot=bot,
            host=host,
            port=port,
            password=password,
            identifier="SearchServer",
            spotify_client=spotify.SpotifyClient(client_id=spotify_id, client_secret=spotify_secret)
        )

    async def _join(self, channel: discord.VoiceChannel):
        voice_client = channel.guild.voice_client
        if voice_client is None:
            await channel.connect(cls=wavelink.Player)

    async def _leave(self, guild: discord.Guild):
        voice_client = guild.voice_client
        if voice_client is not None:
            await self._stop(guild)
            await voice_client.disconnect()
            
    async def _search(self, guild: discord.Guild, trackinfo, requester: discord.Member):
        await self._playlist.add_songs(guild.id, trackinfo, requester)

    async def _pause(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if not voice_client.is_paused() and voice_client.is_playing():
            await voice_client.pause()

    async def _resume(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client.is_paused():
            await voice_client.resume()

    async def _skip(self, guild: discord.Guild):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            if voice_client.is_paused():
                await voice_client.resume()
            await voice_client.stop()
        self._playlist[guild].times = 0
    
    async def _stop(self, guild: discord.Guild):
        self._playlist[guild.id].clear()
        await self._skip(guild)
    
    async def _seek(self, guild: discord.Guild, timestamp: float):
        voice_client: wavelink.Player = guild.voice_client
        if timestamp >= self._playlist[guild.id].current().length:
            await voice_client.stop()
        await voice_client.seek(timestamp * 1000)
    
    async def _volume(self, guild: discord.Guild, volume: float):
        voice_client: wavelink.Player = guild.voice_client
        if voice_client is not None:
            mute = volume == 0
            if mute:
                volume = 1e-5
            else:
                self[guild.id].volume_level = volume
            await voice_client.set_volume(volume)
            await self.bot.ws.voice_state(guild.id, voice_client.channel.id, self_mute=mute)
            
    async def _play(self, guild: discord.Guild, channel: discord.TextChannel):
        self[guild.id].text_channel = channel
        await self._start_mainloop(guild)

    async def _start_mainloop(self, guild: discord.Guild):
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
            self[guild.id]._timer = None
        if self[guild.id]._task is not None:
            return
        coro = self._mainloop(guild)
        self[guild.id]._task = self.bot.loop.create_task(coro)
        self[guild.id]._task.add_done_callback(lambda task, guild=guild: self._start_timer(guild))
    
    async def _mainloop(self, guild: discord.Guild):
        # implement in musicbot class for ui support
        '''
        while len(self._playlist[guild.id].order):
            await self[guild.id].text_channel.send('now playing')
            voice_client: VoiceClient = guild.voice_client
            song = self._playlist[guild.id].current()
            try:
                voice_client.play(discord.FFmpegPCMAudio(song.url))
                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(1.0)
            finally:
                self._playlist.rule(guild.id)
        '''
        raise NotImplementedError

    def _start_timer(self, guild: discord.Guild):
        if self[guild.id]._task is not None:
            self[guild.id]._task.cancel()
            self[guild.id]._task = None
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
        coro = self._timer(guild)
        self[guild.id]._timer = self.bot.loop.create_task(coro)
    
    async def _timer(self, guild: discord.Guild):
        await asyncio.sleep(600.0)
        await self._leave(guild)
    
    def _cleanup(self, guild: discord.Guild):
        if self[guild.id]._task is not None:
            self[guild.id]._task = None
        del self._playlist[guild.id]
        if self[guild.id]._timer is not None:
            self[guild.id]._timer.cancel()
            self[guild.id]._timer = None

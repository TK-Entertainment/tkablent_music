from typing import *
import discord

import wavelink
from ..playlist import LoopState

class InfoGenerator:
    def __init__(self):
        from ..ui import musicbot, bot, _sec_to_hms, embed_opt,\
                        auto_stage_available, guild_info

        self.musicbot = musicbot
        self.bot = bot
        self._sec_to_hms = _sec_to_hms
        self.embed_opt = embed_opt
        self.auto_stage_available = auto_stage_available
        self.guild_info = guild_info

    def _SongInfo(self, guild_id: int, color_code: str = None, index: int = 0):
        playlist = self.musicbot._playlist[guild_id]
        song = playlist[index]

        if color_code == "green": # Green means adding to queue
            color = discord.Colour.from_rgb(97, 219, 83)
        elif color_code == "red": # Red means deleted
            color = discord.Colour.from_rgb(255, 0, 0)
        else: 
            color = discord.Colour.from_rgb(255, 255, 255)

        # Generate Loop Icon
        if color_code != "red" and playlist.loop_state != LoopState.NOTHING:
            loopstate: LoopState = playlist.loop_state
            loopicon = ''
            if loopstate == LoopState.SINGLE:
                loopicon = f' | 🔂 🕗 {playlist.times} 次'
            elif loopstate == LoopState.SINGLEINF:
                loopicon = ' | 🔂'
            elif loopstate == LoopState.PLAYLIST:
                loopicon = ' | 🔁'
        else:
            loopstate = None
            loopicon = ''

        # Generate Embed Body
        embed = discord.Embed(title=song.title, url=song.uri, colour=color)
        embed.add_field(name="作者", value=f"{song.author}", inline=True)
        embed.set_author(name=f"這首歌由 {song.requester.name}#{song.requester.discriminator} 點播", icon_url=song.requester.display_avatar)
        
        if song.is_stream(): 
            embed._author['name'] += " | 🔴 直播"
            if color_code == None: 
               embed.add_field(name="結束播放", value=f"輸入 ⏩ {self.bot.command_prefix}skip / ⏹️ {self.bot.command_prefix}stop\n來結束播放此直播", inline=True)
        else: 
            embed.add_field(name="歌曲時長", value=self._sec_to_hms(song.length, "zh"), inline=True)
        
        if self.musicbot[guild_id]._volume_level == 0: 
            embed._author['name'] += " | 🔇 靜音"
        
        if loopstate != LoopState.NOTHING: 
            embed._author['name'] += f"{loopicon}"
        
        if len(playlist.order) > 1 and color_code != 'red':
            queuelist: str = ""
            queuelist += f"1." + playlist[1].title + "\n"
            if len(playlist.order) > 2: 
                queuelist += f"...還有 {len(playlist.order)-2} 首歌"

            embed.add_field(name=f"待播清單 | {len(playlist.order)-1} 首歌待播中", value=queuelist, inline=False)
        embed.set_thumbnail(url=f'https://img.youtube.com/vi/{song.identifier}/0.jpg')
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
        return embed

    def _PlaylistInfo(self, playlist: wavelink.YouTubePlaylist, requester: discord.User):
        # Generate Embed Body
        color = discord.Colour.from_rgb(97, 219, 83)
        embed = discord.Embed(title=playlist.name, colour=color)
        embed.set_author(name=f"此播放清單由 {requester.name}#{requester.discriminator} 點播", icon_url=requester.display_avatar)

        pllist: str = ""
        for i in range(2):
            pllist += f"{i+1}. {playlist.tracks[i].title}\n"
        if len(playlist.tracks) > 2:
            pllist += f"...還有 {len(playlist.tracks)-2} 首歌"
        
        embed.add_field(name=f"歌曲清單 | 已新增 {len(playlist.tracks)} 首歌", value=pllist, inline=False)
        embed.set_thumbnail(url=f'https://img.youtube.com/vi/{playlist.tracks[0].identifier}/0.jpg')
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))

        return embed

    async def _UpdateSongInfo(self, guild_id: int):
        message = f'''
            **:arrow_forward: | 正在播放以下歌曲**
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*'''
        if not self.auto_stage_available(guild_id):
            message += '\n            *可能需要手動對機器人*` 邀請發言` *才能正常播放歌曲*'
        await self.guild_info(guild_id).playinfo.edit(content=message, embed=self._SongInfo(guild_id), view=self.guild_info(guild_id).playinfo_view)
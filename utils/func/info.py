from typing import *
import discord
import requests

import wavelink
from ..playlist import LoopState, SpotifyAlbum
from ..ui import caution_emoji, youtube_emoji, spotify_emoji, soundcloud_emoji, skip_emoji

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

        if len(playlist.order) == 0:
            return None

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
                loopicon = f' | 🔂ₛ 🕗 {playlist.times} 次'
            elif loopstate == LoopState.SINGLEINF:
                loopicon = ' | 🔂ₛ'
            elif loopstate == LoopState.PLAYLIST:
                loopicon = ' | 🔁'
        else:
            loopstate = None
            loopicon = ''

        # Generate Embed Body
        if 'youtube' in song.uri:
            source_icon = youtube_emoji
        elif 'soundcloud' in song.uri:
            source_icon = soundcloud_emoji
        elif 'spotify' in song.uri:
            source_icon = spotify_emoji

        embed = discord.Embed(title=f"{source_icon} | {song.title}", url=song.uri, colour=color)
        embed.add_field(name="作者", value=f"{song.author}", inline=True)
        if song.suggested:
            embed.set_author(name=f"這首歌為 自動推薦歌曲", icon_url="https://i.imgur.com/p4vHa3y.png")
        else:
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

        queuelist: str = ""

        if self.guild_info(guild_id).skip: # If song is skipped, update songinfo for next song state
            offset = 1
        else:
            offset = 0

        if self.guild_info(guild_id).music_suggestion and len(playlist.order) == 2 and playlist[1].suggested and color_code != 'red':
            if self.guild_info(guild_id).skip:
                queuelist += f"**推薦歌曲載入中**"
            else:
                queuelist += f"**【推薦】** {playlist[1].title}"
            embed.add_field(name="{} 即將播放".format(f":hourglass: |" if self.guild_info(guild_id).skip else ""), value=queuelist, inline=False)
        
        elif len(playlist.order) == 1 and playlist.loop_state == LoopState.PLAYLIST:
            embed.add_field(name="即將播放", value="*無下一首，將重複播放此歌曲*", inline=False)
        
        elif len(playlist.order)-offset > 1 and color_code != 'red':
            queuelist += f"**>> {playlist[1+offset].title}**\n*by {playlist[1+offset].requester}*\n"
            if len(playlist.order) > 2: 
                queuelist += f"*...還有 {len(playlist.order)-2-offset} 首歌*"

            embed.add_field(name=f"即將播放 | {len(playlist.order)-1-offset} 首歌待播中", value=queuelist, inline=False)

        if 'youtube' in song.uri:
            embed.set_thumbnail(url=f'https://img.youtube.com/vi/{song.identifier}/hqdefault.jpg')
        elif 'spotify' in song.uri and (color != 'green' or color != 'red'):
            embed.set_thumbnail(url=song.cover)
            embed.add_field(name=f"{youtube_emoji} | 音樂來源", value=f'[{song.yt_title}]({song.yt_url})', inline=False)
            embed.add_field(name=f"為何有這個？", value=f'''
因 Spotify 平台的特殊性 (無法取得其音源)
故此機器人是使用相對應的標題及其他資料
在 Youtube 上找到最相近的音源
            ''', inline=False)

        if self.guild_info(guild_id).music_suggestion and song.audio_source == 'soundcloud' and (color_code != 'red' or color_code != 'green'):
            embed.add_field(name=f"{caution_emoji} | 自動歌曲推薦已暫時停用", value=f'此歌曲來源為 Soundcloud\n暫時不支援自動歌曲推薦\n請點播一首 Youtube/Spotify 的歌曲來重新啟用', inline=False)

        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
        return embed

    def _PlaylistInfo(self, playlist: Union[wavelink.YouTubePlaylist, SpotifyAlbum], requester: discord.User):
        # Generate Embed Body
        if isinstance(playlist, wavelink.YouTubePlaylist):
            source_icon = youtube_emoji
        else:
            source_icon = spotify_emoji
        color = discord.Colour.from_rgb(97, 219, 83)
        embed = discord.Embed(title=f"{source_icon} | {playlist.name}", url=playlist.uri, colour=color)
        embed.set_author(name=f"此播放清單由 {requester.name}#{requester.discriminator} 點播", icon_url=requester.display_avatar)

        pllist: str = ""
        for i, track in enumerate(playlist.tracks):
            pllist += f"{i+1}. {track.title}\n"
            if i == 1: 
                break
        if len(playlist.tracks) > 2:
            pllist += f"...還有 {len(playlist.tracks)-2} 首歌"
        
        embed.add_field(name=f"歌曲清單 | 已新增 {len(playlist.tracks)} 首歌", value=pllist, inline=False)
        if isinstance(playlist, wavelink.YouTubePlaylist):
            embed.set_thumbnail(url=f'https://img.youtube.com/vi/{playlist.tracks[0].identifier}/hqdefault.jpg')
        else:
            embed.set_thumbnail(url=playlist.thumbnail)
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))

        return embed

    async def _UpdateSongInfo(self, guild_id: int):
        if self.guild_info(guild_id).lastskip and len(self.musicbot._playlist[guild_id].order) == 1:
            message = f'''
            **:fast_forward: | 跳過歌曲**
            目前歌曲已成功跳過，候播清單已無歌曲
            正在播放最後一首歌曲，資訊如下所示
            *輸入 **{self.bot.command_prefix}play** 以加入新歌曲*
                '''
        elif self.guild_info(guild_id).lastskip and len(self.musicbot._playlist[guild_id].order) > 1:
            message = f'''
            **:fast_forward: | 跳過歌曲**
            目前歌曲已成功跳過，正在播放下一首歌曲，資訊如下所示
            *輸入 **{self.bot.command_prefix}play** 以加入新歌曲*
                '''
        elif len(self.musicbot._playlist[guild_id].order) == 0:
            message = f'''
            **:clock4: | 播放完畢，等待播放動作**
            候播清單已全數播放完畢，等待使用者送出播放指令
            *輸入 **{self.bot.command_prefix}play [URL/歌曲名稱]** 即可播放/搜尋*
        '''
        else:
            message = f'''
            **:arrow_forward: | 正在播放以下歌曲**
            *輸入 **{self.bot.command_prefix}pause** 以暫停播放*'''
            
        if not self.auto_stage_available(guild_id):
            message += '\n            *可能需要手動對機器人*` 邀請發言` *才能正常播放歌曲*'

        self.guild_info(guild_id).playinfo_view.skip.emoji = skip_emoji
        if len(self.musicbot._playlist[guild_id].order) == 1:
            self.guild_info(guild_id).playinfo_view.skip.style = discord.ButtonStyle.gray
            self.guild_info(guild_id).playinfo_view.skip.disabled = True
        else:
            self.guild_info(guild_id).playinfo_view.skip.style = discord.ButtonStyle.blurple
            self.guild_info(guild_id).playinfo_view.skip.disabled = False

        await self.guild_info(guild_id).playinfo.edit(content=message, embed=self._SongInfo(guild_id), view=self.guild_info(guild_id).playinfo_view)
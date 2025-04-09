from .exception_handler import ExceptionHandler
import discord

import time
from ..utils.storage import GuildInfo
from ..utils.track_helper import TrackHelper
from ..enums import ButtonType
from ..emoji import Emoji
from .queue import Queue

class Search:
    def __init__(self, exception_handler, queue):
        self.exception_handler: ExceptionHandler = exception_handler
        self.queue: Queue = queue

    async def YoutubeFuckedUp(self, interaction: discord.Interaction):
        msg = f"""
            **:no_entry: | 很遺憾地告訴你...**
            因應 Discord 新政策
            您摯愛的點歌方式 — **Youtube 連結** 已經*寄*了
            
            但請放心，您還是能用關鍵字去搜尋音樂 (我們有找到第三方提供者)
            對 Spotify 以及 Soundcloud 的連結還是支援的喔~

            *只能說，全世界的版權意識都慢慢上來了呢ww*

            **迷因、幹話、美好的事物
            為平淡的生活增添更多色彩
            
            TK Entertainment**
                """
        await interaction.response.send_message(msg, ephemeral=True)

    async def SearchWhenPlaying(self, interaction: discord.Interaction, track_helper: TrackHelper, guild_info: GuildInfo, musicbot):
        class MusicChooseButton(discord.ui.Button):
            queue = self.queue

            def __init__(self, trackid: str, number: int, musictype: ButtonType, musicbot):
                grid = ["", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

                match musictype:
                    case ButtonType.RECOMMEND:
                        style = discord.ButtonStyle.blurple
                        row = 1
                    case ButtonType.HISTORY:
                        style = discord.ButtonStyle.gray
                        row = 2
                    case ButtonType.OTHER | ButtonType.FAVORITE:
                        style = discord.ButtonStyle.green
                        row = 3
                
                if musictype != ButtonType.OTHER and musictype != ButtonType.FAVORITE:
                    super().__init__(
                        emoji=grid[number],
                        style=style,
                        row=row
                    )
                else:
                    if musictype == ButtonType.FAVORITE:
                        super().__init__(
                            label="列出最愛",
                            emoji=Emoji.star_bright,
                            style=style,
                            row=row
                        )
                    else:
                        super().__init__(
                            label="其他歌曲",
                            emoji=Emoji.search_emoji,
                            style=style,
                            row=row
                        )

                self.trackid = trackid
                self.musictype = musictype
                self.musicbot = musicbot

            async def callback(self, interaction: discord.Interaction):
                if self.musictype != ButtonType.OTHER:
                    if self.musictype == ButtonType.FAVORITE:
                        await self.musicbot._i_play.callback(
                            self.musicbot, interaction, f"sid=>showallfav"
                        )
                    else:
                        await self.musicbot._i_play.callback(
                            self.musicbot, interaction, f"sid=>{self.trackid}"
                        )
                else:
                    await interaction.response.send_modal(
                        self.queue.new_song_modal_helper()(interaction.user)
                    )
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        embed = discord.Embed(
            title="🎶 | 點播新歌曲",
            description="您可以選擇以下的推薦/曾點播過的歌曲\n或點擊「其他歌曲」來點播其他的歌曲\n亦或是點擊「列出最愛」來列出最愛的歌曲",
        )
        view = discord.ui.View()
        i = 1
        if len(guild_info.mostly_played) > 10:
            mostly_played = ""
            k = 0
            for trackid in guild_info.mostly_played:
                if musicbot.track_helper._cache.get(trackid[0]) is None or (int(time.time()) - musicbot.track_helper._cache.get(trackid[0])["timestamp"] >= 2592000):
                    track = await track_helper.get_track(interaction, f"sid=>{trackid[0]}", quick_search=True)
                    if track[0] is None: continue
                    title = track[0].title
                    identifier = track[0].identifier
                else:
                    title = musicbot.track_helper._cache[trackid[0]]["title"]
                    identifier = trackid[0]
                mostly_played += f"**【{i}】** {title}\n"
                #embed.add_field(name=f"【{i}】", value=f"{title}", inline=True)
                view.add_item(MusicChooseButton(identifier, i, ButtonType.RECOMMEND, musicbot))
                i += 1
                k += 1
                if k == 4: break
            
            if mostly_played == "": mostly_played = "❌ | 目前無可用推薦項目 (*°∀°)"
            
        embed.add_field(
            name=f"💖【好聽一直聽】",
            value="❌ | 目前此項資料不足，暫時不可用。" if len(guild_info.mostly_played) <= 10 else mostly_played,
            inline=False
        )

        if len(guild_info.recently_played) != 0:
            recently_played = ""
            k = 0
            for trackid in guild_info.recently_played:
                if musicbot.track_helper._cache.get(trackid) is None or (int(time.time()) - musicbot.track_helper._cache.get(trackid)["timestamp"] >= 2592000):
                    track = await track_helper.get_track(interaction, f"sid=>{trackid}", quick_search=True)
                    if track[0] is None: continue
                    title = track[0].title
                    identifier = track[0].identifier
                else:
                    title = musicbot.track_helper._cache[trackid]["title"]
                    identifier = trackid
                
                recently_played += f"**【{i}】** {title}\n"
                #embed.add_field(name=f"【{i}】", value=f"{title}", inline=True)
                view.add_item(MusicChooseButton(identifier, i, ButtonType.HISTORY, musicbot))
                i += 1
                k += 1
                if k == 4: break  
            if recently_played == "": recently_played = "❌ | 目前無可用推薦項目 (*°∀°)"

        embed.add_field(
            name=f"🕒【最近播放】", 
            value="❌ | 最近這個群組沒放過啥歌 (*°∀°)" if len(guild_info.recently_played) == 0 else recently_played,
            inline=False
        )

        view.add_item(MusicChooseButton(0, i, ButtonType.OTHER, musicbot))
        view.add_item(MusicChooseButton(0, i+1, ButtonType.FAVORITE, musicbot))
        await interaction.followup.send(embed=embed, view=view)

    async def SearchFailed(self, interaction: discord.Interaction, url) -> None:
        await self.exception_handler._MusicExceptionHandler(interaction, None, url)

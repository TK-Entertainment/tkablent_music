from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from typing import *
import discord
import random
import datetime
import copy

import wavelink
from ..playlist import LoopState
from ..ui import LeaveType, StopType
from ..ui import caution_emoji, spotify_emoji, skip_emoji, search_emoji, repeat_emoji


class InfoGenerator:
    def __init__(self):
        from ..ui import (
            musicbot,
            bot,
            _sec_to_hms,
            embed_opt,
            auto_stage_available,
            guild_info,
        )

        self.musicbot = musicbot
        self.bot = bot
        self._sec_to_hms = _sec_to_hms
        self.embed_opt = embed_opt
        self.auto_stage_available = auto_stage_available
        self.guild_info = guild_info

    def _isitholiday(self):
        holiday = ""
        month = datetime.datetime.now().month
        day = datetime.datetime.now().day
        if month == 12 and day == 24:
            holiday = "xmaseve"
        elif month == 12 and day == 25:
            holiday = "xmas"
        elif month == 12 and day == 31:
            holiday = "newyeareve"
        elif month == 1 and day == 1:
            holiday = "newyear"
        elif (month == 1 and day >= 21 and day <= 30):
            holiday = "cnewyear"
        else:
            holiday = ""

        return holiday

    def _SongInfo(
        self,
        guild_id: int,
        color_code: str = None,
        index: int = 0,
        removed=None,
        operation: LeaveType = None,
        operator: discord.Member = None,
    ):
        holiday = self._isitholiday()
        embed_opt = copy.deepcopy(self.embed_opt)

        playlist = self.musicbot._playlist[guild_id]

        # This part for non-playing state
        if len(playlist.order) == 0:
            # String that shows when bot leaving
            if isinstance(operation, LeaveType):
                match operation:
                    case LeaveType.ByCommand:
                        txt = f"📤 | 已退出語音/舞台頻道"
                    case LeaveType.ByButton:
                        if operator.discriminator == "0":
                            txt = f"📤 | 由 {operator.name} 要求退出語音/舞台頻道"
                        else:
                            txt = f"📤 | 由 {operator.name}#{operator.discriminator} 要求退出語音/舞台頻道"
                    case LeaveType.ByTimeout:
                        txt = f"📤/🕗 | 因機器人已閒置 10 分鐘，已自動退出"
            # String that shows when bot stopping
            elif isinstance(operation, StopType):
                match operation:
                    case StopType.ByCommand:
                        txt = f"⏹️ | 已停止播放歌曲並清除待播清單"
                    case StopType.ByButton:
                        if operator.discriminator == "0":
                            txt = f"⏹️ | 由 {operator.name} 要求停止播放歌曲並清除待播清單"
                        else:
                            txt = f"⏹️ | 由 {operator.name}#{operator.discriminator} 要求停止播放歌曲並清除待播清單"
            else:
                txt = f"🕗 | 歌曲均已播放完畢，等待指令"

            embed = discord.Embed(
                title=f"輸入 /play [URL/關鍵字] 來開始播放",
                colour=discord.Colour.from_rgb(255, 255, 255),
            )
            if holiday == "xmas" or holiday == "xmaseve":
                embed.set_author(name=txt, icon_url="https://i.imgur.com/c3X2KBD.png")
            else:
                embed.set_author(name=txt, icon_url="https://i.imgur.com/p4vHa3y.png")
        
        # This part for playing state
        else:
            if color_code == "red":
                song = removed
            else:
                song: wavelink.Playable = playlist[index]

            # Embed side color decision
            if holiday == "xmas" or holiday == "xmaseve":
                xmascolors = [
                    discord.Colour.from_rgb(187, 37, 40),
                    discord.Colour.from_rgb(234, 70, 48),
                    discord.Colour.from_rgb(248, 178, 41),
                    discord.Colour.from_rgb(20, 107, 58),
                    discord.Colour.from_rgb(22, 91, 51),
                ]

                color = random.choice(xmascolors)
            elif holiday == "newyear" and holiday == "cnewyear":
                color = discord.Colour.from_rgb(255, 0, 0)
            else:
                if color_code == "green":  # Green means adding to queue
                    color = discord.Colour.from_rgb(97, 219, 83)
                elif color_code == "red":  # Red means deleted
                    color = discord.Colour.from_rgb(255, 0, 0)
                else:
                    color = discord.Colour.from_rgb(255, 255, 255)

            # Generate Loop Icon
            if color_code != "red" and playlist.loop_state != LoopState.NOTHING:
                loopstate: LoopState = playlist.loop_state
                stateicon = ""
                if loopstate == LoopState.SINGLE:
                    stateicon = f"🔂ₛ 🕗 {playlist.times} 次"
                elif loopstate == LoopState.SINGLEINF:
                    stateicon = "🔂ₛ 單曲重播"
                elif loopstate == LoopState.PLAYLIST:
                    stateicon = "🔁 全待播清單重播"
            else:
                loopstate = None
                stateicon = ""

            # Generate Embed Body
            voice_client: wavelink.Player = self.bot.get_guild(guild_id).voice_client
            if color_code != "red" and color_code != "green":
                if (
                    len(voice_client.channel.members) == 1
                    and voice_client.channel.members[0] == self.bot.user
                ):
                    playing_state = "📤/⏸️ | 無人於頻道中，已暫停播放\n"
                elif self.guild_info(guild_id).skip:
                    playing_state = "⏩ | 已跳過上個歌曲\n"
                else:
                    if voice_client.paused:
                        playing_state = "⏸️ | 暫停播放\n"
                    else:
                        playing_state = "▶️ | 播放中\n"

                if not self.auto_stage_available(guild_id):
                    notice = "\n*可能需要手動對機器人 **邀請發言** 才能正常播放歌曲*"
                else:
                    notice = ""
            else:
                playing_state = ""
                notice = ""

            if not song.source == "spotify" and song.is_stream:
                embed = discord.Embed(
                    title=f"{song.title}",
                    description=f"**{song.author}**\n*🔴 直播*{notice}",
                    colour=color,
                )
            else:
                time_string = self._sec_to_hms((song.length) / 1000, "zh")
                embed = discord.Embed(
                    title=f"{song.title}",
                    description=f"**{song.author}**\n*{time_string}*{notice}",
                    colour=color,
                )

            # Generate Embed Author (indicates song requester)
            # song.suggested: bool (self defined)
            if song.suggested:
                # If song is suggested by bot, then indicates it as suggested song
                if holiday == "xmas" or holiday == "xmaseve":
                    embed.set_author(
                        name=f"{playing_state}這首歌為 自動推薦歌曲",
                        icon_url="https://i.imgur.com/c3X2KBD.png",
                    )
                else:
                    embed.set_author(
                        name=f"{playing_state}這首歌為 自動推薦歌曲",
                        icon_url="https://i.imgur.com/p4vHa3y.png",
                    )
            else:
                # Otherwise, show the requester of the song
                # song.requester: discord.User (self defined)
                if song.requester.discriminator == "0":
                    embed.set_author(
                        name=f"{playing_state}這首歌由 {song.requester.name} 點播",
                        icon_url=song.requester.display_avatar,
                    )
                else:
                    embed.set_author(
                        name=f"{playing_state}這首歌由 {song.requester.name}#{song.requester.discriminator} 點播",
                        icon_url=song.requester.display_avatar,
                    )
            
            # Generate stream notice
            if not song.source == "spotify" and song.is_stream:
                if color_code == None:
                    embed.add_field(
                        name="結束播放",
                        value=f"點擊 ⏩ **跳過** / ⏹️ **停止播放**\n來結束播放此直播",
                        inline=True,
                    )
            
            if holiday != "":
                if holiday == "xmaseve":
                    embed._author["name"] += "\n🎄 今日聖誕夜"
                elif holiday == "xmas":
                    embed._author["name"] += "\n🎄 聖誕節快樂！"
                elif holiday == "newyeareve":
                    embed._author["name"] += "\n🎊 明天就是{}了！".format(
                        datetime.datetime.now().year + 1
                    )
                elif holiday == "newyear":
                    embed._author["name"] += "\n🎊 {}新年快樂！".format(
                        datetime.datetime.now().year
                    )
                elif holiday == "cnewyear":
                    embed._author["name"] += "\n🧧 過年啦！你是發紅包還是收紅包呢？"

            if stateicon != "":
                embed_opt["footer"]["text"] = (
                    stateicon + "\n" + embed_opt["footer"]["text"]
                )

            queuelist: str = ""

            if self.guild_info(guild_id).skip:
            # If song is skipped, update songinfo for next song state
                offset = 1
            else:
                offset = 0

            # Upcoming song (via Suggestion)
            # playlist[].suggested: bool (self defined)
            if (
                self.guild_info(guild_id).music_suggestion
                and not ((len(playlist.order) >= 2 and not playlist[-1].suggested))
                and ((len(playlist.order) == 2 and playlist[-1].suggested) or self.guild_info(guild_id).suggestion_processing)
                and color_code != "red"
            ):
                if self.guild_info(guild_id).skip or self.guild_info(guild_id).suggestion_processing:
                    queuelist += f"**推薦歌曲載入中**"
                else:
                    queuelist += f"**:bulb:** {playlist[1].title}"
                embed.add_field(
                    name="{}即將播放".format(
                        f":hourglass: | " if self.guild_info(guild_id).skip or self.guild_info(guild_id).suggestion_processing else ""
                    ),
                    value=queuelist,
                    inline=False,
                )

            # Upcoming song (with single repeat on and only one song in queue)
            elif len(playlist.order) == 1 and playlist.loop_state == LoopState.PLAYLIST:
                embed.add_field(name="即將播放", value="*無下一首，將重複播放此歌曲*", inline=False)

            # Upcoming song
            elif len(playlist.order) - offset > 1 and color_code != "red":
                queuelist += f"**>> {playlist[1+offset].title}**\n*by {playlist[1+offset].requester}*\n"
                if len(playlist.order) > 2:
                    queuelist += f"*...還有 {len(playlist.order)-2-offset} 首歌*"

                embed.add_field(
                    name=f"即將播放 | {len(playlist.order)-1-offset} 首歌待播中",
                    value=queuelist,
                    inline=False,
                )

            if song.source == "spotify" and (color != "green" or color != "red"):
                embed.set_thumbnail(url=song.artwork)

            if (
                not self.musicbot.track_helper.check_current_suggest_support(guild_id)
            ) and (
                color_code != "red" or color_code != "green"
            ):  # color code refer to behaviour
                # red stands for delete information, green stands for add to queue notice
                embed.add_field(
                    name=f"{caution_emoji} | 自動歌曲推薦已暫時停用",
                    value=f"此歌曲暫時不支援自動歌曲推薦功能\n請播放其他歌曲來使用此功能",
                    inline=False,
                )

            if ("bilibili" in song.uri):
                embed_opt["footer"]["text"] = (
                    "【!】bilibili 播放測試 | 此功能僅供試用，不保證穩定\n" + embed_opt["footer"]["text"]
            )
            if ("spotify" in song.uri):
                embed_opt["footer"]["text"] = (
                    "【!】目前播放 Spotify 歌曲，結果可能不準確\n" + embed_opt["footer"]["text"]
            )

        embed_opt["footer"]["text"] = (
            embed_opt["footer"]["text"] + "\n播放伺服器由 404 Network Information Co. 提供支援"
        )

        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **embed_opt))
        return embed

    def _PlaylistInfo(
        self,
        playlist: Union[list[wavelink.Playable], list[wavelink.Playlist]],
        requester: discord.User,
    ):
        # Generate Embed Body
        if isinstance(playlist, list) and not isinstance(playlist[0], wavelink.Playlist):
            title = f"{search_emoji} | 選取的搜尋歌曲"
            url = None
        elif isinstance(playlist[0], wavelink.Playlist):
            if (playlist[0].url is not None) and ("spotify" in playlist[0].url):
                title = f"{spotify_emoji} | {playlist[0].name}"
                url = playlist[0].url
            else:
                title = f":newspaper: | 音樂播放清單"
                url = None
            
        color = discord.Colour.from_rgb(97, 219, 83)
        embed = discord.Embed(title=title, url=url, colour=color)
        if requester.discriminator == "0":
            embed.set_author(
                name=f"此播放清單由 {requester.name} 點播", icon_url=requester.display_avatar
            )
        else:
            embed.set_author(
                name=f"此播放清單由 {requester.name}#{requester.discriminator} 點播",
                icon_url=requester.display_avatar,
            )

        pllist: str = ""
        if isinstance(playlist, list) and not isinstance(playlist[0], wavelink.Playlist):
            tracklist = playlist
        else:
            tracklist = playlist[0].tracks

        for i, track in enumerate(tracklist):
            pllist += f"{i+1}. {track.title}\n"
            if i == 1:
                break

        if len(tracklist) > 2:
            pllist += f"...還有 {len(tracklist)-2} 首歌"

        embed.add_field(
            name=f"歌曲清單 | 已新增 {len(tracklist)} 首歌", value=pllist, inline=False
        )
        if (playlist[0].url is not None) and ("spotify" in playlist[0].url):
            embed.set_thumbnail(url=playlist.artwork)
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))

        return embed

    async def _UpdateSongInfo(self, guild_id: int):
        if len(self.musicbot._playlist[guild_id].order) == 0:
            try:
                await self.guild_info(guild_id).playinfo.edit(
                    embed=self._SongInfo(guild_id), view=None
                )
            except:
                self.guild_info(guild_id).playinfo = None
                self.guild_info(guild_id).playinfo_view = None
        else:
            self.guild_info(guild_id).playinfo_view.skip.emoji = skip_emoji
            if len(self.musicbot._playlist[guild_id].order) == 1:
                self.guild_info(
                    guild_id
                ).playinfo_view.skip.style = discord.ButtonStyle.gray
                self.guild_info(guild_id).playinfo_view.skip.disabled = True
            else:
                self.guild_info(
                    guild_id
                ).playinfo_view.skip.style = discord.ButtonStyle.blurple
                self.guild_info(guild_id).playinfo_view.skip.disabled = False

            if self.musicbot._playlist.is_noqueue(guild_id):
                self.guild_info(guild_id).playinfo_view.listqueue.disabled = True
                self.guild_info(guild_id).playinfo_view.listqueue.label = "暫無待播歌曲"
            else:
                self.guild_info(guild_id).playinfo_view.listqueue.disabled = False
                self.guild_info(guild_id).playinfo_view.listqueue.label = "待播清單"

            if self.musicbot._playlist[guild_id].loop_state == LoopState.SINGLE:
                # Modify loop button label to current loop times
                self.guild_info(
                    guild_id
                ).playinfo_view.loop_control.label = (
                    f"ₛ {self.musicbot._playlist[guild_id].times} 次"
                )
            elif self.musicbot._playlist[guild_id].loop_state == LoopState.NOTHING:
                # Modify loop button to non-loop state
                self.guild_info(
                    guild_id
                ).playinfo_view.loop_control.emoji = repeat_emoji
                self.guild_info(guild_id).playinfo_view.loop_control.label = ""
                self.guild_info(
                    guild_id
                ).playinfo_view.loop_control.style = discord.ButtonStyle.danger

            if not self.musicbot.track_helper.check_current_suggest_support(guild_id):
                self.guild_info(
                    guild_id
                ).playinfo_view.suggest.style = discord.ButtonStyle.gray
                self.guild_info(guild_id).playinfo_view.suggest.disabled = True
            else:
                self.guild_info(guild_id).playinfo_view.suggest.disabled = False
                if self.guild_info(guild_id).music_suggestion:
                    self.guild_info(
                        guild_id
                    ).playinfo_view.suggest.style = discord.ButtonStyle.green
                else:
                    self.guild_info(
                        guild_id
                    ).playinfo_view.suggest.style = discord.ButtonStyle.danger

            try:
                await self.guild_info(guild_id).playinfo.edit(
                    embed=self._SongInfo(guild_id),
                    view=self.guild_info(guild_id).playinfo_view,
                )
            except:
                self.guild_info(guild_id).playinfo = None
                self.guild_info(guild_id).playinfo_view = None
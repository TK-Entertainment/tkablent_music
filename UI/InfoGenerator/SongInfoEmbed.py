import discord
from typing import *
import wavelink
import random
from wavelink.ext import spotify
from datetime import datetime

from Misc.Enums import LoopState
from Generic.Emojis import Emoji
from Generic.Enums import LeaveType, StopType, Language, UIModule, Holiday, ColorCode
from Generic.Essentials import essentials
from Storage.PlaylistStorage import playlist_storage
from Storage.GuildPlayerInfo import guild_player_info
from Storage.GuildPlayInfo import guild_play_info

class SongInfo(discord.Embed):
    def __init__(
        self,
        guild_id: int, # Guild ID
        voice_client: wavelink.Player, # Voice Client
        lang: Language, # Language
        color_code: ColorCode = None, # Color Code for operation
        index: int = 0,
        removed = None,
        operation: LeaveType = None,
        operator: discord.Member = None
    ):
        self.lang = lang
        
        holiday = essentials.isitholiday()
        playlist = playlist_storage[guild_id]
        
        activity_text = self.get_activity_text(operation, operator)
        strings = essentials.get_language_dict(lang, UIModule.InfoGenerator)
        holiday_text = self.get_holiday_text(holiday)

        # Color decision
        if holiday == Holiday.Xmas or holiday == Holiday.XmasEve:
            xmascolors = [
                discord.Colour.from_rgb(187, 37, 40), 
                discord.Colour.from_rgb(234, 70, 48),
                discord.Colour.from_rgb(248, 178, 41),
                discord.Colour.from_rgb(20, 107, 58),
                discord.Colour.from_rgb(22, 91, 51),
                ]

            color = random.choice(xmascolors)

        elif holiday == Holiday.NewYear or holiday == Holiday.ChineseNewYear:
            color = discord.Colour.from_rgb(255, 0, 0)

        else:
            if color_code == ColorCode.Green: # Green means adding to queue
                color = discord.Colour.from_rgb(97, 219, 83)
            elif color_code == ColorCode.Red: # Red means deleted
                color = discord.Colour.from_rgb(255, 0, 0)
            else: # Normal state (which is white)
                color = discord.Colour.from_rgb(255, 255, 255)

        # When there is no song playing
        if len(playlist.order) == 0:
            super().__init__(title=strings["Info.Idle.Text"], colour=discord.Colour.from_rgb(255, 255, 255))
            if holiday == Holiday.Xmas or holiday == Holiday.XmasEve:
                self.set_author(name=f"{holiday_text}\n{activity_text}", icon_url="https://i.imgur.com/c3X2KBD.png")
            else:
                self.set_author(name=f"{holiday_text}\n{activity_text}", icon_url="https://i.imgur.com/p4vHa3y.png")
            footer_add_bili = ""
            footer_add_state = ""

        else:
            # Means called by /remove function
            if color_code == ColorCode.Red:
                song = removed
            # Behave as normal info generator
            else:
                song: wavelink.GenericTrack = playlist[index]

            # Generate Loop Icon
            if color_code != ColorCode.Red and playlist.loop_state != LoopState.NOTHING:
                loopstate: LoopState = playlist.loop_state
                stateicon = ''

                match loopstate:
                    case LoopState.SINGLE:
                        stateicon = '🔂ₛ 🕗 {}' \
                                    .format(
                                        strings["Info.Loop.Single.Times"]
                                        .replace(r"{times}", playlist.times)
                                    )
                    case LoopState.SINGLEINF:
                        stateicon = '🔂ₛ {}'.format(strings["Info.Loop.Single"])
                    case LoopState.PLAYLIST:
                        stateicon = '🔁 {}'.format(strings["Info.Loop.Playlist"])
                    case _:
                        stateicon = ''
            else:
                loopstate = None
                stateicon = ''

            # Generate Embed Body
            if color_code != ColorCode.Red and color_code != ColorCode.Green:
                playing_state = self.get_playing_activity_text(voice_client, guild_id)
                
                if not self.auto_stage_available(guild_id):
                    notice = strings["Info.AutoStageNotice"]
                else:
                    notice = ""
            else:
                playing_state = ""
                notice = ""
                    
            if not isinstance(song, spotify.SpotifyTrack) and song.is_stream:
                super().__init__(
                    title=f"{song.title}", 
                    description="**{}**\n*🔴 {}*{}"
                                .format(song.author, strings["Info.Stream"], notice),
                    colour=color
                )
            else:
                if lang == Language.zh_tw:
                    time_string = essentials.sec_to_hms((song.length)/1000, "zh")
                else:
                    time_string = essentials.sec_to_hms((song.length)/1000, "symbol")
                
                super().__init__(
                    title=f"{song.title}", 
                    description=f"**{song.author}**\n*{time_string}*{notice}", 
                    colour=color
                )

            if song.suggested:
                source_text = strings["Info.Source.Suggested"]

                if holiday == Holiday.Xmas or holiday == Holiday.XmasEve:
                    icon = "https://i.imgur.com/c3X2KBD.png"
                else:
                    icon = "https://i.imgur.com/p4vHa3y.png"
                
                self.set_author(name=f"{holiday_text}{playing_state}{source_text}", icon_url=icon)
            else:
                if song.requester.discriminator == "0":
                    source_text = strings["Info.Source.Old"] \
                                    .replace(r"{name}", song.requester.name) \
                                    .replace(r"{code}", song.requester.discriminator)
                else:
                    source_text = strings["Info.Source.New"] \
                                    .replace(r"{name}", song.requester.name)
                self.set_author(name=f"{holiday_text}{playing_state}{source_text}", icon_url=song.requester.display_avatar)

            if not isinstance(song, spotify.SpotifyTrack) and song.is_stream: 
                if color_code == ColorCode.NONE: 
                    self.add_field(
                        name=strings["Info.Stream.Notice.Title"], 
                        value=strings["Info.Stream.Notice.Text"], 
                        inline=True
                    )
            
            
                embed_opt['footer']['text'] = stateicon + "\n" + embed_opt['footer']['text'] 

            queuelist: str = ""

            # Upcoming song (via Suggestion)
            if guild_player_info[guild_id].music_suggestion and len(playlist.order) == 2 and playlist[1].suggested and color_code != ColorCode.Red:
                if guild_play_info[guild_id].skip:
                    queuelist += "**{}**".format(strings["Info.Suggestion.Loading"])
                else:
                    queuelist += f"**:bulb:** {playlist[1].title}"
                self.add_field(name="{}{}".format(f":hourglass: | " if guild_play_info[guild_id].skip else "", strings["Info.Upcoming"]), value=queuelist, inline=False)
            
            # Upcoming song (with single repeat on and only one song in queue)
            elif len(playlist.order) == 1 and playlist.loop_state == LoopState.PLAYLIST:
                self.add_field(name=strings["Info.Upcoming"], value="*{}*".format(strings["Info.Upcoming.Final"]), inline=False)
            
            # Upcoming song
            elif len(playlist.order) > 1 and color_code != ColorCode.Red:
                queuelist += f"**>> {playlist[1].title}**\n*by {playlist[1].requester}*\n"
                if len(playlist.order) > 2: 
                    string = strings["Info.Upcoming.Count"] \
                                .replace(r"{count}", len(playlist.order)-2)
                    queuelist += f"*{string}*"
                
                string_title = strings["Info.Upcoming.SubTitle"] \
                                .replace(r"{count}", len(playlist.order)-1)
                self.add_field(name="{} | {}".format(strings["Info.Upcoming"], string_title), value=queuelist, inline=False)

            if 'spotify' in song.uri and (color != ColorCode.Green or color != ColorCode.Red):
                self.set_thumbnail(url=song.cover)

            if (not playlist_storage.check_current_suggest_support(guild_id)) \
                and (color_code != ColorCode.Red or color_code != ColorCode.Green): #color code refer to behaviour
                    # red stands for delete information, green stands for add to queue notice
                self.add_field(
                    name="{} | {}".format(Emoji.Caution, strings["Info.Suggestion.Disabled.Title"]), 
                    value=strings["Info.Suggestion.Disabled.Text"], 
                    inline=False
                )

            # will be deleted after testing
            if song.audio_source == "bilibili":
                footer_add_bili = strings["Info.Test.Bilibili"]

            if stateicon != "": 
                footer_add_state = stateicon + "\n"
            
        embed_opt = essentials.embed_opt(f"{footer_add_bili}{footer_add_state}")

        self._footer = embed_opt


    def get_holiday_text(self, holiday: Holiday) -> str:
        strings = essentials.get_language_dict(self.lang, UIModule.InfoGenerator)

        match holiday:
            case Holiday.XmasEve:
                return " 🎄 {}".format(strings["Info.Holiday.XmasEve"])
            case Holiday.Xmas:
                return " 🎄 {}".format(strings["Info.Holiday.Xmas"])
            case Holiday.NewYearEve:
                return " 🎊 {}" \
                        .format(strings["Info.Holiday.NewYearEve"].replace(r"{year}", datetime.now().year + 1))
            case Holiday.NewYear:
                return " 🎊 {}" \
                        .format(strings["Info.Holiday.NewYear"].replace(r"{year}", datetime.now().year + 1))
            case Holiday.ChineseNewYear:
                return " 🧧 {}".format(strings["Info.Holiday.ChineseNewYear"])
            case _:
                return ""

    def get_activity_text(self, operation: Union[LeaveType, StopType], operator: discord.Member = None) -> str:
        strings = essentials.get_language_dict(self.lang, UIModule.InfoGenerator)

        match operation:
            case LeaveType.ByCommand:
                return "📤 | {}".format(strings["Info.Leave.ByCommand"])
            
            case LeaveType.ByButton:
                if operator.discriminator == "0":
                    string = strings["Info.Leave.ByButton.New"] \
                            .replace(r"{name}", operator.name)
                else:
                    string = strings["Info.Leave.ByButton.Old"] \
                            .replace(r"{name}", operator.name) \
                            .replace(r"{code}", operator.discriminator)
                
                return f"📤 | {string}"
            
            case LeaveType.ByTimeout:
                return "📤/🕗 | {}".format(strings["Info.Leave.ByTimeout"])      
            
            case StopType.ByCommand:
                return "⏹️ | {}".format(strings["Info.Stop.ByCommand"])
            
            case StopType.ByButton:
                if operator.discriminator == "0":
                    string = strings["Info.Stop.ByButton.New"] \
                            .replace(r"{name}", operator.name)
                else:
                    string = strings["Info.Stop.ByButton.Old"] \
                            .replace(r"{name}", operator.name) \
                            .replace(r"{code}", operator.discriminator)
                
                return f"⏹️ | {string}"

            case _:
                return "🕗 | {}".format(strings["Info.Done"])

    def get_playing_activity_text(self, voice_client: wavelink.Player, guild_id: int) -> str:
        strings = essentials.get_language_dict(self.lang, UIModule.InfoGenerator)
        
        if len(voice_client.channel.members) == 1 and voice_client.channel.members[0] == self.bot.user:
            return "📤/⏸️ | {}".format(strings["Info.Pause.ByIdle"])
        elif guild_play_info[guild_id].skip:
            return "⏩ | {}".format(strings["Info.Skip"])
        else:
            if voice_client.is_paused():
                return "⏸️ | {}".format(strings["Info.Pause"])
            else:
                return "▶️ | {}".format(strings["Info.Playing"])
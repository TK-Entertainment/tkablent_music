from typing import TYPE_CHECKING, Union, Optional
if TYPE_CHECKING:
    from typing import *
import discord
import copy

from ..playlist import PlaylistBase
from .info import InfoGenerator
from ..emoji import Emoji

import wavelink


class Queue:
    def __init__(self, info_generator):
        from ..ui import _sec_to_hms, embed_opt, musicbot, bot, guild_info

        self._sec_to_hms = _sec_to_hms
        self.embed_opt = embed_opt
        self.musicbot = musicbot
        self.bot = bot
        self.guild_info = guild_info
        self.info_generator: InfoGenerator = info_generator

    # Add to queue
    async def Embed_AddedToQueue(
        self,
        interaction: discord.Interaction,
        trackinfo: list[Union[wavelink.Playable, wavelink.Playlist, None]],
        requester: Optional[discord.User],
        is_search,
    ) -> None:
        # If queue has more than 2 songs, then show message when
        # user use play command
        playlist: PlaylistBase = self.musicbot._playlist[interaction.guild.id]
        if len(playlist.order) == 1:
            return
        if (len(playlist.order) > 1 and is_search) or (
            isinstance(trackinfo, list) or isinstance(trackinfo[0], wavelink.Playlist) and (len(trackinfo) > 1)
        ):
            if is_search:
                msg = f"""
            **:white_check_mark: | 搜尋成功**
            以下歌曲已加入待播清單中
            """
            else:
                if isinstance(trackinfo[0], wavelink.Playlist):
                    if (trackinfo[0].url is not None) and ("spotify" in trackinfo[0].url):
                        if trackinfo[0].type == "album":
                            type_string = "Spotify 專輯"
                        else:
                            type_string = "Spotify 播放清單"
                    else:
                        type_string = "播放清單"
                elif isinstance(trackinfo, list):
                    type_string = "播放清單"

                msg = f"""
            **:white_check_mark: | 成功加入待播清單**
            以下{type_string}已加入待播清單中
            """

            embed = self.info_generator._PlaylistInfo(trackinfo, requester)
        else:
            index = len(playlist.order) - 1

            msg = f"""
            **:white_check_mark: | 成功加入待播清單**
            以下歌曲已加入待播清單中，為第 **{len(playlist.order)-1}** 首歌
            """

            embed = self.info_generator._SongInfo(
                color_code="green", index=index, guild_id=interaction.guild.id
            )

        if (self.guild_info(interaction.guild.id).playinfo is not None) and (
            self.guild_info(interaction.guild.id).playinfo_view is not None):
            self.guild_info(
                interaction.guild.id
            ).playinfo_view.skip.emoji = Emoji.lastpage_emoji
            self.guild_info(
                interaction.guild.id
            ).playinfo_view.skip.disabled = self.guild_info(
                interaction.guild.id
            ).playinfo_view.shuffle.disabled = False
            self.guild_info(
                interaction.guild.id
            ).playinfo_view.skip.style = self.guild_info(
                interaction.guild.id
            ).playinfo_view.shuffle.style = discord.ButtonStyle.blurple
            await self.guild_info(interaction.guild.id).playinfo.edit(
                view=self.guild_info(interaction.guild.id).playinfo_view
            )

        if not interaction.response.is_done():
            await interaction.response.send_message(
                msg, embed=embed, ephemeral=True
            )
        else:
            try:
                await interaction.followup.send(msg, embed=embed, ephemeral=True)
            except:
                await interaction.channel.send(msg, embed=embed)
        try:
            await self.info_generator._UpdateSongInfo(interaction.guild.id)
        except:
            pass

    # Queue Embed Generator
    def _QueueEmbed(
        self, playlist: PlaylistBase, page: int = 0, op=None
    ) -> discord.Embed:
        embed = discord.Embed(
            title=":information_source: | 候播清單",
            description=f"以下清單為歌曲候播列表\n共 {len(playlist.order)-1} 首",
            colour=0xF2F3EE,
        )

        for i in range(1, 4):
            index = page * 3 + i
            if index == len(playlist.order):
                break
            length = self._sec_to_hms((playlist[index].length) / 1000, "symbol")
            if playlist[index].extras.suggested:
                requester = "💡推薦歌曲"
                index_text = ""
            else:
                requester = f"{playlist[index].extras.requester_name} 點歌"
                index_text = f"第 {index} 順位\n"
            embed.add_field(
                name="{}{}\n{}{}".format(
                    index_text,
                    playlist[index].title,
                    "🔴 直播 | " if playlist[index].is_stream else "",
                    requester,
                ),
                value="作者: {}{}{}".format(
                    playlist[index].author,
                    " / 歌曲時長: " if not playlist[index].is_stream else "",
                    length if not playlist[index].is_stream else "",
                ),
                inline=False,
            )

        embed_opt = copy.deepcopy(self.embed_opt)
        if op == "button":
            txt = "請點按「刪除這些訊息」來關閉\n"
        else:
            txt = ""

        if len(playlist.order) > 4:
            total_pages = (len(playlist.order) - 1) // 3
            if (len(playlist.order) - 1) % 3 != 0:
                total_pages += 1
            embed_opt["footer"]["text"] = (
                f"{txt}第 {page+1} 頁 / 共 {total_pages} 頁\n"
                + self.embed_opt["footer"]["text"]
            )
        else:
            embed_opt["footer"]["text"] = f"{txt}" + self.embed_opt["footer"]["text"]

        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **embed_opt))
        return embed

    def new_song_modal_helper(self):
        class NewSongModal(discord.ui.Modal):
            musicbot = self.musicbot

            def __init__(self, requester: Union[discord.User, discord.Member]):
                if requester.discriminator == "0":
                    requester = f"{requester.name}"
                else:
                    requester = f"{requester.name}#{requester.discriminator}"
                self.url_or_name = discord.ui.TextInput(
                    custom_id="song_url",
                    label="歌曲網址或關鍵字 (網址支援 Spotify, SoundCloud, B站(單曲))",
                    placeholder=f"此歌曲由 {requester} 點播",
                )
                super().__init__(title="🔎 | 搜尋歌曲", timeout=120)

                self.add_item(self.url_or_name)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                await self.musicbot._i_play.callback(
                    self.musicbot, interaction, self.url_or_name.value
                )

        return NewSongModal

    # Queue Listing
    async def ShowQueue(self, interaction: discord.Interaction, op=None) -> None:
        playlist: PlaylistBase = self.musicbot._playlist[interaction.guild.id]

        class QueueListing(discord.ui.View):
            QueueEmbed = self._QueueEmbed
            embed_opt = self.embed_opt
            operation = op
            guild_info = self.guild_info
            NewSongModal = self.new_song_modal_helper()

            def __init__(self, *, timeout=60):
                super().__init__(timeout=timeout)
                self.last: discord.ui.Button = self.children[0]
                self.page = 0

            @property
            def first_page_button(self) -> discord.ui.Button:
                return self.children[0]

            @property
            def left_button(self) -> discord.ui.Button:
                return self.children[1]

            @property
            def right_button(self) -> discord.ui.Button:
                return self.children[2]

            @property
            def last_page_button(self) -> discord.ui.Button:
                return self.children[3]

            @property
            def new_song_button(self) -> discord.ui.Button:
                return self.children[4]

            @property
            def total_pages(self) -> int:
                total_pages = (len(playlist.order) - 1) // 3
                if (len(playlist.order) - 1) % 3 == 0:
                    total_pages -= 1
                return total_pages

            def clear_page_control(self):
                for button in [
                    self.first_page_button,
                    self.left_button,
                    self.right_button,
                    self.last_page_button,
                ]:
                    self.remove_item(button)

            def update_button(self):
                if self.page == 0:
                    self.left_button.disabled = self.first_page_button.disabled = True
                    self.left_button.style = (
                        self.first_page_button.style
                    ) = discord.ButtonStyle.gray
                else:
                    self.left_button.disabled = self.first_page_button.disabled = False
                    self.left_button.style = (
                        self.first_page_button.style
                    ) = discord.ButtonStyle.blurple
                if self.page == self.total_pages:
                    self.right_button.disabled = self.last_page_button.disabled = True
                    self.right_button.style = (
                        self.last_page_button.style
                    ) = discord.ButtonStyle.gray
                else:
                    self.right_button.disabled = self.last_page_button.disabled = False
                    self.right_button.style = (
                        self.last_page_button.style
                    ) = discord.ButtonStyle.blurple

            @discord.ui.button(
                emoji=Emoji.firstpage_emoji, style=discord.ButtonStyle.gray, disabled=True
            )
            async def firstpage(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.page = 0
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page, self.operation)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(
                emoji=Emoji.prevpage_emoji, style=discord.ButtonStyle.gray, disabled=True
            )
            async def prevpage(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.page -= 1
                if self.page < 0:
                    self.page = 0
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page, self.operation)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(emoji=Emoji.nextpage_emoji, style=discord.ButtonStyle.blurple)
            async def nextpage(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.page += 1
                if self.page > self.total_pages:
                    self.page = self.total_pages
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page, self.operation)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(emoji=Emoji.lastpage_emoji, style=discord.ButtonStyle.blurple)
            async def lastpage(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.page = self.total_pages
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page, self.operation)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(
                emoji=Emoji.search_emoji, label="搜尋/新增歌曲", style=discord.ButtonStyle.green
            )
            async def new_song(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                await interaction.response.send_modal(
                    self.NewSongModal(interaction.user)
                )

            @discord.ui.button(emoji=Emoji.end_emoji, style=discord.ButtonStyle.danger)
            async def done(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                await interaction.message.delete()
                await interaction.response.pong()
                self.stop()

            async def on_timeout(self):
                if self.operation == "button":
                    try:
                        await interaction.edit_original_response(
                            content="時限已到，請按「關閉這些訊息」來刪掉此訊息", view=None, embed=None
                        )
                    except:
                        pass
                else:
                    await msg.delete()

        view = QueueListing()
        # if len(playlist.order) < 2:
        #     view.clear_page_control()
        #     if op == "button":
        #         view.remove_item(view.done)
        #         txt = "\n            *請點按「刪除這些訊息」來關閉此訊息*"
        #     else:
        #         txt = ""
        #     await interaction.response.send_message(
        #         f"""
        #     **:information_source: | 待播歌曲**
        #     目前沒有任何歌曲待播中
        #     *輸入 ** '{self.bot.command_prefix}play 關鍵字或網址' **可繼續點歌*{txt}
        #     """,
        #         ephemeral=(op == "button"),
        #         view=view,
        #     )
        #     msg = await interaction.original_response()
        #     return
        # else:
        embed = self._QueueEmbed(playlist, 0, op)
        if (len(playlist.order)) <= 4:
            view.clear_page_control()
        if op == "button":
            view.remove_item(view.done)

        await interaction.response.send_message(
            embed=embed, view=view, ephemeral=(op == "button")
        )
        msg = await interaction.original_response()

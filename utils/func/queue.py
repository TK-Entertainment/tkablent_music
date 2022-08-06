from typing import *
import discord
import copy

from ..player import Command
from ..playlist import PlaylistBase
from .info import InfoGenerator

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
    async def Embed_AddedToQueue(self, command: Command, trackinfo: Union[wavelink.Track, wavelink.YouTubePlaylist], requester: Optional[discord.User]) -> None:
        # If queue has more than 2 songs, then show message when
        # user use play command
        playlist: PlaylistBase = self.musicbot._playlist[command.guild.id]
        if len(playlist.order) > 1 or (isinstance(trackinfo, wavelink.YouTubePlaylist)):
            if isinstance(trackinfo, wavelink.YouTubePlaylist):
                msg = '''
                **:white_check_mark: | 成功加入待播清單**
                以下播放清單已加入待播清單中
                '''

                embed = self.info_generator._PlaylistInfo(trackinfo, requester)
            else:
                index = len(playlist.order) - 1

                msg = f'''
                **:white_check_mark: | 成功加入待播清單**
                以下歌曲已加入待播清單中，為第 **{len(playlist.order)-1}** 首歌
                '''

                embed = self.info_generator._SongInfo(color_code="green", index=index, guild_id=command.guild.id)

            if command.command_type == 'Interaction' and command.is_response() is not None and not command.is_response():        
                await command.send(msg, embed=embed)
            else:
                await command.channel.send(msg, embed=embed)

    # Queue Embed Generator
    def _QueueEmbed(self, playlist: PlaylistBase, page: int=0, op=None) -> discord.Embed:
        embed = discord.Embed(title=":information_source: | 候播清單", description=f"以下清單為歌曲候播列表\n共 {len(playlist.order)-1} 首", colour=0xF2F3EE)
        
        for i in range(1, 4):
            index = page*3+i
            if (index == len(playlist.order)): break
            length = self._sec_to_hms(playlist[index].length, "symbol")
            embed.add_field(
                name="第 {} 順位\n{}\n{}{} 點歌".format(index, playlist[index].title, "🔴 直播 | " if playlist[index].is_stream() else "", playlist[index].requester),
                value="作者: {}{}{}".format(playlist[index].author, " / 歌曲時長: " if not playlist[index].is_stream() else "", length if not playlist[index].is_stream() else ""),
                inline=False,
            )

        embed_opt = copy.deepcopy(self.embed_opt)

        if len(playlist.order) > 4:
            if op == 'button':
                txt = '請點按「刪除這些訊息」來關閉\n'
            else:
                txt = ''
            total_pages = (len(playlist.order)-1) // 3
            if (len(playlist.order)-1) % 3 != 0:
                total_pages += 1
            embed_opt['footer']['text'] = f'{txt}第 {page+1} 頁 / 共 {total_pages} 頁\n' + self.embed_opt['footer']['text']
        
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **embed_opt))
        return embed
    
    # Queue Listing
    async def ShowQueue(self, command: Union[Command, discord.Interaction], op=None) -> None:
        playlist: PlaylistBase = self.musicbot._playlist[command.guild.id]

        class QueueListing(discord.ui.View):

            QueueEmbed = self._QueueEmbed
            embed_opt = self.embed_opt
            operation = op
            guild_info = self.guild_info

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
            def total_pages(self) -> int:
                total_pages = (len(playlist.order)-1) // 3  
                return total_pages

            def update_button(self):
                if self.page == 0:
                    self.left_button.disabled = self.first_page_button.disabled = True
                    self.left_button.style = self.first_page_button.style = discord.ButtonStyle.gray
                else:
                    self.left_button.disabled = self.first_page_button.disabled = False
                    self.left_button.style = self.first_page_button.style = discord.ButtonStyle.blurple
                if self.page == self.total_pages:
                    self.right_button.disabled = self.last_page_button.disabled = True
                    self.right_button.style = self.last_page_button.style = discord.ButtonStyle.gray
                else:
                    self.right_button.disabled = self.last_page_button.disabled = False
                    self.right_button.style = self.last_page_button.style = discord.ButtonStyle.blurple

            @discord.ui.button(label='⏪', style=discord.ButtonStyle.gray, disabled=True)
            async def firstpage(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.page = 0
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page, self.operation)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='⬅️', style=discord.ButtonStyle.gray, disabled=True)
            async def prevpage(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.page -= 1
                if self.page < 0:
                    self.page = 0
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page, self.operation)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='➡️', style=discord.ButtonStyle.blurple)
            async def nextpage(self, interaction: discord.Interaction, button: discord.ui.Button):            
                self.page += 1
                if self.page > self.total_pages:
                    self.page = self.total_pages
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page, self.operation)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='⏩', style=discord.ButtonStyle.blurple)
            async def lastpage(self, interaction: discord.Interaction, button: discord.ui.Button):            
                self.page = self.total_pages
                self.update_button()
                embed = self.QueueEmbed(playlist, self.page, self.operation)
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='❎', style=discord.ButtonStyle.danger)
            async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.message.delete()
                await interaction.response.pong()
                self.stop()

            async def on_timeout(self):
                if self.operation == 'button':
                    await command.edit_original_message(content='時限已到，請按「關閉這些訊息」來刪掉此訊息', view=None, embed=None)
                else:
                    await msg.delete()
            
        if (len(playlist.order) < 2):
            if op == 'button':
                await command.response.send_message(f'''
            **:information_source: | 待播歌曲**
            目前沒有任何歌曲待播中
            *輸入 ** '{self.bot.command_prefix}play 關鍵字或網址' **可繼續點歌*
            *請點按「刪除這些訊息」來關閉此訊息*
            ''', ephemeral=True)
            else:
                await command.send(f'''
            **:information_source: | 待播歌曲**
            目前沒有任何歌曲待播中
            *輸入 ** '{self.bot.command_prefix}play 關鍵字或網址' **可繼續點歌*
            ''')
            return
        else:
            embed = self._QueueEmbed(playlist, 0, op)
            if not (len(playlist.order)) <= 4:
                view = QueueListing()
                if op == 'button':
                    view.remove_item(view.done)
                    await command.response.send_message(embed=embed, view=view, ephemeral=True)
                else:
                    msg = await command.send(embed=embed, view=view)
            else:
                if op == 'button':
                    await command.response.send_message(embed=embed, ephemeral=True)
                else:
                    await command.send(embed=embed)
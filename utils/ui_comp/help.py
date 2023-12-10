from typing import *
import discord
from discord.ext import commands

from ..ui import rescue_emoji


class Help:
    def __init__(self):
        from ..ui import bot, embed_opt

        self.bot: commands.Bot = bot
        self.embed_opt: dict = embed_opt

    def _HelpEmbedBasic(self) -> discord.Embed:
        embed = discord.Embed(
            title=":regional_indicator_q: | 指令說明 | 基本指令",
            description="若遇到錯誤可以先閱讀訊息所提示的方法來排錯喔",
            colour=0xF2F3EE,
        )
        embed.add_field(name="/help", value="你目前就正在用這個喔，輸入會列出指令說明", inline=False)
        embed.add_field(
            name="/join",
            value="將機器人加入到您目前所在的語音頻道\n**【！】若遇到錯誤 JOINFAIL**\n*可能是您沒有加入到任一語音頻道中，或是機器人無權限加入該頻道導致*",
            inline=False,
        )
        embed.add_field(
            name="/leave",
            value="使機器人離開其所在的語音頻道\n**【！】若遇到錯誤 LEAVEFAIL**\n*可能是機器人並沒有加入到任一語音頻道中導致*",
            inline=False,
        )
        return embed

    def _HelpEmbedPlayback(self, page: int) -> discord.Embed:
        embed = discord.Embed(
            title=":regional_indicator_q: | 指令說明 | 播放相關指令",
            description="若遇到錯誤可以先閱讀訊息所提示的方法來排錯喔",
            colour=0xF2F3EE,
        )
        if page == 1:
            embed.add_field(name="/playwith", value="管理對於混合式連結的機器人預設動作", inline=False)
            embed.add_field(
                name="/play [URL/關鍵字]",
                value="開始播放指定歌曲(輸入關鍵字會啟動搜尋)\n**支援網址點歌平台:**\nSoundcloud / Spotify / Bilibili (目前僅支援單曲)\n**【！】若遇到錯誤 SEARCH_OR_PLAYING_FAILED**\n可能是您提供的網址有誤、該影片暫時不可用、關鍵字搜尋不到任何影片或機器人暫時出現問題導致",
                inline=False,
            )
            embed.add_field(
                name="/np",
                value="顯示目前播放歌曲資訊 (如果控制面板被刷掉可以用這個ww)\n*【注意】輸入後，原控制面板會清除*\n**【！】若輸入後沒反應**\n*可能因目前沒有播放歌曲導致*",
                inline=False,
            )
            embed.add_field(
                name="/pause",
                value="暫停目前歌曲播放\n**【！】若遇到錯誤 PAUSEFAIL**\n*可能目前沒在播放歌曲，或目前歌曲已經被暫停導致*",
                inline=False,
            )
            embed.add_field(
                name="/resume",
                value="繼續播放已暫停的歌曲\n**【！】若遇到錯誤 RESUMEFAIL**\n*可能目前沒在播放歌曲，或目前歌曲未被暫停導致*",
                inline=False,
            )
            embed.add_field(
                name="/skip",
                value="跳過目前的歌曲\n**【！】若遇到錯誤 SKIPFAIL**\n*可能目前沒在播放歌曲導致*",
                inline=False,
            )
        elif page == 2:
            embed.add_field(
                name="/stop",
                value="停止歌曲並清除所有待播清單中的歌曲\n**【！】若遇到錯誤 STOPFAIL**\n*可能因目前沒在播放歌曲導致*",
                inline=False,
            )
            embed.add_field(
                name="/seek [秒/時間戳]",
                value="快轉至指定時間\n*參數支援: 秒 (如: 2) / 時間戳 (如: 0:02)*\n**【！】若遇到錯誤 SEEKFAIL**\n*可能因輸入的跳轉時間無效(格式錯誤)或目前沒在播放歌曲導致*",
                inline=False,
            )
            embed.add_field(
                name="/restart",
                value="重新播放目前歌曲\n**【！】若遇到錯誤 REPLAYFAIL**\n*可能因目前沒在播放歌曲導致*",
                inline=False,
            )
            embed.add_field(
                name="/loop [次數]",
                value="切換單曲循環開關 (輸入次數則可指定單曲播放幾次)\n**【！】若遇到錯誤 LOOPFAIL_SIG**\n*可能因指定的重複次數無效 (小於0一類的) 或目前沒在播放歌曲導致*",
                inline=False,
            )
            embed.add_field(name="/wholeloop", value="切換全待播清單循環開關", inline=False)
        return embed

    def _HelpEmbedQueue(self) -> discord.Embed:
        embed = discord.Embed(
            title=":regional_indicator_q: | 指令說明 | 待播清單相關指令",
            description="若遇到錯誤可以先閱讀訊息所提示的方法來排錯喔",
            colour=0xF2F3EE,
        )
        embed.add_field(name="/queue", value="顯示待播歌曲列表", inline=False)
        embed.add_field(
            name="/shuffle",
            value="隨機排列待播歌曲列表\n**【！】若遇到錯誤 SHUFFLEFAIL**\n*可能是因目前待播清單無歌曲導致*",
            inline=False,
        )
        embed.add_field(
            name="/remove [順位數]",
            value="移除指定待播歌曲 (順位數可以依 /queue 顯示的代號輸入)\n**【注意】建議歌曲是不能移除的，嘗試移除會導致錯誤 REMOVEFAIL**\n**【！】若遇到錯誤 REMOVEFAIL**\n*可能是因輸入的順位數無效 (根本沒這首歌) 或目前待播清單無歌曲導致*",
            inline=False,
        )
        embed.add_field(
            name="/swap [順位數1] [順位數2]",
            value="交換指定待播歌曲順序 ([順位數1] <-> [順位數2])\n**【注意】建議歌曲是不能交換的，嘗試交換會導致錯誤 SWAPFAIL**\n**【！】若遇到錯誤 SWAPFAIL**\n*可能是因輸入的順位數無效 (根本沒這首歌) 或目前待播清單無歌曲導致*",
            inline=False,
        )
        embed.add_field(
            name="/move [原順位數] [目標順位數]",
            value="移動指定待播歌曲至指定順序 ([原順位數] -> [目標順位數])\n**【注意】建議歌曲是不能移動的，嘗試移動會導致錯誤 MOVEFAIL**\n**【！】若遇到錯誤 MOVEFAIL**\n*可能是因輸入的順位數無效 (根本沒這首歌) 或目前待播清單無歌曲導致*",
            inline=False,
        )
        return embed

    async def Help(self, interaction: discord.Interaction) -> None:
        class Help(discord.ui.View):
            HelpEmbedBasic = self._HelpEmbedBasic
            HelpEmbedPlayback = self._HelpEmbedPlayback
            HelpEmbedQueue = self._HelpEmbedQueue
            embed_opt = self.embed_opt

            def __init__(self, *, timeout=60):
                super().__init__(timeout=timeout)
                self.last: discord.ui.Button = self.children[0]
                Button = discord.ui.Button(
                    emoji=rescue_emoji,
                    style=discord.ButtonStyle.link,
                    url="https://discord.gg/9qrpGh4e7V",
                    label="支援群組",
                    row=1,
                )
                self.add_item(Button)

            def toggle(self, button: discord.ui.Button):
                self.last.disabled = False
                self.last.style = discord.ButtonStyle.blurple
                button.disabled = True
                button.style = discord.ButtonStyle.gray
                self.last = button

            @discord.ui.button(
                label="基本指令", style=discord.ButtonStyle.gray, disabled=True
            )
            async def basic(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.toggle(button)
                embed = self.HelpEmbedBasic()
                embed = discord.Embed.from_dict(
                    dict(**embed.to_dict(), **self.embed_opt)
                )
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label="播放相關 (第一頁)", style=discord.ButtonStyle.blurple)
            async def playback_p1(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.toggle(button)
                embed = self.HelpEmbedPlayback(1)
                embed = discord.Embed.from_dict(
                    dict(**embed.to_dict(), **self.embed_opt)
                )
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label="播放相關 (第二頁)", style=discord.ButtonStyle.blurple)
            async def playback_p2(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.toggle(button)
                embed = self.HelpEmbedPlayback(2)
                embed = discord.Embed.from_dict(
                    dict(**embed.to_dict(), **self.embed_opt)
                )
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label="待播清單相關", style=discord.ButtonStyle.blurple)
            async def queue(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.toggle(button)
                embed = self.HelpEmbedQueue()
                embed = discord.Embed.from_dict(
                    dict(**embed.to_dict(), **self.embed_opt)
                )
                await interaction.response.edit_message(embed=embed, view=view)

            async def on_timeout(self):
                self.clear_items()
                await msg.edit(content="時限已到，請按「關閉這些訊息」來刪掉此訊息", view=None)

        embed = self._HelpEmbedBasic()
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
        view = Help()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        msg = await interaction.original_response()

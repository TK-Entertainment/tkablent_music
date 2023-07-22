from typing import *
import discord
from discord.ext import commands

from ..ui import rescue_emoji

class Help:
    def __init__(self):
        from ..ui import bot, embed_opt

        self.bot: commands.Bot = bot
        self.embed_opt: dict = embed_opt



    async def Help(self, interaction: discord.Interaction) -> None:

        class Help(discord.ui.View):

            HelpEmbedBasic = self._HelpEmbedBasic
            HelpEmbedPlayback = self._HelpEmbedPlayback
            HelpEmbedQueue = self._HelpEmbedQueue
            embed_opt = self.embed_opt

            def __init__(self, *, timeout=60):
                super().__init__(timeout=timeout)
                self.last: discord.ui.Button = self.children[0]
                Button = discord.ui.Button(emoji=rescue_emoji, style=discord.ButtonStyle.link, url="https://discord.gg/9qrpGh4e7V", label="支援群組", row=1)
                self.add_item(Button)

            def toggle(self, button: discord.ui.Button):
                self.last.disabled = False
                self.last.style = discord.ButtonStyle.blurple
                button.disabled = True
                button.style = discord.ButtonStyle.gray
                self.last = button

            @discord.ui.button(label='基本指令', style=discord.ButtonStyle.gray, disabled=True)
            async def basic(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.toggle(button)
                embed = self.HelpEmbedBasic()
                embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)
            
            @discord.ui.button(label='播放相關 (第一頁)', style=discord.ButtonStyle.blurple)
            async def playback_p1(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.toggle(button)
                embed = self.HelpEmbedPlayback(1)
                embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='播放相關 (第二頁)', style=discord.ButtonStyle.blurple)
            async def playback_p2(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.toggle(button)
                embed = self.HelpEmbedPlayback(2)
                embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='待播清單相關', style=discord.ButtonStyle.blurple)
            async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.toggle(button)
                embed = self.HelpEmbedQueue()
                embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)

            async def on_timeout(self):
                self.clear_items()
                await msg.edit(content="時限已到，請按「關閉這些訊息」來刪掉此訊息", view=None)

        embed = self._HelpEmbedBasic()
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
        view = Help()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        msg = await interaction.original_response()
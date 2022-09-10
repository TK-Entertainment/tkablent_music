from typing import *
import discord
from discord.ext import commands
from ..command import Command
from .misc import end_emoji

class Help:
    def __init__(self, bot, embed_opt, **kwargs):
        self.bot: commands.Bot = bot
        self.embed_opt: dict = embed_opt
        super().__init__(embed_opt=embed_opt, **kwargs)
        print("早安3")

    def _HelpEmbedBasic(self) -> discord.Embed:
        return discord.Embed(title=":regional_indicator_q: | 指令說明 | 基本指令", description=f'''
        {self.bot.command_prefix}help | 顯示此提示框，列出指令說明
        {self.bot.command_prefix}join | 將機器人加入到您目前所在的語音頻道
        {self.bot.command_prefix}leave | 使機器人離開其所在的語音頻道
        ''', colour=0xF2F3EE)
    def _HelpEmbedPlayback(self) -> discord.Embed:
        return discord.Embed(title=":regional_indicator_q: | 指令說明 | 播放相關指令", description=f'''
        {self.bot.command_prefix}play [URL/名稱] | 開始播放指定歌曲(輸入名稱會啟動搜尋)
        {self.bot.command_prefix}np | 顯示目前播放歌曲資訊
        {self.bot.command_prefix}pause | 暫停歌曲播放
        {self.bot.command_prefix}resume | 續播歌曲
        {self.bot.command_prefix}skip | 跳過目前歌曲
        {self.bot.command_prefix}stop | 停止歌曲並清除所有待播清單中的歌曲
        {self.bot.command_prefix}seek [秒/時間戳] | 快轉至指定時間 (時間戳格式 ex.00:04)
        {self.bot.command_prefix}restart | 重新播放目前歌曲
        {self.bot.command_prefix}loop | 切換單曲循環開關
        {self.bot.command_prefix}wholeloop | 切換全待播清單循環開關
        ''', colour=0xF2F3EE)
    def _HelpEmbedQueue(self) -> discord.Embed:
        return discord.Embed(title=":regional_indicator_q: | 指令說明 | 待播清單相關指令", description=f'''
        {self.bot.command_prefix}queue | 顯示待播歌曲列表
        {self.bot.command_prefix}remove [順位數] | 移除指定待播歌曲
        {self.bot.command_prefix}swap [順位數1] [順位數2] | 交換指定待播歌曲順序
        {self.bot.command_prefix}move [原順位數] [目標順位數] | 移動指定待播歌曲至指定順序
        ''', colour=0xF2F3EE)

    async def Help(self, command: Command) -> None:

        class Help(discord.ui.View):

            HelpEmbedBasic = self._HelpEmbedBasic
            HelpEmbedPlayback = self._HelpEmbedPlayback
            HelpEmbedQueue = self._HelpEmbedQueue
            embed_opt = self.embed_opt

            def __init__(self, *, timeout=60):
                super().__init__(timeout=timeout)
                self.last: discord.ui.Button = self.children[0]

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
            
            @discord.ui.button(label='播放相關', style=discord.ButtonStyle.blurple)
            async def playback(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.toggle(button)
                embed = self.HelpEmbedPlayback()
                embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(label='待播清單相關', style=discord.ButtonStyle.blurple)
            async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.toggle(button)
                embed = self.HelpEmbedQueue()
                embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
                await interaction.response.edit_message(embed=embed, view=view)

            @discord.ui.button(emoji=end_emoji, style=discord.ButtonStyle.danger)
            async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.pong()
                await interaction.message.delete()
                self.stop()

            async def on_timeout(self):
                self.clear_items()
                await msg.edit(view=self)
                await msg.add_reaction('🛑')

        embed = self._HelpEmbedBasic()
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
        view = Help()
        msg = await command.send(embed=embed, view=view)
import discord

from ..Generic.Emojis import Emoji
from ..Generic.GroupButton import GroupButton
from ..Generic.Essentials import essentials

class Help(discord.ui.View):
    def __init__(self, *, timeout=60, msg: discord.InteractionMessage = None):
        if isinstance(msg, None):
            raise ValueError("msg must be discord.InteractionMessage, but given None")
        
        super().__init__(timeout=timeout)
        self.last: discord.ui.Button = self.children[0]
        self.msg: discord.InteractionMessage = msg
        self.add_item(GroupButton())

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
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **essentials.embed_opt()))
        await interaction.response.edit_message(embed=embed, view=self)
        self.msg = await interaction.original_response()
    
    @discord.ui.button(label='播放相關 (第一頁)', style=discord.ButtonStyle.blurple)
    async def playback_p1(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle(button)
        embed = self.HelpEmbedPlayback(1)
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **essentials.embed_opt()))
        await interaction.response.edit_message(embed=embed, view=self)
        self.msg = await interaction.original_response()

    @discord.ui.button(label='播放相關 (第二頁)', style=discord.ButtonStyle.blurple)
    async def playback_p2(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle(button)
        embed = self.HelpEmbedPlayback(2)
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **essentials.embed_opt()))
        await interaction.response.edit_message(embed=embed, view=self)
        self.msg = await interaction.original_response()

    @discord.ui.button(label='待播清單相關', style=discord.ButtonStyle.blurple)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle(button)
        embed = self.HelpEmbedQueue()
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **essentials.embed_opt()))
        await interaction.response.edit_message(embed=embed, view=self)
        self.msg = await interaction.original_response()

    async def on_timeout(self):
        self.clear_items()
        await self.msg.edit(content="時限已到，請按「關閉這些訊息」來刪掉此訊息", view=None)
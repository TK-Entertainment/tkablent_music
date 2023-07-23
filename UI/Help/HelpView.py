import discord

from Generic.GroupButton import GroupButton
from Generic.Essentials import essentials
from Generic.Enums import Language, UIModule
from .HelpEmbed import HelpEmbed
from .HelpEnums import HelpEmbedStrings

class Help(discord.ui.View):
    def __init__(self, *, timeout=60, msg: discord.InteractionMessage = None, lang: Language=Language.zh_tw):
        if isinstance(msg, None):
            raise ValueError("msg must be discord.InteractionMessage, but given None")
        
        strings = essentials.get_language_dict(lang, UIModule.Help)

        super().__init__(timeout=timeout)
        self.last: discord.ui.Button = self.children[0]
        self.msg: discord.InteractionMessage = msg
        self.lang = lang

        self.add_item(GroupButton(lang))
        self.basic.label = strings["Help.Basic.Button"]
        self.playback_p1.label = strings["Help.Playback_1.Button"]
        self.playback_p2.label = strings["Help.Playback_2.Button"]
        self.queue.label = strings["Help.Queue.Button"]

    def toggle(self, button: discord.ui.Button):
        self.last.disabled = False
        self.last.style = discord.ButtonStyle.blurple
        button.disabled = True
        button.style = discord.ButtonStyle.gray
        self.last = button

    @discord.ui.button(label='基本指令', style=discord.ButtonStyle.gray, disabled=True)
    async def basic(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle(button)
        embed = HelpEmbed(HelpEmbedStrings.Basic, self.lang)
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **essentials.embed_opt()))
        await interaction.response.edit_message(embed=embed, view=self)
        self.msg = await interaction.original_response()
    
    @discord.ui.button(label='播放相關 (第一頁)', style=discord.ButtonStyle.blurple)
    async def playback_p1(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle(button)
        embed = HelpEmbed(HelpEmbedStrings.Playback_1, self.lang)
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **essentials.embed_opt()))
        await interaction.response.edit_message(embed=embed, view=self)
        self.msg = await interaction.original_response()

    @discord.ui.button(label='播放相關 (第二頁)', style=discord.ButtonStyle.blurple)
    async def playback_p2(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle(button)
        embed = HelpEmbed(HelpEmbedStrings.Playback_2, self.lang)
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **essentials.embed_opt()))
        await interaction.response.edit_message(embed=embed, view=self)
        self.msg = await interaction.original_response()

    @discord.ui.button(label='待播清單相關', style=discord.ButtonStyle.blurple)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle(button)
        embed = HelpEmbed(HelpEmbedStrings.Queue, self.lang)
        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **essentials.embed_opt()))
        await interaction.response.edit_message(embed=embed, view=self)
        self.msg = await interaction.original_response()

    async def on_timeout(self):
        self.clear_items()
        await self.msg.edit(content="時限已到，請按「關閉這些訊息」來刪掉此訊息", view=None)
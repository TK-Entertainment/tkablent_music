import discord
import os
import json

from UI.Generic.Emojis import Emoji
from UI.Generic.Enums import Language, UIModule
from UI.Generic.Essentials import essentials

class GroupButton_View(discord.ui.View):
    def __init__(self, lang: Language):
        super().__init__(timeout=None)

        label = essentials.get_language_dict(lang, UIModule.Misc)["GroupButton.label"]

        Button = discord.ui.Button(
            emoji=Emoji.Rescue,
            style=discord.ButtonStyle.link, 
            url="https://discord.gg/9qrpGh4e7V", 
            label=label
        )
        
        self.add_item(Button)

class GroupButton(discord.ui.Button):
    def __init__(self, lang: Language):
        label = essentials.get_language_dict(lang, UIModule.Misc)["GroupButton.label"]

        super().__init__(
            emoji=Emoji.Rescue,
            style=discord.ButtonStyle.link, 
            url="https://discord.gg/9qrpGh4e7V", 
            label=label
        )
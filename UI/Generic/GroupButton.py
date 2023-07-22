import discord

from .Emojis import Emoji

class GroupButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        Button = discord.ui.Button(
            emoji=Emoji.Rescue,
            style=discord.ButtonStyle.link, 
            url="https://discord.gg/9qrpGh4e7V", 
            label="支援群組"
        )
        
        self.add_item(Button)
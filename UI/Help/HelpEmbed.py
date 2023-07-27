import discord

from UI.Help.HelpEnums import HelpEmbedStrings
from UI.Generic.Enums import Language, UIModule
from UI.Generic.Essentials import essentials

class HelpEmbed(discord.Embed):
    def __init__(self, type: HelpEmbedStrings, lang: Language):
        strings = essentials.get_language_dict(lang, UIModule.Help)
        
        title = strings["Help.Title"]
        subtitle = type.value["title"]
        description = strings["Help.Description"]

        super().__init__(
            title=f":regional_indicator_q: | {title} | {subtitle}", 
            description=description, 
            colour=0xF2F3EE
        )
        
        for cmd, desc in type.value["texts"].items():
            self.add_field(name=cmd, value=desc, inline=False)
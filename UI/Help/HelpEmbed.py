import discord

from ..Misc.Enums import HelpEmbedStrings

class HelpEmbed(discord.Embed):
    def __init__(self, type: HelpEmbedStrings):
        title = type.value["title"]
        super().__init__(title=f":regional_indicator_q: | 指令說明 | {title}", description="若遇到錯誤可以先閱讀訊息所提示的方法來排錯喔", colour=0xF2F3EE)
        
        for cmd, desc in type.value["texts"]:
            self.add_field(name=cmd, value=desc, inline=False)
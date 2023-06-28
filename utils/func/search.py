from .exception_handler import ExceptionHandler
import discord

class Search:
    def __init__(self, exception_handler):
        self.exception_handler: ExceptionHandler = exception_handler

    async def YoutubeFuckedUp(self, interaction: discord.Interaction):
        msg = f'''
            **:no_entry: | 很遺憾地告訴你...**
            因應 Discord 新政策
            您摯愛的點歌方式 — **Youtube 連結** 已經*寄*了
            
            但請放心，您還是能用關鍵字去搜尋音樂 (我們有找到第三方提供者)
            對 Spotify 以及 Soundcloud 的連結還是支援的喔~

            *只能說，全世界的版權意識都慢慢上來了呢ww*

            **迷因、幹話、美好的事物
            為平淡的生活增添更多色彩
            
            TK Entertainment**
                '''
        await interaction.response.send_message(msg, ephemeral=True)

    async def SearchInProgress(self, interaction: discord.Interaction):
        msg = f'''
            **<a:Loading:1011280276325924915> | 正在載入音樂...**
            大量 Spotify 歌曲會載入較慢...
            目前機器人正在載入音樂，請稍等片刻
            當音樂完成載入時，會顯示通知~
            *你可以按下「刪除這些訊息」來關閉這個訊息*
                '''

        await interaction.edit_original_response(content=msg)
        return interaction.original_response()

    async def SearchFailed(self, interaction: discord.Interaction, url) -> None:
        await self.exception_handler._MusicExceptionHandler(interaction, None, url)
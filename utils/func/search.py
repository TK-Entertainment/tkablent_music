from ..player import Command
from .exception_handler import ExceptionHandler

class Search:
    def __init__(self, exception_handler):
        self.exception_handler: ExceptionHandler = exception_handler

    async def YoutubeFuckedUp(self, command: Command):
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
        if command.command_type == 'Interaction':
            await command.send(msg, ephemeral=True)
        else:
            await command.send(msg)

    async def SearchInProgress(self, command: Command):
        if command.command_type == 'Interaction':
            notif = "\n            *你可以按下「刪除這些訊息」來關閉這個訊息*"
        else:
            notif = ''
        msg = f'''
            **<a:Loading:1011280276325924915> | 正在載入音樂...**
            大量 Spotify 歌曲會載入較慢...
            目前機器人正在載入音樂，請稍等片刻
            當音樂完成載入時，會顯示通知~{notif}
                '''
        if command.command_type == 'Interaction':
            await command.edit_response(content=msg)
            return command.original_response()
        else:
            return await command.send(msg)

    async def SearchFailed(self, command: Command, url) -> None:
        await self.exception_handler._MusicExceptionHandler(command, None, url)
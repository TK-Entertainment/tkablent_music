from ..command import Command
from .exception_handler import ExceptionHandler

class Search(ExceptionHandler): # inherit ExceptionHandler and UIBase
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
            await command.send(msg, ephemeral=True)
            return None
        else:
            return await command.send(msg)

    async def SearchFailed(self, command: Command, url) -> None:
        await self._MusicExceptionHandler(command, None, url)
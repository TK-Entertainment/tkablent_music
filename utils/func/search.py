from ..player import Command
from .exception_handler import ExceptionHandler

class Search:
    def __init__(self, exception_handler):
        self.exception_handler: ExceptionHandler = exception_handler

    async def SearchFailed(self, command: Command, url) -> None:
        await self.exception_handler._MusicExceptionHandler(command, None, url)
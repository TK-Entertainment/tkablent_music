from .misc import _generate_embed_option
from .base import UIBase
from .info import InfoGenerator
from .exception_handler import ExceptionHandler
from .help import Help
from .join import Join
from .stage import Stage
from .leave import Leave
from .search import Search
from .queue import Queue
from .queue_control import QueueControl
from .player_control import PlayerControl

class UI(PlayerControl, QueueControl, Help, Join, Leave, Search):
    def __init__(self, music_bot, botversion):
        super().__init__(
            musicbot = music_bot, 
            botversion = botversion, 
            embed_opt = _generate_embed_option(music_bot.bot, botversion),
            bot = music_bot.bot
        )

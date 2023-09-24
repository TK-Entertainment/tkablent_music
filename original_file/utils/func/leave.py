from typing import *
from discord.ext import commands
import discord
import asyncio

from .exception_handler import ExceptionHandler
from .info import InfoGenerator
from ..ui import LeaveType

class Leave:
    def __init__(self, exception_handler, info_generator):
        from ..ui import guild_info, bot, musicbot

        self.guild_info = guild_info
        self.exception_handler: ExceptionHandler = exception_handler
        self.info_generator: InfoGenerator = info_generator
        self.bot = bot
        self.musicbot = musicbot


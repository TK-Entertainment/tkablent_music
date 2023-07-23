from typing import *
import discord
from discord.ext import commands

from ..ui import rescue_emoji

class Help:
    def __init__(self):
        from ..ui import bot, embed_opt

        self.bot: commands.Bot = bot
        self.embed_opt: dict = embed_opt

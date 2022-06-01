bot_version = 'LOCAL DEVELOPMENT'

from typing import *
import os, dotenv, sys

import disnake
from disnake.ext import commands

print(f'''
Current Version
{sys.version}
''')

dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN')

presence = disnake.Game(name='播放音樂 | $play')
intents = disnake.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None, activity=presence, status=disnake.Status.online)

from utils import *

bot.add_cog(MusicBot(bot))

try:
    bot.run(TOKEN)

except AttributeError:
    print(f'''
    =========================================
    Codename TKablent | Version Alpha
    Copyright 2022-present @ TK Entertainment
    Shared under CC-NC-SS-4.0 license
    =========================================
    
    Discord Bot TOKEN | Invaild 無效

    我們在準備您的機器人時發生了一點問題
    We encountered some problem when the bot is getting ready
    
    似乎您提供在 .env 檔案中的 TOKEN 是無效的
    請確認您已在 .env 檔案中輸入有效且完整的 TOKEN
    It looks like your TOKEN is invaild
    Please make sure that your Discord Bot TOKEN is already in .env file
    and it's a VAILD TOKEN.
    ''')
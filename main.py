from typing import *
import os, dotenv, sys

import discord
from discord.ext import commands
import wavelink
import atexit

print(f'''
Current Version
{sys.version}
''')

production = False

if production:
    prefix = '$'
    status = discord.Status.online
    production_status = 'ce' # ce for cutting edge, s for stable
    bot_version = f'20220813-{production_status}'
else:
    prefix = '%'
    status = discord.Status.dnd
    branch = 'master'
    bot_version = f'LOCAL DEVELOPMENT / {branch} Branch'

dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN')
HOST = os.getenv('WAVELINK_HOST')
PORT = os.getenv('WAVELINK_PORT')
PASSWORD = os.getenv('WAVELINK_PWD')

presence = discord.Game(name='播放音樂 | $play')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None, activity=presence, status=status)

from utils import *

def on_exit():
    cog: MusicCog = bot.cogs['MusicCog']

    node: wavelink.Node = cog.playnode
    for player in node.players:
        player.disconnect()
    node.disconnect()

@bot.event
async def on_ready():
    await bot.add_cog(MusicCog(bot, bot_version))
    await bot.tree.sync()

    cog: MusicCog = bot.cogs['MusicCog']
    await cog.resolve_ui()
    node: wavelink.Node = await cog._start_daemon(bot, HOST, PORT, PASSWORD)
    cog.playnode = node

    atexit.register(on_exit)
    print(f'''
        =========================================
        Codename TKablent | Version Alpha
        Copyright 2022-present @ TK Entertainment
        Shared under CC-NC-SS-4.0 license
        =========================================

        Discord Bot TOKEN | Vaild 有效

        If there is any problem, open an Issue with log
        else no any response or answer

        If there isn't any exception under this message,
        That means bot is online without any problem.
        若此訊息下方沒有任何錯誤訊息
        即代表此機器人已成功開機
    ''')

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f'''
        Wavelink 音樂處理伺服器已準備完畢

        伺服器名稱: {node.identifier}
    ''')

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
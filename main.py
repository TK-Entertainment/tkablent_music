import os, dotenv, sys, asyncio

import discord
from discord.ext import commands
import wavelink

print(
f""" 
Current Version
{sys.version}
"""
)

production = True
prefix = "/"
branch = "master"

if production:
    status = discord.Status.online
    production_status = "s"  # ce for cutting edge, s for stable
    test_subject = "wl3.0_test"
    bot_version = "m.20240318.3{}-{}".format(f".{test_subject}" if production_status != "s" else "", production_status)
else:
    status = discord.Status.dnd
    bot_version = f"LOCAL DEVELOPMENT / {branch} Branch\nMusic Function"

dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = False
bot = commands.AutoShardedBot(
    command_prefix=prefix, intents=intents, help_command=None, status=status
)

from music_comp import *

precenses = [
    discord.Game(f"需要幫助? | {bot.command_prefix}help"),
    discord.Game(f"來點音樂? | {bot.command_prefix}play"),
    discord.Game("迷因、幹話、美好的事物"),
    discord.Game("為平淡的生活增添更多色彩"),
    discord.Game(f"{bot_version}"),
]


async def precense_update():
    while True:
        for precense in precenses:
            await bot.change_presence(activity=precense)
            await asyncio.sleep(10)


async def count_total():
    total_count = 0
    for guild in bot.guilds:
        total_count += guild.member_count
    print(
        f"[Statistics] Bot is now serving {total_count} users in {len(bot.guilds)} guilds."
    )


@bot.event
async def on_ready():
    bot.loop.create_task(precense_update())
    bot.loop.create_task(count_total())
    await bot.add_cog(MusicCog(bot, bot_version))
    await bot.add_cog(HelperCog(bot))
    await bot.tree.sync()

    cog: MusicCog = bot.cogs["MusicCog"]
    await cog.post_boot()
    await cog._create_daemon()

    print(
        f"""
        =========================================
        Codename TKablent | Branch {branch}
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
    """
    )


@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):
    print(
        f"""
        Wavelink 音樂處理伺服器已準備完畢

        伺服器名稱: {payload.node.identifier}
    """
    )


try:
    bot.run(TOKEN)
except AttributeError:
    print(
        f"""
    =========================================
    Codename TKablent | Branch {branch}
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
    """
    )

import os, dotenv, sys, asyncio

import discord
from discord.ext import commands
import wavelink
import uvloop
import sentry_sdk
from sentry_sdk import capture_exception
import logging

print(
f""" 
Current Version
{sys.version}
"""
)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

production = True
prefix = "/"
branch = "master"

if production:
    production_status = "s"  # ce for cutting edge, s for stable
    test_subject = "wl3.0_test"
    bot_version = "m.20240318.5.p11{}-{}".format(f".{test_subject}" if production_status != "s" else "", production_status)
    print(os.getenv("SENTRY_DSN"))
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        _experiments={
            "continuous_profiling_auto_start": True,
        },
    )
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s : [%(levelname)s] %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
else:
    bot_version = f"LOCAL DEVELOPMENT / {branch} Branch\nMusic Function"

dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_COUNT = int(os.getenv("GUILD_COUNT", 0))

intents = discord.Intents.default()
intents.message_content = False

bot = commands.AutoShardedBot(
    command_prefix=prefix, intents=intents, help_command=None, status=discord.Status.dnd, activity=discord.Game("正在開機，請稍候再輸入指令"), shard_count=(GUILD_COUNT // 150) + 1
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
            try:
                await bot.change_presence(activity=precense)
            except Exception as e:
                logging.warning("Failed to update precense: {e}")
            await asyncio.sleep(10)

async def count_total():
    total_count = 0
    for guild in bot.guilds:
        total_count += guild.member_count
    logging.info(
        f"[Statistics] Bot is now serving {total_count} users in {len(bot.guilds)} guilds."
    )


@bot.event
async def on_ready():
    allowed_guilds = list(map(int, os.getenv("ALLOWED_GUILDS").split(",")))
    bot.loop.create_task(count_total())
    await bot.add_cog(MusicCog(bot, bot_version))
    bot.tree.add_command(HelperCog(bot), override=True)
    await bot.tree.sync()

    for guild_id in allowed_guilds:
        await bot.tree.sync(guild=discord.Object(id=guild_id))

    cog: MusicCog = bot.cogs["MusicCog"]
    await cog.post_boot()
    await cog._create_daemon()

    dotenv.set_key(".env", "GUILD_COUNT", str(len(bot.guilds)))

    logging.info("Bot is ready to serve.")
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
    await bot.change_presence(activity=discord.Game(f"開機完成owo | {bot.command_prefix}help"))
    bot.status = discord.Status.online
    await asyncio.sleep(5)
    bot.loop.create_task(precense_update())


@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):
    logging.info(
        f"""
        Wavelink 音樂處理伺服器已準備完畢

        伺服器名稱: {payload.node.identifier}
    """
    )

try:
    bot.run(TOKEN)
    del TOKEN
    del GUILD_COUNT
except AttributeError:
    logging.error("Bot failed to boot, invalid TOKEN")
    capture_exception(AttributeError)
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

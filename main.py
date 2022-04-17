bot_version = 'LOCAL DEVELOPMENT'

from typing import *
import os, dotenv, sys, gc

import disnake
from disnake.ext import commands

if os.name != "nt":
    import uvloop
    uvloop.install()

print(f'''
Current Version
{sys.version}
''')

dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = disnake.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

from music import *
INF = int(1e18)

class Router(commands.Cog):
    '''a router to fetch the right musicbot token from a guild request'''
 
    bot: commands.Bot
    router: Dict[int, MusicBot]
    ui: UI

    def __init__(self, bot):
        commands.Cog.__init__(self)
        self.bot: commands.Bot = bot
        self.router: Dict[int, MusicBot] = {}
        self.ui = UI(bot_version)
    
    @commands.command(name='join')
    async def join(self, ctx: commands.Context, jointype=None):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].join(ctx, jointype)

    @commands.command(name='leave')
    async def leave(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].leave(ctx)
        del self.router[ctx.guild.id]
        gc.collect()
        
    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx: commands.Context, *url):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].play(ctx, *url)

    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].pause(ctx)

    @commands.command(name='resume')
    async def resume(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].resume(ctx)

    @commands.command(name='skip')
    async def skip(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].skip(ctx)

    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].stop(ctx)

    @commands.command(name="mute", aliases=['quiet', 'shutup'])
    async def mute(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].mute(ctx)

    @commands.command(name='volume')
    async def volume(self, ctx: commands.Context, percent: Union[float, str]=None, unmute: bool=False):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].volume(ctx, percent, unmute)

    @commands.command(name='seek')
    async def seek(self, ctx: commands.Context, timestamp: Union[float, str]):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].seek(ctx, timestamp)

    @commands.command(name='restart', aliases=['replay'])
    async def restart(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].restart(ctx)

    @commands.command(name='loop', aliases=['songloop'])
    async def single_loop(self, ctx: commands.Context, times: Union[int, str]=INF):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].single_loop(ctx, times)

    @commands.command(name='wholeloop', aliases=['queueloop', 'qloop'])
    async def whole_loop(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].whole_loop(ctx)

    @commands.command(name='show', aliases=['queuelist', 'queue'])
    async def show(self, ctx: commands.Context):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].show(ctx)

    @commands.command(name='remove', aliases=['queuedel'])
    async def remove(self, ctx: commands.Context, idx: Union[int, str]):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].remove(ctx, idx)
    
    @commands.command(name='swap')
    async def swap(self, ctx: commands.Context, idx1: Union[int, str], idx2: Union[int, str]):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].swap(ctx, idx1, idx2)

    @commands.command(name='move_to', aliases=['insert_to', 'move'])
    async def move_to(self, ctx: commands.Context, origin: Union[int, str], new: Union[int, str]):
        if self.router.get(ctx.guild.id) is None:
            self.router[ctx.guild.id] = MusicBot(self.bot)
        await self.router[ctx.guild.id].move_to(ctx, origin, new)

    # Error handler
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        else:
            print(error)
            await ctx.send(f'''
            **:no_entry: | 失敗 | UNKNOWNERROR**
            執行指令時發生了一點未知問題，請稍候再嘗試一次
            --------
            技術資訊:
            {error}
            --------
            *若您覺得有Bug或錯誤，請參照上方資訊及代碼回報至 Github*
            ''') 

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'''
    =========================================
    Codename TKablent | Version Alpha
    Copyright 2022-present @ TK Entertainment
    Shared under CC-NC-SS-4.0 license
    =========================================
    
    Discord Bot TOKEN | {TOKEN}

    If there is any problem, open an Issue with log
    else no any response or answer

    If there isn't any exception under this message,
    That means bot is online without any problem.
    若此訊息下方沒有任何錯誤訊息
    即代表此機器人已成功開機
    ''')

bot.add_cog(Router(bot))

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
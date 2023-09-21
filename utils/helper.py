import discord
from discord.ext import commands
from discord import app_commands


class HelperCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        commands.Cog.__init__(self)
        self.bot: commands.Bot = bot

    @commands.command(name="currentjoined")
    async def current_joined(self, ctx: commands.Context):
        if ctx.guild.id == 844597380170252348:
            await ctx.send(f"Currently joined {len(self.bot.guilds)} guilds")

import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os
import asyncio
from msgspec.json import decode as json_decode

allowed_guilds = list(map(int, os.getenv("ALLOWED_GUILDS").split(",")))

def fetch(guild: int, key: str) -> None:
    """fetch from database"""
    with open(rf"{os.getcwd()}/music_comp/data.json", "rb") as f:
        data: dict = json_decode(f.read())
    if (
        data.get(str(guild)) is None
        or data[str(guild)].get(key) is None
    ):
        return None
    return data[str(guild)][key]

class HelperCog(app_commands.Group):
    def __init__(self, bot: commands.Bot):
        super().__init__(name="internal", description="THESE TOOL IS MEANT TO BE USED INTERNALLY", guild_ids=allowed_guilds)
        self.bot: commands.Bot = bot

    @app_commands.command(name="current_joined", description="INTERNAL USE ONLY: Get the current joined guilds")
    async def current_joined(self, interaction: discord.Interaction):
        if interaction.guild.id in allowed_guilds:
            await interaction.response.send_message(f"[INTERNAL USE ONLY]\nCurrently joined {len(self.bot.guilds)} guilds\n[CONFIDENTIAL]")

    @app_commands.command(name="list_joined", description="INTERNAL USE ONLY: Get the current joined guilds")
    async def list_joined(self, interaction: discord.Interaction):
        if interaction.guild.id in allowed_guilds:
            try:
                await interaction.response.send_message(f"[INTERNAL USE ONLY]\nCurrently joined:\n```\n{self.bot.guilds}\n```\n[CONFIDENTIAL]")
            except Exception as e:
                print(e)

    @app_commands.command(name="test_announce", description="INTERNAL USE ONLY: Test announcing")
    async def test_announce(self, interaction: discord.Interaction, title: str, description: str, send: bool):
        if interaction.guild.id in allowed_guilds:
            issued_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if send:
                await self.announce(interaction, title, description)
            try:
                embed = discord.Embed(title=f"{title}", description=f"{description.replace('\\n', '\n')}", colour=discord.Colour.red())
                embed.set_author(name="TKablent 系統通知", icon_url="https://i.imgur.com/p4vHa3y.png")
                embed.set_footer(text=f"公告時間: {issued_time}")
                await interaction.response.send_message(embed=embed)
            except Exception as e:
                print(e)

    async def announce_task(self, interaction: discord.Interaction, title: str, description: str, issued_time: str):
            try:
                i = 1
                embed = discord.Embed(title=f"{title}", description=f"{description.replace('\\n', '\n')}", colour=discord.Colour.red())
                embed.set_author(name="TKablent 系統通知", icon_url="https://i.imgur.com/p4vHa3y.png")
                embed.set_footer(text=f"公告時間: {issued_time}")
                for guild in self.bot.guilds:
                    print(f"[Announcement] Sending to {guild.name} ({i}/{len(self.bot.guilds)})")
                    try:
                        if fetch(guild.id, "text_channel") is not None:
                            embed.set_footer(text=f"公告時間: {issued_time}")
                            await guild.get_channel(fetch(guild.id, "text_channel")).send(embed=embed)
                        else:
                            raise Exception("No text channel found")
                    except Exception as e:
                        for channel in guild.text_channels:
                            try:
                                embed.set_footer(text=f"公告時間: {issued_time}\n【注意】若您不想要在這邊收到公告，請您使用一次機器人\n機器人往後即會在您使用機器人的頻道發送公告")
                                await channel.send(embed=embed)
                                break
                            except Exception as e:
                                continue   
                    i += 1
            except Exception as e:
                print(e)

    async def announce(self, interaction: discord.Interaction, title: str, description: str):
        if interaction.guild.id in allowed_guilds:
            await interaction.response.defer(thinking=True)
            issued_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            asyncio.create_task(self.announce_task(interaction, title, description, issued_time))

            await interaction.followup.send("[INTERNAL USE ONLY]\nAnnouncement sent")

    async def announce_update_task(self, interaction: discord.Interaction, version: str, issued_time: str):
        try:
            embed = discord.Embed(title="機器人將進行更新作業", description=f"TKablent 將在 5 分鐘後進行更新作業\n將更新至 **{version}**\n更新內容將會在開機後第一次使用時通知您\n\n期間將無法使用本機器人，還請見諒\n機器人若狀態為綠燈且顯示 **正在播放...** 即代表重啟完成\n\n*請注意: 本次更新後，您目前正在使用的播放清單將會被清除，以保證相容性問題*", colour=discord.Colour.red())
            embed.set_author(name="TKablent 系統通知", icon_url="https://i.imgur.com/p4vHa3y.png")
            embed.set_footer(text=f"公告時間: {issued_time}")
            i = 1
            for guild in self.bot.guilds:
                print(f"[Announcement] Sending to {guild.name} ({i}/{len(self.bot.guilds)})")
                try:
                    if fetch(guild.id, "text_channel") is not None:
                        embed.set_footer(text=f"公告時間: {issued_time}")
                        await guild.get_channel(fetch(guild.id, "text_channel")).send(embed=embed)
                    else:
                        raise Exception("No text channel found")
                except Exception as e:
                    for channel in guild.text_channels:
                        try:
                            embed.set_footer(text=f"公告時間: {issued_time}\n【注意】若您不想要在這邊收到公告，請您使用一次機器人\n機器人往後即會在您使用機器人的頻道發送公告")
                            await channel.send(embed=embed)
                            break
                        except Exception as e:
                            continue        
                i += 1
        except Exception as e:
            print(e)

    @app_commands.command(name="announce_update", description="INTERNAL USE ONLY: Announcing the update process")
    async def announce_update(self, interaction: discord.Interaction, version: str):
        if interaction.guild.id in allowed_guilds:
            await interaction.response.defer(thinking=True)
            issued_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            asyncio.create_task(self.announce_update_task(interaction, version, issued_time))

            await interaction.followup.send("[INTERNAL USE ONLY]\nAnnouncement sent")

    @app_commands.command(name="count_total", description="INTERNAL USE ONLY: Getting the total number of users")
    async def count_total(self, interaction: discord.Interaction):
        total_count = 0
        for guild in self.bot.guilds:
            total_count += guild.member_count
        await interaction.response.send_message(f"[INTERNAL USE ONLY]\nBot is now serving {total_count} users in {len(self.bot.guilds)} guilds.")
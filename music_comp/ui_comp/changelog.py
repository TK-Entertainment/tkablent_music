from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import *
import discord
from discord.ext import commands
import json, os
from ..ui import rescue_emoji, end_emoji
from datetime import datetime
import time
import copy


class Changelogs:
    def __init__(self):
        from ..ui import musicbot, bot_version, embed_opt
        embed_opt_raw = copy.deepcopy(embed_opt)
        embed_opt_raw["footer"]["text"] = (
            embed_opt_raw["footer"]["text"] + "\n播放伺服器由 404 Network Information Co. 提供支援"
        )
        self.embed_opt = embed_opt_raw

        self.bot: commands.Bot = musicbot.bot
        self.musicbot = musicbot
        self.bot_version = bot_version
        self.ChangeLogsDefine()

    def ChangeLogsDefine(self) -> None:
        self.version = self.bot_version
        self.branch = "Stable" if self.bot_version[-1] == "s" else "Cutting Edge"
        self.test_subject = self.bot_version.split(".")[2].split("-")[0] if self.bot_version[-1] != "s" else ""
        
        # Define if this is a final version for the test subject
        self.is_final_test_version = False

        # Define if this version is inherit from specfic test version
        self.inherit_from_version = ""
        self.picture = ""
        self.emergency_build = True

        self.github_link = "https://github.com/TK-Entertainment/tkablent_music/releases/tag/m.20231224.wl30_test-ce"

        # Index 0 means changelog state (# for inherit version separator, + for new stuff, ! for changed stuff, - for removed stuff, (!) for emergency log)
        # Index 1 means changelog summary
        # Index 2 means changelog description
        self.changelogs = [
            ["+", "【新增】機器人播放 Spotify 歌曲時會顯示相關警告", "=> 以前就已經確認 Spotify 音源準確性的問題\n=> 從此版本開始會顯示警告"],
            ["!", "【更新】機器人播放組件 API 更新到 Wavelink 3.0", "=> 這是一個很大的 API 更新，很多語法都改變了\n=> 還需要細項調整，此版本可能存在許多潛在問題"],
            ["!", "【優化】棄用許多外置 API 套件", "=> 因 Lavalink 4.0 帶來了新的插件功能，故此版本開始棄用了許多的外置 API\n=> 可能可以為機器人帶來部分效能提升"],
            ["!", "【優化】點播 Spotify 歌曲時，機器人將不再顯示等待畫面", "=> 拜 Lavalink 4.0 所賜，現在機器人可以很有效率的抓到歌曲\n=> 將不再需要等待"],
            ["!", "【改變】/restart 指令改變為 /replay", "=> 從此版本開始，/restart 指令將重新命名為 /replay"],
            ["!", "【改變】節慶提示字將自行成行", "============="],
            ["#", "⚠️ 已知問題", "============="],
            ["(!)", "【Bug】Spotify 的推薦歌曲功能將暫時無法使用", "=> 目前因 API 架構改變，尚未找到方法實作 Spotify 的推薦\n=> 故 Spotify 之歌曲將暫時無法使用機器人的推薦功能"],
            ["(!)", "【Bug】Bilibili 歌曲播放功能尚未確定可以使用", "=> 目前此版本尚未測試是否可以播放 BiliBili 的歌曲\n=> 故可能暫時無法使用"],
            ["(!)", "【Bug】其他因大架構更新而出現的問題", "=> 如上所述，此版本是更新架構後第一個釋出版本，可能存在諸多問題\n=> 還請各位測試人員協助回報問題，這樣我們才能更快的讓所有人用到這個版本！\n=> 非常感謝！"],
        ]

    async def SendChangelogs(self, interaction: discord.Interaction) -> None:
        last_sent_version = self.musicbot[interaction.guild_id].changelogs_latestversion
        if (last_sent_version == "") or (last_sent_version != self.bot_version):
            await self.SendChangelogsEmbed(interaction)
            self.musicbot[interaction.guild_id].changelogs_latestversion = self.bot_version

    async def SendChangelogsEmbed(self, interaction: discord.Interaction) -> None:
        class ChangelogBody(discord.ui.View):
            github_link = self.github_link

            def __init__(self):
                super().__init__(timeout=None)
                self.groupbutton = discord.ui.Button(
                    emoji=rescue_emoji,
                    style=discord.ButtonStyle.link,
                    url="https://discord.gg/9qrpGh4e7V",
                    label="支援群組",
                    row=0,
                )
                self.GithubButton = discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    url=self.github_link,
                    label="GitHub Release",
                    row=0,
                )
                self.add_item(self.GithubButton)
                self.add_item(self.groupbutton)

            @discord.ui.button(
                emoji=end_emoji, style=discord.ButtonStyle.danger
            )
            async def end(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.clear_items()
                try:
                    await msg.delete()
                except discord.HTTPException:
                    pass
                self.stop()

        embed = discord.Embed(title=f"TKablent {self.branch}\n{self.bot_version}", description="{}哈囉！我們這次帶來了以下幾項更新：".format(f"***此版本更新內容自測試版 {self.inherit_from_version} 滾入\n***" if (self.inherit_from_version != "" and self.branch == "Stable") else ""))
        embed.set_author(name="新更新推出啦！{}{}".format(
            f"\n【!】{self.test_subject} 測試項目最終版本，詳情請參下方更新項目" if self.is_final_test_version and self.branch == "Cutting Edge" else "",
            f"\n【!】此為緊急修復更新，詳情請參下方更新項目" if self.emergency_build and self.branch == "Stable" else ""
            ), icon_url="https://i.imgur.com/p4vHa3y.png")
        
        for item in self.changelogs:
            icon = "🆕" if item[0] == "+" else "🛠️" if item[0] == "!" else "🗑️" if item[0] == "-" else "⚠️" if item[0] == "(!)" else "#"
            embed.add_field(name=f"{icon} {item[1]}", value=f"*{item[2]}*", inline=False)

        embed.add_field(name="想知道更多嗎？", value=f"詳細更新資訊可參考 GitHub 或進入我們的群組取得幫助、交流或給我們建議喔")

        if self.picture != "":
            embed.set_image(url=self.picture)

        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))        
        msg = await interaction.channel.send(embed=embed, view=ChangelogBody())

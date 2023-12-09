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
        self.is_final_test_version = True

        # Define if this version is inherit from specfic test version
        self.inherit_from_version = "m.20231209.linkandui-ce"

        self.github_link = "https://github.com/TK-Entertainment/tkablent_music/releases/tag/m.20231209.linkandui-ce"

        # Index 0 means changelog state (# for inherit version separator, + for new stuff, ! for changed stuff, - for removed stuff)
        # Index 1 means changelog summary
        # Index 2 means changelog description
        self.changelogs = [
            ["!", "【重要】此為 linkandui 測試項目的最終版本", "=> 此版本為 **linkandui** 測試項目的最終版本，將在下一次更新 ce 版時轉移至下一個測試項目 **wavelink30-depend** 開始全新核心的測試\n=> 因測試版機器人目前使用人數較少，故此次將不進行退群動作\n=> 因配合新核心測試工作，穩定版將暫緩更新。請稍待新測試項目穩定後即會恢復"],
            ["!", "【優化】大幅加速搜尋提示字及本地緩存儲存處理速度", "=> 優化終於來啦，這次是個大的\n=> 經過內部測試，在相同環境、相同候選字、皆無快取的情況下\n=> 搜尋速度加快超過 **5** 倍速度，本地緩存儲存速度則加快約 **1.4** 倍\n=> 詳情可至 [Github Release | m.20231209.linkandui-ce](https://github.com/TK-Entertainment/tkablent_music/releases/tag/m.20231209.linkandui-ce) 查看"],
            ["+", "【新增】新增各伺服器的更新資訊推送", "=> 考慮到並非所有使用者都有加入本群組，機器人自本版本起會在該伺服器更新後第一次傳送要求時傳送更新資訊，讓所有使用者知道我們準備了什麼好料的 (owob)"]
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
        embed.set_author(name="新更新推出啦！{}".format(f"\n【!】{self.test_subject} 測試項目最終版本，詳情請參下方更新項目" if self.is_final_test_version and self.branch == "Cutting Edge" else ""), icon_url="https://i.imgur.com/p4vHa3y.png")
        
        for item in self.changelogs:
            icon = "🆕" if item[0] == "+" else "🛠️" if item[0] == "!" else "🗑️"
            embed.add_field(name=f"{icon} {item[1]}", value=f"*{item[2]}*", inline=False)

        embed.add_field(name="想知道更多嗎？", value=f"詳細更新資訊可參考 GitHub 或進入我們的群組取得幫助、交流或給我們建議喔")

        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))        
        msg = await interaction.channel.send(embed=embed, view=ChangelogBody())

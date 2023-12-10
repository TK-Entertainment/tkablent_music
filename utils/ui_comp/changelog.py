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
        self.picture = "https://i.imgur.com/JoUL5CF.gif"

        self.github_link = "https://github.com/TK-Entertainment/tkablent_music/releases/tag/m.20230716.7-s"

        # Index 0 means changelog state (# for inherit version separator, + for new stuff, ! for changed stuff, - for removed stuff)
        # Index 1 means changelog summary
        # Index 2 means changelog description
        self.changelogs = [
            ["!", "【注意】此為維護性更新", "=> 此更新僅同步至正式版機器人，測試版會跟隨下個測試項目一起併入此次更新\n=>其餘內容跟隨上次更新"],
            ["!", "【優化】推薦歌曲功能啟動的體驗 (詳情可參圖)", "=> 修改了一下推薦歌曲按鈕的工作方式\n=> 過去的版本會等待歌曲處理完成後才會更改狀態，但這很容易使 Discord 逾時而出現假性無回應狀態\n=> 此次更新優化了體驗，機器人會先更改狀態，並在之後才更新處理完成的歌曲"],
            ["!", "!【修正】修復部分按鈕邏輯問題", "=> 此版本修復了有時按鈕已被停用，但是按鈕顏色仍然保持未停用時的狀態的問題"],
            ["#", "以下為 m.20230716.6-s 更新內容", "============="],
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
            icon = "🆕" if item[0] == "+" else "🛠️" if item[0] == "!" else "🗑️" if item[0] == "-" else "#"
            embed.add_field(name=f"{icon} {item[1]}", value=f"*{item[2]}*", inline=False)

        embed.add_field(name="想知道更多嗎？", value=f"詳細更新資訊可參考 GitHub 或進入我們的群組取得幫助、交流或給我們建議喔")

        if self.picture != "":
            embed.set_image(url=self.picture)

        embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))        
        msg = await interaction.channel.send(embed=embed, view=ChangelogBody())

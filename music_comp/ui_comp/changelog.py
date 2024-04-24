from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import *
import discord
from discord.ext import commands
from ..ui import rescue_emoji, end_emoji
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
        self.emergency_build = False

        self.github_link = "https://github.com/TK-Entertainment/tkablent_music/releases/tag/m.20240318-s"

        # Index 0 means changelog state (# for inherit version separator, + for new stuff, ! for changed stuff, - for removed stuff, (!) for emergency log)
        # Index 1 means changelog summary
        # Index 2 means changelog description
        self.changelogs = [
            ["(!)", "【緊急修復】修復上版更新後導致的無法點播多首搜尋結果的問題", "============="],
            ["#", "⚠️ 已知問題", "============="],
            ["(!)", "【Bug】Spotify 的推薦歌曲功能將暫時無法使用\n(預計於 m.20240318.2-s 解決)", "=> 目前因 API 架構改變，尚未找到方法實作 Spotify 的推薦\n=> 故 Spotify 之歌曲將暫時無法使用機器人的推薦功能"],
            ["(!)", "【Bug】Bilibili 歌曲播放功能尚未確定可以使用\n(預計於 m.20240318.2-s 解決)", "=> 目前此版本尚未測試是否可以播放 BiliBili 的歌曲\n=> 故可能暫時無法使用"],
            ["(!)", "【Bug】其他因大架構更新而出現的問題", "=> 因大架構更動及重寫，機器人可能存在諸多零星問題\n=> 還請各位使用者協助回報問題，這樣我們才能更快讓機器人變得更好！"],
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

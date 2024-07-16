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
        self.picture = "https://cdn.discordapp.com/attachments/642704558996586496/1262838299735621684/image.png?ex=66980d51&is=6696bbd1&hm=0443c66aa4de144678a868d73eb39936a27de92e5fe8aa65d204aa3b75762eea&"
        self.emergency_build = False

        self.github_link = "https://github.com/TK-Entertainment/tkablent_music/releases/tag/m.20240318-s"

        # Index 0 means changelog state (# for inherit version separator, + for new stuff, ! for changed stuff, - for removed stuff, (!) for emergency log)
        # Index 1 means changelog summary
        # Index 2 means changelog description
        self.changelogs = [
            ["+", "【新增】新增群組最愛點播/近期點播選項 (可參圖)", "=> 在上次意見回饋中，我們發現有些群組希望能夠快速點播最愛或近期點播過的歌曲\n=> 現在您可以在點播選單中選擇「這群ㄉ最愛！」或「最近播放」來點播\n=> 請注意，最愛歌曲的結果會在該群組點播歌曲至一定數量時出現 (不含自動播放)"],
            ["+", "【新增】全新新增歌曲介面 (由播放介面進入)", "=> 現在最愛點播/近期點播選項也在點選介面上可用！\n=> 使用手機的你也可以點播最愛點播/近期點播的歌了"],
            ["!", "【修復】修復上個版本無法透過介面暫停的問題", "=> 此版本已修復此問題"],
            ["!", "【改進】一些有的沒的穩定性及可靠性修復", "=> 我也不知道修了啥，但應該是有的 (*°∀°)"],
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

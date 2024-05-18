from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import *
import discord
from discord.ext import commands
import json, os
from ..ui import rescue_emoji, end_emoji
from datetime import datetime
import time


class Survey:
    def __init__(self):
        from ..ui import musicbot, auto_stage_available, guild_info

        self.enabled = False

        self.__survey_name = "202308_usual"

        self._file_name = rf"{os.getcwd()}/music_comp/surveys/{self._survey_name}_survey.json"
        self._survey_thread = 1137651881292865596

        self.__bot: commands.Bot = musicbot.bot
        self._musicbot = musicbot
        self._auto_stage_available = auto_stage_available
        self._guild_info = guild_info

        with open(self._file_name, "r") as f:
            self._survey = json.load(f)

    def survey(self, item) -> dict:
        return self._survey[item]

    def _update_cache(
        self, replier: str, replier_id: int, stars: str | int, suggestion: str
    ) -> None:
        """update database"""
        with open(self._file_name, "r") as f:
            data: dict = json.load(f)
        if replier_id not in data.get("user_ids"):
            data["users"].append(replier)
            data["user_ids"].append(replier_id)

        data["reply_count"] += 1
        data["data"].append([replier, stars, suggestion])

        self._survey = data

        with open(self._file_name, "w") as f:
            json.dump(data, f)

    def SurveyButton(self):
        class SurveyModal(discord.ui.Modal):
            bot = self.__bot
            survey_name = self._survey_name
            survey = self._survey
            file_name = self._file_name
            survey_thread = self._survey_thread
            update_cache = self._update_cache

            def __init__(self):
                self.stars = discord.ui.TextInput(
                    custom_id="stars",
                    label="請您填寫對於此機器人的體驗評價 (請填入數字，必填)",
                    placeholder=f"可填入 1(最差) ~ 10(最佳)",
                    style=discord.TextStyle.short,
                    min_length=1,
                    max_length=2,
                )

                self.suggestions = discord.ui.TextInput(
                    custom_id="suggestions",
                    label="有什麼想要給我們的建議嗎？(選填)",
                    placeholder="可填入想要增加的新功能 (不限於音樂類功能)、需要改進的地方等等",
                    style=discord.TextStyle.paragraph,
                    required=False,
                )

                super().__init__(title="📝 | 使用者使用體驗調查", timeout=120)

                self.add_item(self.stars)
                self.add_item(self.suggestions)

            async def count_total(self):
                total_count = 0
                for guild in self.bot.guilds:
                    total_count += guild.member_count
                return total_count

            async def on_submit(self, interaction: discord.Interaction) -> None:
                if interaction.user.discriminator == "0":
                    user_name = interaction.user.name
                else:
                    user_name = (
                        f"{interaction.user.name}#{interaction.user.discriminator}"
                    )

                self.update_cache(
                    replier=user_name,
                    replier_id=interaction.user.id,
                    stars=self.stars.value,
                    suggestion=self.suggestions.value,
                )

                channel = self.bot.get_channel(self.survey_thread)
                total = await self.count_total()
                replies = self.survey("reply_count")
                ratio = round((replies / total) * 100, 2)
                embed = discord.Embed(
                    title="已收到問卷調查",
                    description=f"已收到問卷，問卷名稱: **{self.survey_name}**",
                    color=0x00FF00,
                )
                embed.add_field(name="評分", value=self.stars.value, inline=False)
                embed.add_field(name="建議", value=self.suggestions.value, inline=False)
                embed.set_author(name=user_name, icon_url=interaction.user.avatar)
                embed.set_footer(
                    text=f"ID: {interaction.user.id} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n問卷回收率: {ratio}% ({replies} / {total})"
                )
                await channel.send(embed=embed)

                await interaction.response.send_message(
                    "已收到您的問卷，感謝您的填寫！", ephemeral=True
                )

        class SurveyBody(discord.ui.View):
            survey = self.survey

            def __init__(self):
                super().__init__(timeout=None)
                self.button = discord.ui.Button(
                    emoji=rescue_emoji,
                    style=discord.ButtonStyle.link,
                    url="https://discord.gg/9qrpGh4e7V",
                    label="支援群組",
                    row=1,
                )
                self.add_item(self.button)

            @discord.ui.button(
                label="填寫問卷", emoji=discord.PartialEmoji.from_str("📝"), style=discord.ButtonStyle.blurple
            )
            async def survey_button(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                if interaction.user.id in self.survey("user_ids"):
                    await interaction.response.send_message(
                        "您已經填寫過問卷囉，感謝您的填寫！", ephemeral=True
                    )
                    return
                await interaction.response.send_modal(SurveyModal())

            @discord.ui.button(
                label="關閉問卷", emoji=end_emoji, style=discord.ButtonStyle.danger
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

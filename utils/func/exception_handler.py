from typing import *
import discord
import datetime

from ..player import Command
from ..github import GithubIssue
from .info import InfoGenerator
from ..ui import groupbutton

class ExceptionHandler:
    def __init__(self, info_generator):
        from ..ui import embed_opt, bot, guild_info
        self.guild_info = guild_info
        self.info_generator: InfoGenerator = info_generator
        self.embed_opt = embed_opt
        self.bot = bot
        self.github: GithubIssue = GithubIssue()
        self.errorcode_to_msg = {
            "PLAYER_FAULT": "機器人遇到了一些問題，故無法正常播放\n            將跳過此歌曲",
            "JOINFAIL": ["請確認您是否已加入一個語音頻道", "join", "來把我加入頻道"],
            "LEAVEFAIL": ["請確認您是否已加入一個語音/舞台頻道，或機器人並不在頻道中", "leave", "來讓我離開頻道"],
            "PAUSEFAIL": ["無法暫停音樂，請確認目前有歌曲正在播放，或是當前歌曲並非處於暫停狀態，亦或是候播清單是否為空", "pause", "來暫停音樂"],
            "RESUMEFAIL": ["無法續播音樂，請確認目前有處於暫停狀態的歌曲，或是候播清單是否為空", "resume", "來續播音樂"],
            "SKIPFAIL": ["無法跳過歌曲，請確認目前候播清單是否為空", "skip", "來跳過音樂"],
            "STOPFAIL": ["無法停止播放歌曲，請確認目前是否有歌曲播放，或候播清單是否為空", "stop", "來停止播放音樂"],
            "VOLUMEADJUSTFAIL": ["無法調整音量，請確認目前機器人有在語音頻道中\n            或是您輸入的音量百分比是否有效\n            請以百分比格式(ex. 100%)執行指令", "volume", "來調整音量"],
            "SEEKFAIL": ["無法跳轉歌曲，請確認您輸入的跳轉時間有效\n            或目前是否有歌曲播放，亦或候播清單是否為空\n            請以秒數格式(ex. 70)或時間戳格式(ex. 01:10)執行指令", "seek", "來跳轉音樂"],
            "REPLAYFAIL": ["無法重播歌曲，請確認目前是否有歌曲播放", "replay", "來重播歌曲"],
            "LOOPFAIL_SIG": ["無法啟動重複播放功能，請確認您輸入的重複次數有效", f"loop / {self.bot.command_prefix}loop [次數]", "來控制重複播放功能"],
            "REMOVEFAIL": ["無法刪除指定歌曲，請確認您輸入的順位數有效", "remove [順位數]", "來刪除待播歌曲"],
            "SWAPFAIL": ["無法交換指定歌曲，請確認您輸入的順位數有效", "swap [順位數1] [順位數2]", "來交換待播歌曲"],
            "MOVEFAIL": ["無法移動指定歌曲，請確認您輸入的目標順位數有效", "move [原順位數] [目標順位數]", "來移動待播歌曲"],
            "SHUFFLEFAIL": ["無法隨機排列待播歌曲，請確認待播列表有歌曲可供排列", "shuffle", "來隨機排列待播歌曲"],
        }

    async def _MusicExceptionHandler(self, message, exception=None, url=None):
        part_content = f'''
        **:warning: | 警告 | SEARCH_OR_PLAYING_FAILED**
        您提供的音樂，機器人無法播放
        有可能該音樂為會員影片、為私人影片或不存在
        或為機器人不支援的平台

        *此錯誤不會影響到播放，僅為提醒訊息*'''

        done_content = part_content

        content = f'''
            {part_content}
            *若您覺得有Bug或錯誤，請到我們的群組來回報錯誤*
        '''

        await self._BugReportingMsg(message, content, done_content, errorcode="SEARCH_OR_PLAYING_FAILED", exception=exception, video_url=url)

    async def _CommonExceptionHandler(self, message: Command , errorcode: str, exception=None):
        done_content = f'''
            **:no_entry: | 失敗 | {errorcode}**
            {self.errorcode_to_msg[errorcode][0]}
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}{self.errorcode_to_msg[errorcode][1]}** {self.errorcode_to_msg[errorcode][2]}*
        '''

        content = f'''
            **:no_entry: | 失敗 | {errorcode}**
            {self.errorcode_to_msg[errorcode][0]}
            --------
            *請在確認排除以上可能問題後*
            *再次嘗試使用 **{self.bot.command_prefix}{self.errorcode_to_msg[errorcode][1]}** {self.errorcode_to_msg[errorcode][2]}*
            *若您覺得有Bug或錯誤，請到我們的群組來回報錯誤*
            '''

        await self._BugReportingMsg(message, content, done_content, errorcode, exception)
        
    async def _BugReportingMsg(self, message: Union[Command, discord.TextChannel], content, done_content, errorcode, exception=None, video_url=None):
        cdt = datetime.datetime.now()
        errortime = cdt.strftime("%Y/%m/%d %H:%M:%S")

        if errorcode == "SEARCH_FAILED":
            embed = self.info_generator._SongInfo(guild_id=message.guild.id, color_code='red')
            if isinstance(message, Command) and message.is_response():
                msg = await message.channel.send(content, embed=embed, view=groupbutton)
            else:
                msg = await message.send(content, embed=embed, view=groupbutton)
        else:
            if isinstance(message, Command) and message.command_type == "Interaction":
                if message.is_response():
                    msg = await message.channel.send(content, view=groupbutton)
                else:
                    msg = await message.send(content, view=groupbutton)
            else:
                msg = await message.send(content, view=groupbutton)

        self.guild_info(message.guild.id).lasterrorinfo = {
            "errortime": errortime,
            "msg": msg,
            "done_content": done_content,
            "errorcode": errorcode,
            "exception": exception,
            "video_url": video_url
        }

    # async def Interaction_BugReportingModal(self, interaction: discord.Interaction, guild: discord.Guild):

    #     class BugReportingModal(discord.ui.Modal):
    #         lasterror = self.guild_info(guild.id).lasterrorinfo
    #         github = self.github
    #         guildinfo = guild
    #         bot = self.bot

    #         if "errorcode" not in lasterror.keys():
    #             error_code = ""
    #         else:
    #             error_code = lasterror["errorcode"]

    #         if "errortime" not in lasterror.keys():
    #             error_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    #         else:
    #             error_time = lasterror["errortime"]

    #         embed_opt = self.embed_opt

    #         def __init__(self):
    #             self.bot_name = discord.ui.TextInput(
    #                 custom_id="bot_name",
    #                 label="機器人名稱 (已自動填入，不需更改)",
    #                 default=f"{self.bot.user.name}#{self.bot.user.discriminator}"
    #             )

    #             self.guild = discord.ui.TextInput(
    #                 custom_id="guild",
    #                 label="伺服器名稱 (已自動填入，不需更改)",
    #                 default=f"{self.guildinfo.name} ({self.guildinfo.id})"
    #             )

    #             self.error_code_text = discord.ui.TextInput(
    #                 custom_id="error_code",
    #                 label="錯誤代碼 (由上一次錯誤填入，可修改)",
    #                 default=self.error_code
    #             )

    #             self.modaltime_text = discord.ui.TextInput(
    #                 custom_id="submit_time",
    #                 label="錯誤發生時間 (已自動填入，不需更改)",
    #                 default=self.error_time
    #             )

    #             self.description = discord.ui.TextInput(
    #                 custom_id="error_description",
    #                 label="請簡述錯誤是如何產生的",
    #                 placeholder="簡述如何重新產生該錯誤，或該錯誤是怎麼產生的。\n如果隨意填寫或更改上方資料，將可能遭到忽略",
    #                 style=discord.TextStyle.paragraph
    #             )
    #             super().__init__(
    #                 title = "🐛 | 回報蟲蟲",
    #                 timeout=120
    #             )

    #             for item in [
    #                     self.bot_name,
    #                     self.guild,
    #                     self.error_code_text,
    #                     self.modaltime_text,
    #                     self.description
    #                 ]:
    #                 self.add_item(item)


    #         def result_embed(self, results: dict):
    #             embed = discord.Embed(title="🐛 | 錯誤回報簡表 (點我到 Github Issue)", url=self.github.issue_user_url, description="")
    #             embed.add_field(name="錯誤代碼", value="{}".format(results["errorcode"]))
    #             embed.add_field(name="錯誤回報時間", value="{}".format(results["timestamp"]))
    #             embed.add_field(name="造成錯誤之影片連結", value="{}".format(results["video_url"]))
    #             embed.add_field(name="使用者回報之簡述", value="{}".format(results["description"]))
    #             embed.add_field(name="參考錯誤代碼", value="{}".format(results["exception"]))
    #             embed.add_field(name="👏 感謝你的回報", value="⠀")
    #             embed = discord.Embed.from_dict(dict(**embed.to_dict(), **self.embed_opt))
    #             return embed

    #         async def on_submit(self, interaction: discord.Interaction):
    #             if self.error_code_text.value != self.error_code:
    #                 exception = "無可參考之錯誤回報，或錯誤代碼被更改"
    #                 video_url = None
    #             else:
    #                 exception = self.lasterror["exception"]
    #                 video_url = self.lasterror["video_url"]
    #             submission = self.github.submit_bug(
    #                 self.bot_name.value,
    #                 self.guild.value,
    #                 self.error_code_text.value,
    #                 self.modaltime_text.value,
    #                 self.description.value,
    #                 exception,
    #                 video_url,
    #             )
    #             await interaction.response.send_message(embed=self.result_embed(submission))

    #             try:
    #                 await self.lasterror["msg"].edit(content=self.lasterror["done_content"])
    #             except:
    #                 pass

    #         async def on_timeout(self):
    #             pass

    #     modal = BugReportingModal()
    #     await interaction.response.send_modal(modal)
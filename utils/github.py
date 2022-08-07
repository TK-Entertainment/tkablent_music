import requests, json, os, dotenv

dotenv.load_dotenv()

# For testing purposes only
test = True

class GithubIssue:
    def __init__(self):
        token = os.getenv('GITHUB_TOKEN')
        self.headers = {"Accept": "application/vnd.github.v3+json", "Authorization" : f"token {token}"}
        if test:
            self.issue_url = "https://api.github.com/repos/TK-Entertainment/testing_repo/issues"
            self.issue_user_url = "https://github.com/TK-Entertainment/testing_repo/issues"
        else:
            self.issue_url = "https://api.github.com/repos/TK-Entertainment/tkablent/issues"
            self.issue_user_url = "https://github.com/TK-Entertainment/tkablent/issues"
        
        self.errorcode_to_msg = {
            "SEARCH_FAILED": "搜尋時，提供的連結無法正常播放或不存在",
            "PLAYER_FAULT": "播放時，機器人發生錯誤，無法正常播放",
            "JOINFAIL": "機器人嘗試加入頻道時失敗",
            "LEAVEFAIL": "機器人嘗試離開頻道時失敗",
            "PAUSEFAIL": "機器人嘗試暫停音樂時失敗",
            "RESUMEFAIL": "機器人嘗試續播音樂時失敗",
            "SKIPFAIL": "機器人嘗試跳過音樂時失敗",
            "STOPFAIL": "機器人嘗試停止音樂時失敗",
            "VOLUMEADJUSTFAIL": "機器人嘗試調整音量時失敗",
            "SEEKFAIL": "機器人嘗試跳轉音樂時失敗",
            "REPLAYFAIL": "機器人嘗試重新播放音樂時失敗",
            "LOOPFAIL_SIG": "機器人嘗試切換重新播放功能時失敗",
            "REMOVEFAIL": "機器人嘗試從待播清單中移除音樂時失敗",
            "SWAPFAIL": "機器人嘗試從待播清單中更換兩個音樂順序時失敗",
            "MOVEFAIL": "機器人嘗試從待播清單中移動音樂時失敗",
            "TESTING": "機器人表單測試"
        }


    def submit_bug(self, bot_name, guild, errorcode, timestamp, description, exception, video_url=None) -> dict:
        if video_url is None:
            video_url = "無影片連結可用，或此類錯誤與歌曲播放無關"

        if "LocalDev" in bot_name:
            version = "master Branch / 本地開發版本"
        elif "Alpha" in bot_name or "Beta" in bot_name:
            version = "Alpha or Beta / 測試版本"
        else:
            version = "Stable / 正式版本"

        if errorcode not in self.errorcode_to_msg.keys():
            errortext = "其他錯誤代碼/未知錯誤"
        else:
            errortext = self.errorcode_to_msg[errorcode]

        data = {
            "title": f"機器人錯誤回報表單 from {guild}",
            "body": f'''
**錯誤代碼**  
{errorcode} ({errortext})  
  
**錯誤回報時間**  
{timestamp} (Taipei Standard Time)  
  
**造成錯誤之影片連結**  
{video_url}  
  
**使用者回報之簡述**  
{description}  
  
**參考錯誤代碼**  
{exception}  
  
**此 Issue 為機器人端表單所開啟的**  
**發出表單機器人: {bot_name}**  
**機器人版本: {version}**''',
            "labels": ['bug', 'bug_from_bot']
            }

        owo = requests.post(
            self.issue_url, 
            data=json.dumps(data),
            headers=self.headers
            )
        
        print(owo.content)

        return {
            "errorcode": f"{errorcode} ({self.errorcode_to_msg[errorcode]})",
            "timestamp": f"{timestamp} (Taipei Standard Time)",
            "video_url": video_url,
            "description": description,
            "exception": exception,
        }

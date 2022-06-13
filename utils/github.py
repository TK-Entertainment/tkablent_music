import requests, json, os, dotenv

dotenv.load_dotenv()

class GithubIssue:
    def __init__(self):
        token = os.getenv('GITHUB_TOKEN')
        self.headers = {"Accept": "application/vnd.github.v3+json", "Authorization" : f"token {token}"}
        #self.issue_url = "https://api.github.com/repos/TK-Entertainment/tkablent/issues"
        self.issue_url = "https://api.github.com/repos/TK-Entertainment/testing_repo/issues"
        
        self.errorcode_to_msg = {
            "VIDPRIVATE": "搜尋時，機器人偵測到該影片為私人影片",
            "FORMEMBERS": "搜尋時，機器人偵測到該影片為會員限定影片",
            "NOTSTARTED": "搜尋時，機器人偵測到該影片為尚未開始的直播",
            "UNAVAILIBLE": "搜尋時，機器人偵測到該影片為無法存取的影片",
            "PLAY_VIDPRIVATE": "播放時，機器人偵測到該影片為私人影片",
            "PLAY_FORMEMBERS": "播放時，機器人偵測到該影片為會員限定影片",
            "PLAY_NOTSTARTED": "播放時，機器人偵測到該影片為尚未開始的直播",
            "PLAY_UNAVAILIBLE": "播放時，機器人偵測到該影片為無法存取的影片",
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
        }


    def submit_bug(self, bot_name, guild, errorcode, timestamp, description, exception, video_url=None):
        if video_url is None:
            video_url = "無影片連結可用，或此類錯誤與歌曲播放無關"

        if "LocalDev" in bot_name:
            version = "master Branch / 本地開發版本"
        elif "Alpha" in bot_name or "Beta" in bot_name:
            version = "Alpha or Beta / 測試版本"
        else:
            version = "Stable / 正式版本"

        data = {
            "title": f"機器人錯誤回報表單 from {guild}",
            "body": f'''
**錯誤代碼**  
{errorcode} ({self.errorcode_to_msg[errorcode]})  
  
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

        requests.post(
            self.issue_url, 
            data=json.dumps(data),
            headers=self.headers
            )
        
        

        return

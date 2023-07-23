from enum import Enum

class JoinStrings(Enum):
    JoinSuccess = "成功加入語音頻道"
    JoinFail = "加入語音頻道時發生錯誤"
    LeaveSuccess = "成功離開語音頻道"
    LeaveFail = "離開語音頻道時發生錯誤"
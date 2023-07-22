from datetime import datetime
import os

class Essentials:
    def __init__(self):
        self.bot_version = os.getenv('BOT_VERSION')

    def get_current_year(self):
        # Just for fetching current year
        cdt = datetime.now().date()
        year = cdt.strftime("%Y")
        return year

    def sec_to_hms(self, seconds, format) -> str:
        sec = int(seconds%60)
        min = int(seconds//60%60)
        hr = int(seconds//60//60%24)
        day = int(seconds//86400)

        if format == "symbol":
            if day != 0:
                return "{}{}:{}{}:{}{}:{}{}".format("0" if day < 10 else "", day, "0" if hr < 10 else "", hr, "0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
            if hr != 0:
                return "{}{}:{}{}:{}{}".format("0" if hr < 10 else "", hr, "0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
            else:
                return "{}{}:{}{}".format("0" if min < 10 else "", min, "0" if sec < 10 else "", sec)
        
        elif format == "zh":
            if day != 0:
                return f"{day} 天 {hr} 小時 {min} 分 {sec} 秒"
            elif hr != 0: 
                return f"{hr} 小時 {min} 分 {sec} 秒"
            elif min != 0:
                return f"{min} 分 {sec} 秒"
            elif sec != 0:
                return f"{sec} 秒"
    
    def embed_opt(self, additional=""):
        year = self.get_current_year()
        if "ce" in self.bot_version:
            bot_name = "TKablent | 測試版"
        else:
            bot_name = "TKablent"

        return {
            'footer': {
                'text': f"{additional}{bot_name} | 版本: {self.bot_version}\nCopyright @ {year} TK Entertainment",
                'icon_url': "https://i.imgur.com/wApgX8J.png"
            },
        }
    
essentials = Essentials()
import os, datetime

bot_version = os.getenv('BOT_VERSION')

# Just for fetching current year
cdt = datetime.datetime.now().date()
year = cdt.strftime("%Y")

if "LOCAL DEVELOPMENT ONLY" in bot_version:
    caution_word = "DO NOT USE THIS VERSION OF CODE IN PRODUCTION"
else:
    caution_word = None

embed_opt = {
    'copyright_text': f"TKablent | 版本: {bot_version}\n{caution_word}\nCopyright @ {year} TK Entertainment",
    'icon_url': "https://i.imgur.com/wApgX8J.png"
}

def _sec_to_hms(seconds, format) -> str:
    sec = int(seconds%60); min = int(seconds//60%60); hr = int(seconds//60//60%24); day = int(seconds//86400)
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
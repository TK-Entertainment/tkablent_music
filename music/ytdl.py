import requests
import yt_dlp

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'music/%(extractor_key)s/%(title)s-%(id)s-.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': False,
    'no_warnings': True,
    'age-limit': 20,
    'default_search': 'auto',
    'cookies': 'youtube.com_cookies.txt',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDL:
    def __init__(self):
        self.api_key: str = None

    def get_info(self, song, url):
        # temporarily use ytdlp to download
        info = ytdl.extract_info(url, download=False)
        for k, v in info.items():
            setattr(song, k, v)
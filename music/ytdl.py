import pytube

class YTDL:
    def __init__(self):
        self.api_key: str = None

    def get_info(self, song, url):
        info = pytube.YouTube(url)
        setattr(song, 'title', info.title)
        setattr(song, 'author', info.author)
        setattr(song, 'channel_url', info.channel_url)
        setattr(song, 'song_url', info.watch_url)
        setattr(song, 'thumbnail', info.thumbnail_url)
        setattr(song, 'length', info.length)
        setattr(song, 'url', info.streams.first().url)
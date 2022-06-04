import pytube, yt_dlp
import pytube.exceptions

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDL:
    def __init__(self):
        self.api_key: str = None

    def is_playlist(self, url) -> bool:
        return 'youtube.com/playlist?list=' in url

    def get_url(self, url) -> str:
        try:
            return pytube.YouTube(url).streams.get_highest_resolution().url
        except pytube.exceptions.VideoPrivate or pytube.exceptions.MembersOnly as e:
            raise e
        except:
            return ytdl.extract_info(url, download=False)['url']

    def get_playlist(self, url) -> pytube.Playlist:
        urls = pytube.Playlist(url).video_urls
        for i in range(len(urls)-1):
            url = urls[i+1]
            print(url)
            yield url

    def get_playlist_id(self, url):
        return pytube.Playlist(url).playlist_id

    def get_first_video(self, url) -> str:
        playlist = pytube.Playlist(url)
        print(playlist.video_urls[0])
        return playlist.video_urls[0]

    def get_info(self, url) -> dict:
        try:
            song_info_dict = {}
            if ("http" not in url) and ("www" not in url):
                info = pytube.Search(url).results[0]
            else:
                info = pytube.YouTube(url)
                
                    # the value below is for high audio quality
            song_info_dict['video_id'] = info.video_id
            song_info_dict['title'] = info.title
            song_info_dict['author'] = info.author
            song_info_dict['channel_url'] = info.channel_url
            song_info_dict['watch_url'] = info.watch_url
            song_info_dict['thumbnail_url'] = info.thumbnail_url
            song_info_dict['length'] = info.length
            if info.length != 0:
                song_info_dict['stream'] = False
            else:
                song_info_dict['stream'] = True
        except pytube.exceptions.VideoPrivate or pytube.exceptions.MembersOnly as e:
            raise e
        except:
            try:
                print('[ytdlCore] Failsafe: Using yt_dlp')
                if ("http" not in url) and ("www" not in url):
                    info = ytdl.extract_info(url, download=False)['entries'][0]
                else:
                    info = ytdl.extract_info(url, download=False)

                song_info_dict['video_id'] = info['video_id']
                song_info_dict['title'] = info["title"]
                song_info_dict['author'] = info["uploader"]
                song_info_dict['channel_url'] = info["uploader_url"]
                song_info_dict['watch_url'] = info["webpage_url"]
                song_info_dict['thumbnail_url'] = info['thumbnail']
                song_info_dict['length'] = info['duration']
                if info['duration'] != 0:
                    song_info_dict['stream'] = False
                else:
                    song_info_dict['stream'] = True
            except Exception as e: 
                raise e
        return song_info_dict

        # Debugging Message
    #     if song.length != 0:
    #         print(f'''
    # Pytube Debug Info
    # Title: {song.title}
    # Author: {song.author}
    # Length: {song.length}sec
    # AudioCodec: {infohd.audio_codec}
    # Bitrate: {infohd.abr}
    #         ''')
    #     else:
    #         print(f'''
    # Pytube Debug Info
    # Title: {song.title}
    # Author: {song.author}
    # Length: It is a stream, how can you tell the length?
    # AudioCodec: Not availible
    # Bitrate: Not availible
    #         ''')
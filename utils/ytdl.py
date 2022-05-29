import pytube, yt_dlp


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

    def get_info(self, url) -> dict:
        try:
            song_info_dict = {}
            if ("http" not in url) and ("www" not in url):
                searchflag = True
                info = pytube.Search(url).results[0]
            else:
                searchflag = False
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
                infohd = info.streams.get_highest_resolution()
                song_info_dict['url'] = infohd.url
                song_info_dict['stream'] = False
            else:
                if searchflag == True:
                    url = info.watch_url
                streaminfo = ytdl.extract_info(url, download=False)
                song_info_dict['url'] = streaminfo['url']
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
                song_info_dict['url'] = info['url']
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
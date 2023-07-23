from enum import Enum, auto

INF = int(1e18)

class MultiType(Enum):
    VideoOnly = auto()
    Playlist = auto()

class SpotifyAlbum:
    def __init__(self):
        self.name: str = ""
        self.uri: str = ""
        self.artists: str = ""
        self.requester: str = ""
        self.thumbnail: str = ""
        self.tracks: list = []

class SpotifyPlaylist:
    def __init__(self):
        self.name: str = ""
        self.uri: str = ""
        self.artists: str = ""
        self.requester: str = ""
        self.thumbnail: str = ""
        self.tracks: list = []

class LoopState(Enum):
    NOTHING = auto()
    SINGLE = auto()
    PLAYLIST = auto()
    SINGLEINF = auto()
from enum import Enum, auto

class SpotifySearchType(Enum):
    TRACK = auto()
    ALBUM = auto()
    PLAYLIST = auto()

class SearchType(Enum):
    SPOTIFY = "spsearch"

    @classmethod
    def spotify(cls) -> str:
        return cls.SPOTIFY.value
    
class LoopState(Enum):
    NOTHING = auto()
    SINGLE = auto()
    PLAYLIST = auto()
    SINGLEINF = auto()

class LeaveType(Enum):
    ByCommand = auto()
    ByButton = auto()
    ByTimeout = auto()


class StopType(Enum):
    ByCommand = auto()
    ByButton = auto()

class ButtonType(Enum):
    RECOMMEND = 1
    HISTORY = 2
    OTHER = 3
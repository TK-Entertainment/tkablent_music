from enum import Enum, auto

class LeaveType(Enum):
    ByCommand = auto()
    ByButton = auto()
    ByTimeout = auto()

class StopType(Enum):
    ByCommand = auto()
    ByButton = auto()

class UIModule(Enum):
    ExceptionHandler = "ExceptionHandler"
    Help = "Help"
    InfoGenerator = "Info"
    Join = "Join"
    Leave = "Leave"
    PlayerControl = "PlayerControl"
    QueueControl = "QueueControl"
    Queue = "Queue"
    Search = "Search"
    Stage = "Stage"
    Misc = "Misc"

class Holiday(Enum):
    XmasEve = auto()
    Xmas = auto()
    NewYearEve = auto()
    NewYear = auto()
    ChineseNewYear = auto()
    NONE = auto()

class ColorCode(Enum):
    Red = auto()
    Green = auto()
    NONE = auto()

class Language(Enum):
    zh_tw = "zh_tw"
    en_us = "en_us"
# 完整更新日誌
```diff  
=========================================
Codename TKablent | Version Cutting Edge
Copyright 2022-present @ TK Entertainment
Shared under CC-NC-SS-4.0 license
=========================================
# Version 20220825.2-ce (01d6dfd)
+ 新增了 自動推薦歌曲 功能
# 註1: 目前不支援 Soundcloud 來源的音樂，需要另外點 Youtube/Spotify的音樂才能使用
# 註2: 推薦的歌曲不受到重複播放開關的影響，機器人不會重複播放推薦歌曲
# 註3: 不可以刪除/移動/交換推薦歌曲，且推薦歌曲會在手動播放歌曲後刪除，直到僅剩一首歌時會再自動推薦
+ 新增了 離開語音頻道 的按鈕
+ 跳過按鈕會在音樂播放最初的 5 秒暫時停用，以防止按太快當掉的問題
# 如果還是當掉了，點一首歌來讓它醒來

! 修復了有時顯示待播列表時，頁數會超過的問題
! 更新了正在播放介面的部分顯示方式
! 重新設計建議歌曲演算法，以解決建議偏掉的問題
! 修復了播放 Spotify 時，會把候播清單及正在播放介面搞壞的問題
! 增進了播放介面及其他有按鈕的介面之圖案大小
! 抓了一些小蟲子

# Version 20220822-ce (6511239)
+ [Core][UI] 新增對於 Spotify 播放清單及專輯的播放支援
# 注意，Spotify 歌曲尋找將會較 Youtube 緩慢
+ [UI] 播放資訊開始顯示播放來源

! [Core] 將搜尋伺服器獨立於播放伺服器，提供更穩定的播放體驗
! [UI] 跳過按鈕將會在只剩一首歌時，無法按下
! [Core][UI] 抓了一些小蟲子

# Version 20220813-ce (f5b7e68)
# Rebranded Alpha to Cutting Edge
+ [UI] Added help command
+ [UI] Added /np command
+ [Core] add "leave while inactive" feature
+ [UI][Core] Added playlist support
+ [UI] Added playing exception handler
+ [UI] Added bug reporting modal
+ [Proto] Added Github API
+ [Core][UI] Added slash command support
+ [UI] 新增對於混合連結的支援
+ [UI] Added playback control buttons
+ [UI] Spotify supported (audio source from youtube)

! [Core] Replaced pytube/yt-dlp with Lavalink (Wavelink)
! [Core] Replaced disnake with discord.py
! [Core][UI] Merged UI.SkipSucceed into UI.PlayingMsg
! [Core] Update garbage collector
! [Core] rewrite some functions
! [Core] Rewrite code for stage
! [UI] Organised UI functions
! [Core][UI] Catched few bugs

- [Core] Removed volume function

=========================================
Codename TKablent | Version Alpha
Copyright 2022-present @ TK Entertainment
Shared under CC-NC-SS-4.0 license
=========================================  

# Alpha 20220424 Update
+ [Core] Added timeout leaving function (after 10 minutes)
+ [Core] Added pause when nobody is in the voice channel
+ [Core] Added channel switching function
+ [Core][UI] Added Pytube/yt_dlp exception handler
# Private videos/Member-only videos/Unknown reason
+ [UI] Added showing number of all inqueue songs and total length on queue listing interface
+ [Core] Added requirements.txt to download all required packages and fixed version of pytube from kinshuk-h's repo
! [Github] Updated .gitignore to avoid testing file from uploading
! [UI] Updated sec_to_hms(Second to HourMinuteSecond) function to handle when video length is longer than 1 day
! [Github] Updated .gitignore file to prevent virtualenv directory from uploading
- [Core] Removed debugging message when exceptions were raised

# Alpha 20220417 Update 2
+ [UI] Added indicator when bot is searching for music source (typing indicator)
! [UI] Made "Seek, Replay, Loop, Remove, Swap, Move_to" UI standalone
# -> UI.SeekSucceed, UI.SeekFailed, UI.ReplaySucceed, UI.ReplayFailed, UI.LoopSucceed, UI.SingleLoopFailed, UI.RemoveSucceed, UI.RemoveFailed, UI.Embed_SwapSucceed, UI.SwapFailed, UI.MoveToSucceed, UI.MoveToFailed
! [Core] Fixed sec_to_hms function "hour won't show up" problem
! [Core] Fixed the problem that self.isskip and loopstate won't reset on mainloop done
! [UI][Core] Fixed various problem

# Alpha 20220417
+ Added "Queue" UI
+ Added Multiserver support (41f37a5 by @GrandTiger1729)
# UI.ShowQueue
! Made "Seek" UI standalone
# UI.SeekSucceed / UI.SeekFailed
! Rewrote Second to HourMinuteSecond(sec_to_hms) function
! Fixed SongInfo color conditions
! Fixed various problem

# Alpha 20220415 Update
! Made "Skip/Stop/Volume/Mute" UI standalone
# UI.SkipSucceed / UI.SkipFailed / UI.StopSucceed / UI.StopFailed / UI.VolumeAdjust / UI.VolumeAdjustFailed/ UI.MuteorUnmute
! This is not tested yet

# Alpha 20220415 Update
! Made "Resume" UI standalone
# UI.ResumeSucceed / UI.ResumeFailed
! Added alternative url gather method
# Just in case when pytube is not working, bot can call yt_dlp instead, though it is slower.

Known Issue:
! main.py has 1 problem
# on line 211 embed_op is not defined

# Alpha 20220410-2
+ 在 "正在播放" 及 "新增隊列" 訊息中加入 "待播清單"
# 因手機板排版，僅顯示第一首代播歌曲之名稱
! 完善 音量調整功能 (@GrandTiger1729 設計核心)
! 原碼中新增 本地伺服器用flag 提示
# 供未來調整為多人伺服器用時分辨
! 搜尋提示將會在搜尋完畢後被修改為 "新增至隊列" 訊息 或 被刪除

Known Issue:
! Queue related commands are not available yet
! Multiserver support is not available yet

# Alpha 20220410-1
+ Changing version from Confidential to Alpha
# 大部分功能皆以完備，僅剩部分功能尚未完成
# 此更新僅為版號更新，故更新內容繼承前一版更新
+ Added "Volume" messages
! Fixed volume adjust problem from last commit

Known Issue:
! Queue related commands are not available yet

=========================================
Codename TKablent | Version Confidential
Copyright 2022-present @ TK Entertainment
Shared under CC-NC-SS-4.0 license
=========================================  

# Build 20220410-2
+ Added "Volume" messages
! Fixed volume adjust problem from last commit

Known Issue:
! Queue related commands are not available yet

# Build 20220410-1
+ Added Search function
! Fixed Streaming function
! Fixed other interface problem and bugs

Known Issue:
! Queue related commands are not available yet

# Build 20220409-2
+ 新增 "Song.info" 提示訊息
! 修復了部分的錯誤

Known Issue:
! 無法播放直播影片
# 以上錯誤將會在核心以 Lavalink 重寫後，可能會得到解決
! 暫時不支援多個伺服器同時播放音樂

# Build 20220409-1
! Added play.Embed message for test

# Build 20220408-1
+ Added "Stop" "Replay" messages

# Build 20220402-1
! 修正部分介面表示方式
+ 新增 "Search" "Resume" "Pause" 的介面提示及錯誤訊息
+ 新增 TOKEN 啟動條件不足時，提示使用者進行更正的訊息

# Build 20220401-2
! 修正部分英文文法及語法問題

# Build 20220401-1
+ 增加後台 on_ready 時所提示的訊息
+ 增加前台 "Join" "Leave" 
```
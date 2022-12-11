# 完整更新日誌
目前總共發布 27 個版本  
穩定版 (Stable, s) 共 2 版  
*正在提供更新，更新周期較慢*

開發版 (Cutting Edge, ce) 共 10 版  
*仍舊提供更新，供嘗鮮用戶使用*

前期開發版 (Alpha) 共 7 版  
*已於 20220813 停止更新，由 Cutting Edge 代替*  

內部開發版 (Confidential) 共 8 版  
*已於 20220410 停止更新，由 Alpha 代替*
## December 2022
```diff  
=========================================
Codename TKablent | Version Stable
Copyright 2022-present @ TK Entertainment
Shared under CC-NC-SS-4.0 license
=========================================
# Version m.20221211.1-s (e0d8994, 緊急修復更新)
+【新增功能】新增了搜尋功能中可以翻頁的功能
#=> 以前機器人只能顯示出 24 個搜尋結果，現在可以透過翻頁來看更多的結果呦
!【修復】修復了你把搜尋結果餵給機器人，機器人會永久思考人生的問題
#=> 機器人會好好工作啦，不會再思考人生了ww
! 其餘更新接續 m.20221211-s，如下所示

# Version m.20221211-s (9f15b80)
# Rebranded Cutting Edge (ce) to Stable(s)
!【修復】修復了使用者不在語音頻道時，無法對已經在頻道內的機器人點歌的問題
#=> [Solved] 在頻道外的用戶無法正常點歌 | (ErrorFeedback-2022102401) by TKE (Discord 回報)
-【移除】移除了對傳統指令的支援
#=> 為使功能更加多元，以及使維護較為容易，我們正式將傳統指令從程式碼中移除，還請各位多多見諒
```
## October 2022
```diff
=========================================
Codename TKablent | Version Cutting Edge
Copyright 2022-present @ TK Entertainment
Shared under CC-NC-SS-4.0 license
=========================================
# Version m.20221023-ce (077296c)
- 【重要】因應 Discord 新政策，Youtube 連結點歌方式將會在未來版本中移除
#=> 總之，雖然很遺憾，但為了不要讓我們的機器人跟著 Youtube 連結一起寄了，大家還是忍耐一下~
#=> 你們還是可以用搜尋的方式啦 (新功能)，Spotify 及 Soundcloud 的連結點歌還是支援的喔~
+【新功能】新增搜尋結果選擇功能 (圖一)
#=> 哎呀，怎麼能忘記如此重要的功能呢？我們還加入了點播多個結果的功能喔~
+ 【新功能】新增 搜尋/新增歌曲 按鈕 (圖二)
#=> 手機用戶不用再打指令啦，點下去就可以點歌囉 (當然第一首歌還是得打指令啦)
!【修復】修復了使用推薦歌曲，但使用 /remove 後會沒播放推薦歌曲的問題
#=> [Solved] 待播清單指令應更新推薦系統，否則將會無法正常推薦 (會直接停止播放) | (ErrorFeedback-2022102301) by TKE (Discord 回報)
! 【恢復】恢復 10/20 停用的斜線指令
- 【移除】移除 /reportbug 及 /mtsetup 指令
#=> /reportbug 因群組功能完善而移除，/mtsetup 則因應新政策移除
- 【移除】移除對於混合連結的支援
#=> 同 /mtsetup 移除原因

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Version m.20221010-ce (緊急修復更新)
! 【緊急修正】修正 Spotify 單曲/播放清單 無法播放的問題
#=> [Solved] 没有办法播放... (ErrorFeedback-2022101001) by @Yanayo Shizuon (Discord 回報)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Version m.20221009-ce (緊急修復更新)
! 【緊急修正】修正當使用混合連結時，選擇影片選項會跳出錯誤，選擇播放清單則會沒反映的問題 (簡單說就是沒辦法正常播放)

```
## September 2022
```diff
# Version m.20220918.1-ce (ce1b846)
! 【改進】重新設計了重複播放模式與推薦歌曲的機制
#=> 若目前播放的歌曲為自行播放的 (非系統推薦):
#       推薦歌曲將會在重複播放功能未啟動時才會作動
#       若開啟任意重複播放功能後，將暫時不會推薦歌曲
#=> 若目前播放的歌曲為推薦歌曲:
#       除單一重複播放外，其餘將仍推薦新歌曲，並會在原歌曲播放完後跳至下一首 (包含全待播清單亦同)
! 其餘更新接續 m.20220918-ce，如下所示

# Version m.20220918-ce (20f1e0a)
+【新增】新增隨機排列待播清單的按鈕及指令 (/shuffle)
#=> 下次如果覺得播放清單總是依照原本的順序播放很不爽，可以用這個功能來重新排列~
! 【修復】解決了 /np 無法正常使用的問題
#=> 可以再重新叫出目前播放的歌曲及播放控制介面啦
!【維護】暫時停用獨立搜尋伺服器，回滾為單伺服器處理模式
#=> 因搜尋伺服器需進行例行性的維護，將暫時停用獨立搜尋伺服器，使用單一伺服器處理

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Version m.20220911-ce (743e9db)
+【新增】成功加入待播清單的訊息將以點歌者才能看到的形式傳出 (僅限斜線指令可使用)
#=> 未來會將這個功能擴展到其他指令上，請踴躍使用新的斜線指令呦~
! 【改進】改進了當使用全待播清單重播時，並隊列中只有一首歌時，機器人會刷版面的問題
#=> [Closed] 關於重複播放的困擾 (Suggestion-22090401) by @冰系單手劍少女
! 【改進】歌曲資訊將不會一直傳出，改為使用編輯的方式顯示，以減少刷版面的問題
#=> 如果控制介面因為聊天跑太上去，可以使用 /np 再把它生出來喔
!【修正】修正了部分伺服器無法正確讀取到 Emoji 的問題 (標題前面會變成 youtube)
#=> 若 Emoji 仍舊無法正常顯示，請到錯誤回報區告訴我~
!【修正】修正了重複播放系統的邏輯
#=> 使用跳過後，若處於單曲重播狀態，將會解除單曲重播
#=> 若處於全待播清單重播狀態，仍然會移除跳過的歌曲，重複播放剩餘的歌曲
!【改進】版本號格式改為 m.yyyymmdd(.rev)-ce
#=> 因應未來規畫而更改
```
## August 2022
```diff
# Version 20220825.3-ce
! 修正了建議歌曲演算法，將來源更換為 Youtube Music

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

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Version 20220822-ce (6511239)
+ [Core][UI] 新增對於 Spotify 播放清單及專輯的播放支援
# 注意，Spotify 歌曲尋找將會較 Youtube 緩慢
+ [UI] 播放資訊開始顯示播放來源

! [Core] 將搜尋伺服器獨立於播放伺服器，提供更穩定的播放體驗
! [UI] 跳過按鈕將會在只剩一首歌時，無法按下
! [Core][UI] 抓了一些小蟲子

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
```
## April 2022
```diff
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

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Alpha 20220415 Update
! Made "Skip/Stop/Volume/Mute" UI standalone
# UI.SkipSucceed / UI.SkipFailed / UI.StopSucceed / UI.StopFailed / UI.VolumeAdjust / UI.VolumeAdjustFailed/ UI.MuteorUnmute
! This is not tested yet

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Alpha 20220415 Update
! Made "Resume" UI standalone
# UI.ResumeSucceed / UI.ResumeFailed
! Added alternative url gather method
# Just in case when pytube is not working, bot can call yt_dlp instead, though it is slower.

Known Issue:
! main.py has 1 problem
# on line 211 embed_op is not defined

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Build 20220409-2
+ 新增 "Song.info" 提示訊息
! 修復了部分的錯誤

Known Issue:
! 無法播放直播影片
# 以上錯誤將會在核心以 Lavalink 重寫後，可能會得到解決
! 暫時不支援多個伺服器同時播放音樂

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Build 20220409-1
! Added play.Embed message for test

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Build 20220408-1
+ Added "Stop" "Replay" messages

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Build 20220402-1
! 修正部分介面表示方式
+ 新增 "Search" "Resume" "Pause" 的介面提示及錯誤訊息
+ 新增 TOKEN 啟動條件不足時，提示使用者進行更正的訊息

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Build 20220401-2
! 修正部分英文文法及語法問題

# Build 20220401-1
+ 增加後台 on_ready 時所提示的訊息
+ 增加前台 "Join" "Leave" 
```
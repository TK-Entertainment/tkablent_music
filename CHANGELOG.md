# 完整更新日誌
> **ℹ️ 注意**  
> 此處為純文字更新日誌，若要查看完成含圖片的分版日誌  
> 可到 [Releases](https://github.com/TK-Entertainment/tkablent_music/releases) 查看

目前總共發布 51 個版本  
穩定版 (Stable, s) 共 13 版 | *正在提供更新，更新周期較慢*  
*目前更新到 m.20230716.6-s*  

開發版 (Cutting Edge, ce) 共 23 版 | *仍舊提供更新，供嘗鮮用戶使用*  
*目前更新到 m.20231209.linkandui-ce*  

前期開發版 (Alpha) 共 7 版 | *已於 20220813 停止更新，由 Cutting Edge 代替*  
*最後更新到 Alpha 20220424 Update*  

內部開發版 (Confidential) 共 8 版 | *已於 20220410 停止更新，由 Alpha 代替*  
*最後更新到 # Build 20220410-2*
# December 2023
```
=========================================
Codename TKablent | Version Stable
Copyright 2022-present @ TK Entertainment
Shared under MIT license
=========================================
```
## Version m.20230716.6-s
#### From Cutting Edge | m.20231209.linkandui-ce
```diff
!【重要】此為 linkandui 測試項目的最終版本
=> 此版本為 linkandui 測試項目的最終版本，將在下一次更新 ce 版時轉移至下一個測試項目 wavelink30-depend 開始全新核心的測試
=> 因測試版機器人目前使用人數較少，故此次將不進行退群動作
=> 因配合新核心測試工作，穩定版將暫緩更新。請稍待新測試項目穩定後即會恢復

!【優化】大幅加速搜尋提示字及本地緩存儲存處理速度
=> 優化終於來啦，這次是個大的
=> 經過內部測試，在相同環境、相同候選字、皆無快取的情況下
=> 搜尋速度加快超過 5 倍速度，本地緩存儲存速度則加快約 1.4 倍
=> 詳情可至 https://github.com/TK-Entertainment/tkablent_music/releases/tag/m.20231209.linkandui-ce 查看

+【新增】新增各伺服器的更新資訊推送
=> 考慮到並非所有使用者都有加入本群組，機器人自本版本起會在該伺服器更新後第一次傳送要求時傳送更新資訊，讓所有使用者知道我們準備了什麼好料的 (owob)
```

## Version m.20230716.5-s
#### From Cutting Edge | m.20231205.linkandui-ce
```diff
!【優化】增加機器人穩定度及修正部分問題
=> 重新編寫機器人對於搜尋結果本地快取的儲存方法，以防止機器人因進行快取儲存時導致的無回應狀態
=> 詳情可至 https://github.com/TK-Entertainment/tkablent_music/releases/tag/m.20231205.linkandui-ce 查看

+【新增】新增播放伺服器服務提供商的資訊
=> 特別感謝 404 Network Information Co. 對本專案的支援
=> 可到 https://hello.simple.taipei/ 了解他們！
```

# September 2023
## Version m.20230716.4-s (PR [#20](https://github.com/TK-Entertainment/tkablent_music/pull/20))
#### From Cutting Edge | m.20230922.linkandui-ce
```diff
!【問卷】結束 2023/08 滿意度調查 
=> 感謝您們的回覆，我們已收到您的意見及想法

!【優化】增加程式可靠性
=> 刪除部分以字串作為辨識的程式段，以邏輯判斷為主
=> 順應修復以往以字串辨識時，Wavelink 會發生 NotImplemented 錯誤的問題

!【優化】新增緩存損毀時，相應的應對方式
=> 採A/B Copy的方式，在A Copy損毀時，以B Copy作為備援並還原之
```

# August 2023
## Version m.20230716.3-s ([2179adc](https://github.com/TK-Entertainment/tkablent_music/blob/m.20230806.linkandui-ce/2179adcd4a09a6fa425e72ae2e58e561b63b7b16))
#### From Cutting Edge | m.20230806.linkandui-ce
> **ℹ️ 注意**  
> m.20230716.2-s skipped as it's a internal test version
```diff
+【問卷】開始 2023/08 滿意度調查
=> 此更新後，機器人將會在執行指令時提示可以填寫滿意度的表單，歡迎各位使用者給予我們意見！

!【優化】對於要求過多的處理
=> 目前已經嘗試對要求過多的問題進行處理，將會再觀察情況進行進一步優化
```
# July 2023
## Version m.20230716.1-s ([6d3c90b](https://github.com/TK-Entertainment/tkablent_music/blob/m.20230721.linkandui-ce/6d3c90b990975da2c97c744ae771379826d9e093))
#### From Cutting Edge | m.20230721.linkandui-ce
```diff
!【優化】增加獨立播放伺服器，並對搜尋伺服器做負載平衡
=> 現有一播放伺服器 (不進行搜尋，專供穩定播放) 及 兩台搜尋伺服器 (進行負載平衡)

!【優化】對於指令搜尋候選字功能進行速度上的優化及部分改進
=> 增加緩存來減少搜尋的次數，及透過搜尋伺服器的負載平衡來加快搜尋速度
=> 候選字刪去音樂作者名稱，讓音樂名稱可以顯示得更長

!【修正】修正在開啟/關閉推薦功能時，多次觸發造成錯誤
=> 當有人按下某個按鈕，機器人正在處理之時，該按鈕會暫時停用以防止多次觸發
```
## Version m.20230716.e2-s (緊急修復更新, [e9e1870](https://github.com/TK-Entertainment/tkablent_music/commit/e9e1870cfbe2f6769858d465ea2f796e5d5c708f))
```diff
!【緊急修復】修正使用待播清單管理功能時 (如 /move, /swap)，會遇到錯誤的問題
=> 因在更新套件時有部分程式碼尚未轉換成新版格式，導致執行指令時會出現錯誤
=> 在此版本已經修復此問題
```
## Version m.20230716.e1-s (緊急修復更新, [bd78cb2](https://github.com/TK-Entertainment/tkablent_music/commit/bd78cb2fe6f87857a8a73ef07d675098772b218c))
```diff
!【緊急修復】修正點播部分播放清單時，無法正常點播的問題
=> 在此版本已經修復此問題

!【修正】新版 /help 文件中，填寫指令名稱錯誤
=> /mtsetup --> /playwith
=> 在此版本已經修復此問題
```
## Version m.20230716-s
#### From Cutting Edge | m.20230716.linkandui-ce ([64d2be3](https://github.com/TK-Entertainment/tkablent_music/commit/64d2be3b9e43089a5db49e50591a91e0ccc17697))
```diff
!【改變】重新設計 /help 求助介面 
=> 這玩意是很久之前做的，已經太久沒更新了
=> 順便寫成比較好閱讀的樣子，也附上了相關排錯指引
=> 同時也修改成了只有執行者能看到的形式

!【改變】退出語音頻道的訊息整合到播放介面中 (via DynEmbed)
=> 這個概念一樣是來自於 DynEmbed，盡量將所有訊息整合在單一介面來減少刷頻的問題

!【改變】完成播放的訊息整合到播放介面中 (via DynEmbed)
=> 概念同上，在退出語音頻道的訊息傳出後 3 秒即會變成此訊息

!【優化】優化部分程式碼 (推薦系統)
=> Done DRY programming on suggestion system
=> _get_suggest_track(...) / _process_resuggestion(...) / _search_for_suggestion (...) @ utils\playlist.py
=> Reference: https://github.com/TK-Entertainment/tkablent_music/commit/64d2be3b9e43089a5db49e50591a91e0ccc17697
```
#### From Cutting Edge | m.20230712.1.linkandui-ce ([226a2d8](https://github.com/TK-Entertainment/tkablent_music/commit/226a2d83c9ad3d87ea20e9189be932347316bbc6))
```diff
!【改變】重新設計無人暫停的介面
=> 有任何更改的設計建議也可以到 Issue 跟我們說呦

!【修復】修正無法透過按鈕退出語音頻道的問題

!【修復】修正無法透過按鈕調用待播清單列表的問題

!【修復】修正無人暫停後，控制按鈕的部分行為
=> 無人在頻道，機器人暫停後，現在會停用「播放/暫停」、「跳過」及「自動建議控制」按鍵
=> 並在有人重新進入頻道後，跳過會正常依是否有可供跳過的歌曲來正常重新啟用/保持停用
```
#### From Cutting Edge | m.20230712.linkandui-ce ([fe837cc](https://github.com/TK-Entertainment/tkablent_music/commit/fe837cc826ff1c79cbd82b8523dbb93511c75c1e))
```diff
!【修正】修正部分時候搜尋失敗的問題 
=> 部分歌曲名稱或作者名稱過長，導致搜尋結果模組出問題
=> 此版本已修正此問題

!【修正】修正混和連結無法記住設定的問題
```
#### From Cutting Edge | m.20230711.linkandui-ce ([0c724dd](https://github.com/TK-Entertainment/tkablent_music/commit/0c724ddc2e3d5be0507252d937f1f7abacfad792) / [265717c](https://github.com/TK-Entertainment/tkablent_music/commit/265717c65ffb6d7b52955e3122ca80606424369b) / [ca19022](https://github.com/TK-Entertainment/tkablent_music/commit/ca1902259d793c7c8a7e1da62d2ad05f6852661d) / [138434f](https://github.com/TK-Entertainment/tkablent_music/commit/138434f3288f95e9dba88fe87782c6bfd1787d4a) / [9edb743](https://github.com/TK-Entertainment/tkablent_music/commit/9edb74338b1158150e209e19fe3726ae1cbb9d43))
```diff
!【改變】重新設計播放介面的排版 (0c724dd)
=> 上圖為目前設計，下圖為新設計，有任何更改的設計建議也可以到 Issue 跟我們說呦

!【優化】優化維護播放之系統 (0c724dd)
=> 從迴圈修改為 Event listener 的方式來維護歌曲播放
=> 可能會增進一點效能(?

!【修正】修正自動退出之計時啟動問題 (265717c) / (ca19022) / (138434f)
=> 重新調整自動退出的計時器之啟動時機，以正常地在未播放歌曲的十分鐘後自動推出
=> 以減少機器人伺服器端的效能開銷

!【修正】修正 /seek 及 /restart 指令無法使用的問題 (9edb743)

!【修正】修正 /seek 之時間顯示異常的問題 (9edb743)
=> 因套件更新後，原回傳值為秒，更新後變為毫秒，導致轉換出現問題
=> 在此版本已經修復此問題

!【優化】部分指令之提示已轉換成 Ephemeral (僅傳送者看得到) 的格式 (9edb743)
=> 目前執行失敗、/restart及/seek指令之提示皆改為此種形式
=> 未來會將所有提示改為該格式
```
#### From Cutting Edge | m.20230708.linkandui-ce ([482b161](https://github.com/TK-Entertainment/tkablent_music/commit/482b161b47935f3bc2fb0249145a93139fb135f6))
```diff
!【優化】修正點歌系統排錯問題 (482b161)
=> 點歌指令在接收點播之字串時，以往機器人無法很好的辨別傳入的是否為網址而導致機器人當機
=> 在此版本已經修復此問題
```
#### From Cutting Edge | m.20230629.linkandui-ce ([1898988](https://github.com/TK-Entertainment/tkablent_music/commit/18989886389cc7f346ac72b1c94030bc9e36cdc1) / [1cb3ea5](https://github.com/TK-Entertainment/tkablent_music/commit/1cb3ea56f9686c8d5e7a0abd808c0ccc824f5903) / PR [#18](https://github.com/TK-Entertainment/tkablent_music/pull/18) / PR [#19](https://github.com/TK-Entertainment/tkablent_music/pull/19))
```diff
!【優化】刪除部分棄用模組 (1898988 / 1cb3ea5)
=> 因傳統指令已於 **m.20221211-s** 結束支援，我們正式從程式碼刪除轉換模組，以減少機器人執行開銷及加快些許速度
=> utils.Command (Contexts and Interaction handler) deprecated in this release
!【套件】更新依賴套件並修改語法 (PR #18 / #19) 
=> Wavelink version bumped to v2.5.1
!【優化】優化搜尋/點歌模組 (1cb3ea5)
=> 優化及改善搜尋之準確性，並還原了些許功能
```
# June 2023
## Version m.20230611.1-s (8a4d564)
```diff
+【更改】重複播放標示的顯示方式
#=> 因為 DynEmbed 有點弄不出來，只好先下放一些部分功能到穩定版啦
#=> 先下放重複播放的標示方式，如圖

!【修正】重複播放按鈕的邏輯
#=> 這其實是一個遠古的問題，最近才發現 /w\
#=> 在輸入 /loop [次數] 後，介面不再多出同樣的重複圖案，而是顯示次數 (如果有指定次數的話)
```
## Version m.20230611-s (/)
#### From Beta m.20230609.wl2.0-ce
```diff
+【更新】機器人播放伺服器連接套件更新
#=> Wavelink version bumped to v2.4.0

+【優化】程式碼部分優化，增進機器人效能
```
#### From Beta m.20230611.wl2.0-ce
```diff
!【更改】播放及新增歌曲介面下，點歌者姓名顯示方式更改
#=> 因應 Discord 近期對於使用者名稱系統的更動，部分使用者已經更改成無後輟碼的新使用者名稱格式，故機器人修正部分顯示問題 (本來會顯示#0) (我知道有些人很不爽這個變更，但沒辦法ww)
#仍持有舊使用者名稱者會以左圖形式顯示，新的則會以右圖形式顯示
#可參 Discord 官方部落格說明: https://discord.com/blog/usernames
```

# December 2022
## Version m.20221225-s (da903c5)
```diff  
+【新增】新增節慶特別主題及問候語
#=> 機器人現在會在部分特定節慶時，套用符合該節慶的顏色主題及問候語~

!【修復】修復了在上次更新後，就壞掉的搜尋多選功能
```
## Version m.20221211.1-s (e0d8994, 緊急修復更新)
```diff
+【新增功能】新增了搜尋功能中可以翻頁的功能
#=> 以前機器人只能顯示出 24 個搜尋結果，現在可以透過翻頁來看更多的結果呦

!【修復】修復了你把搜尋結果餵給機器人，機器人會永久思考人生的問題
#=> 機器人會好好工作啦，不會再思考人生了ww

! 其餘更新接續 m.20221211-s，如下所示
```
## Version m.20221211-s (9f15b80)
#### Rebranded Cutting Edge (ce) to Stable(s)
```diff
!【修復】修復了使用者不在語音頻道時，無法對已經在頻道內的機器人點歌的問題
#=> [Solved] 在頻道外的用戶無法正常點歌 | (ErrorFeedback-2022102401) by TKE (Discord 回報)
-【移除】移除了對傳統指令的支援
#=> 為使功能更加多元，以及使維護較為容易，我們正式將傳統指令從程式碼中移除，還請各位多多見諒
```
# October 2022
## Version m.20221023-ce (077296c)
```
=========================================
Codename TKablent | Version Cutting Edge
Copyright 2022-present @ TK Entertainment
Shared under CC-NC-SS-4.0 license
=========================================
```
```diff
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
```
## Version m.20221010-ce (緊急修復更新)
```diff
! 【緊急修正】修正 Spotify 單曲/播放清單 無法播放的問題
#=> [Solved] 没有办法播放... (ErrorFeedback-2022101001) by @Yanayo Shizuon (Discord 回報)
```
## Version m.20221009-ce (緊急修復更新)
```diff
! 【緊急修正】修正當使用混合連結時，選擇影片選項會跳出錯誤，選擇播放清單則會沒反映的問題 (簡單說就是沒辦法正常播放)
```
# September 2022
## Version m.20220918.1-ce (ce1b846)
```diff
! 【改進】重新設計了重複播放模式與推薦歌曲的機制
#=> 若目前播放的歌曲為自行播放的 (非系統推薦):
#       推薦歌曲將會在重複播放功能未啟動時才會作動
#       若開啟任意重複播放功能後，將暫時不會推薦歌曲
#=> 若目前播放的歌曲為推薦歌曲:
#       除單一重複播放外，其餘將仍推薦新歌曲，並會在原歌曲播放完後跳至下一首 (包含全待播清單亦同)

! 其餘更新接續 m.20220918-ce，如下所示
```
## Version m.20220918-ce (20f1e0a)
```diff
+【新增】新增隨機排列待播清單的按鈕及指令 (/shuffle)
#=> 下次如果覺得播放清單總是依照原本的順序播放很不爽，可以用這個功能來重新排列~

! 【修復】解決了 /np 無法正常使用的問題
#=> 可以再重新叫出目前播放的歌曲及播放控制介面啦

!【維護】暫時停用獨立搜尋伺服器，回滾為單伺服器處理模式
#=> 因搜尋伺服器需進行例行性的維護，將暫時停用獨立搜尋伺服器，使用單一伺服器處理
```
## Version m.20220911-ce (743e9db)
```diff
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
# August 2022
## Version 20220825.3-ce
```diff
! 修正了建議歌曲演算法，將來源更換為 Youtube Music
```
## Version 20220825.2-ce (01d6dfd)
```diff
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
```
## Version 20220822-ce (6511239)
```diff
+ [Core][UI] 新增對於 Spotify 播放清單及專輯的播放支援
# 注意，Spotify 歌曲尋找將會較 Youtube 緩慢
+ [UI] 播放資訊開始顯示播放來源

! [Core] 將搜尋伺服器獨立於播放伺服器，提供更穩定的播放體驗
! [UI] 跳過按鈕將會在只剩一首歌時，無法按下
! [Core][UI] 抓了一些小蟲子
```
## Version 20220813-ce (f5b7e68)
#### Rebranded Alpha to Cutting Edge
```diff
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
# April 2022
```
=========================================
Codename TKablent | Version Alpha
Copyright 2022-present @ TK Entertainment
Shared under CC-NC-SS-4.0 license
=========================================
```
## Alpha 20220424 Update
```diff
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
```
## Alpha 20220417 Update 2
```diff
+ [UI] Added indicator when bot is searching for music source (typing indicator)
! [UI] Made "Seek, Replay, Loop, Remove, Swap, Move_to" UI standalone
# -> UI.SeekSucceed, UI.SeekFailed, UI.ReplaySucceed, UI.ReplayFailed, UI.LoopSucceed, UI.SingleLoopFailed, UI.RemoveSucceed, UI.RemoveFailed, UI.Embed_SwapSucceed, UI.SwapFailed, UI.MoveToSucceed, UI.MoveToFailed
! [Core] Fixed sec_to_hms function "hour won't show up" problem
! [Core] Fixed the problem that self.isskip and loopstate won't reset on mainloop done
! [UI][Core] Fixed various problem
```
## Alpha 20220417
```diff
+ Added "Queue" UI
+ Added Multiserver support (41f37a5 by @GrandTiger1729)
# UI.ShowQueue
! Made "Seek" UI standalone
# UI.SeekSucceed / UI.SeekFailed
! Rewrote Second to HourMinuteSecond(sec_to_hms) function
! Fixed SongInfo color conditions
! Fixed various problem
```
## Alpha 20220415 Update
```diff
! Made "Skip/Stop/Volume/Mute" UI standalone
# UI.SkipSucceed / UI.SkipFailed / UI.StopSucceed / UI.StopFailed / UI.VolumeAdjust / UI.VolumeAdjustFailed/ UI.MuteorUnmute
! This is not tested yet
```
## Alpha 20220415 Update
```diff
! Made "Resume" UI standalone
# UI.ResumeSucceed / UI.ResumeFailed
! Added alternative url gather method
# Just in case when pytube is not working, bot can call yt_dlp instead, though it is slower.

Known Issue:
! main.py has 1 problem
# on line 211 embed_op is not defined
```
## Alpha 20220410-2
```diff
+ 在 "正在播放" 及 "新增隊列" 訊息中加入 "待播清單"
# 因手機板排版，僅顯示第一首代播歌曲之名稱
! 完善 音量調整功能 (@GrandTiger1729 設計核心)
! 原碼中新增 本地伺服器用flag 提示
# 供未來調整為多人伺服器用時分辨
! 搜尋提示將會在搜尋完畢後被修改為 "新增至隊列" 訊息 或 被刪除

Known Issue:
! Queue related commands are not available yet
! Multiserver support is not available yet
```
## Alpha 20220410-1
```diff
+ Changing version from Confidential to Alpha
# 大部分功能皆以完備，僅剩部分功能尚未完成
# 此更新僅為版號更新，故更新內容繼承前一版更新
+ Added "Volume" messages
! Fixed volume adjust problem from last commit

Known Issue:
! Queue related commands are not available yet
```
## Build 20220410-2
```
=========================================
Codename TKablent | Version Confidential
Copyright 2022-present @ TK Entertainment
Shared under CC-NC-SS-4.0 license
=========================================  
```
```diff
+ Added "Volume" messages
! Fixed volume adjust problem from last commit

Known Issue:
! Queue related commands are not available yet
```
## Build 20220410-1
```diff
+ Added Search function
! Fixed Streaming function
! Fixed other interface problem and bugs

Known Issue:
! Queue related commands are not available yet
```
## Build 20220409-2
```diff
+ 新增 "Song.info" 提示訊息
! 修復了部分的錯誤

Known Issue:
! 無法播放直播影片
# 以上錯誤將會在核心以 Lavalink 重寫後，可能會得到解決
! 暫時不支援多個伺服器同時播放音樂
```
## Build 20220409-1
```diff
! Added play.Embed message for test
```
## Build 20220408-1
```diff
+ Added "Stop" "Replay" messages
```
## Build 20220402-1
```diff
! 修正部分介面表示方式
+ 新增 "Search" "Resume" "Pause" 的介面提示及錯誤訊息
+ 新增 TOKEN 啟動條件不足時，提示使用者進行更正的訊息
```
## Build 20220401-2
```diff
! 修正部分英文文法及語法問題
```
## Build 20220401-1
```diff
+ 增加後台 on_ready 時所提示的訊息
+ 增加前台 "Join" "Leave" 
```

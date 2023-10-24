<img src="https://i.imgur.com/wApgX8J.png" height=64 width=64></img>
### A Project of TK Entertainment
# TKablent
[![TKablent 支援伺服器](https://discordapp.com/api/guilds/1010564921005707335/widget.png?style=shield)](https://discord.gg/9qrpGh4e7V)
[![最新更新](https://img.shields.io/github/release/tk-entertainment/tkablent_music.svg)](https://github.com/tk-entertainment/tkablent_music/releases/latest)
[![CodeFactor](https://www.codefactor.io/repository/github/tk-entertainment/tkablent_music/badge)](https://www.codefactor.io/repository/github/tk-entertainment/tkablent_music)  
用 Python 製作的 Discord 音樂機器人  

> **Note**  
> 目前程式碼架構正在重構中，正式版/測試版更新會變得較不積極  
> 詳請可見 [structure_rev](https://github.com/TK-Entertainment/tkablent_music/tree/structure_rev) 分支，敬請諒解

## 邀請機器人
**邀請穩定版機器人** (後輟為 -s)  
[![](https://dcbadge.vercel.app/api/shield/1018410580870176788?bot=true)](https://discord.com/oauth2/authorize?client_id=1018410580870176788&permissions=2201184336&scope=bot%20applications.commands)  
  
**邀請測試版機器人** (後輟為 -ce)  
> **Warning**  
> **此機器人運行的是測試版軟體**  
> 可能會極度不穩定 (遇到許多奇怪的問題)，甚至不定時重開，但能在第一時間取得新增的功能及特性
> 若想要取得最新的功能，可以考慮看看，也希望使用此版本的使用者可以多多提交 Bug 回饋
  
> **Important**  
> **關於測試版機器人的相關策略**  
> 此機器人會限制在 100 個伺服器 (因未驗證)，故每次完成一個測試階段 (即測試項目改變時)，機器人將會自動退出伺服器  
> 若要再使用者，機器人會在退出後留下訊息，上方有按鈕可供快速加入，請在機器人滿人前加入，感謝
  
[![](https://dcbadge.vercel.app/api/shield/852909666987147295?bot=true)](https://discord.com/api/oauth2/authorize?client_id=852909666987147295&permissions=2201184336&scope=bot%20applications.commands)  
## 開發狀態
源碼 (Source Code):   
*be3d87a (20230922)*

穩定版 (Stable, s) | *正在提供更新，更新周期較慢*  
*目前更新到 m.20230716.4-s*  

開發版 (Cutting Edge, ce) | *仍舊提供更新，供嘗鮮用戶使用*  
*目前測試項目: 搜尋系統及使用者介面優化 (linkandui)*  
*目前更新到 m.20230922.linkandui-ce*  

前期開發版 (Alpha) | *已於 20220813 停止更新，由 Cutting Edge 代替*  
*最後更新到 Alpha 20220424 Update*  

內部開發版 (Confidential) | *已於 20220410 停止更新，由 Alpha 代替*  
*最後更新到 # Build 20220410-2*

## 版本命名規則
**[functioncode].[releasedate].[subversion].[testsubject]-[releasetype]**  
  
**functioncode**:  
代表發行的功能類型，音樂功能為 **m**，未來會在發行其他功能時另有表格參考  
**releasedate**:  
主要的分版方法，表有較重大功能更新或修復，依當下發行之時間日期作為版號，格式為 **YYYYMMDD**  
**subversion**:  
副要的分版方法，表較小的修復及功能更新或同日發布之多次更新，若為一般更新以數字迭代 (從 **1** 開始)，若為緊急更新則以 **e[版號]** 迭代  
**testsubject**:  
代表測試項目，僅在 releasetype 為 ce (Cutting Edge 測試版) 時會出現，會填入該次測試項目的 Codename  
**releasetype**:  
代表發行類型，穩定版為 **s**，測試版為 **ce**

## 最新更新日誌 
如需觀看更詳細的 Github commits 日誌，請點下方連結  
[m.20230611.1-s...m.20230922.linkandui-ce](https://github.com/TK-Entertainment/tkablent/compare/m.20230611.1-s...m.20230922.linkandui-ce)

```diff
=========================================
Codename TKablent | Version Stable
Copyright 2022-present @ TK Entertainment
Shared under MIT License
=========================================
# Version m.20230716.4-s (PR #20)
## From Cutting Edge | m.20230922.linkandui-ce
!【問卷】結束 2023/08 滿意度調查 
=> 感謝您們的回覆，我們已收到您的意見及想法
!【優化】增加程式可靠性
=> 刪除部分以字串作為辨識的程式段，以邏輯判斷為主
=> 順應修復以往以字串辨識時，Wavelink 會發生 NotImplemented 錯誤的問題
!【優化】新增緩存損毀時，相應的應對方式
=> 採A/B Copy的方式，在A Copy損毀時，以B Copy作為備援並還原之

# Version m.20230716.3-s (2179adc)
## From Cutting Edge | m.20230806.linkandui-ce
## m.20230716.2-s skipped as it's a internal test version
+【問卷】開始 2023/08 滿意度調查
=> 此更新後，機器人將會在執行指令時提示可以填寫滿意度的表單，歡迎各位使用者給予我們意見！
!【優化】對於要求過多的處理
=> 目前已經嘗試對要求過多的問題進行處理，將會再觀察情況進行進一步優化

# Version m.20230716.1-s (6d3c90b)
## From Cutting Edge | m.20230721.linkandui-ce
!【優化】增加獨立播放伺服器，並對搜尋伺服器做負載平衡
=> 現有一播放伺服器 (不進行搜尋，專供穩定播放) 及 兩台搜尋伺服器 (進行負載平衡)
!【優化】對於指令搜尋候選字功能進行速度上的優化及部分改進
=> 增加緩存來減少搜尋的次數，及透過搜尋伺服器的負載平衡來加快搜尋速度
=> 候選字刪去音樂作者名稱，讓音樂名稱可以顯示得更長
!【修正】修正在開啟/關閉推薦功能時，多次觸發造成錯誤
=> 當有人按下某個按鈕，機器人正在處理之時，該按鈕會暫時停用以防止多次觸發

# Version m.20230716.e2-s (緊急修復更新, e9e1870)
!【緊急修復】修正使用待播清單管理功能時 (如 /move, /swap)，會遇到錯誤的問題
=> 因在更新套件時有部分程式碼尚未轉換成新版格式，導致執行指令時會出現錯誤
=> 在此版本已經修復此問題

# Version m.20230716.e1-s (緊急修復更新, bd78cb2)
!【緊急修復】修正點播部分播放清單時，無法正常點播的問題
=> 在此版本已經修復此問題

!【修正】新版 /help 文件中，填寫指令名稱錯誤
=> /mtsetup --> /playwith
=> 在此版本已經修復此問題

# Version m.20230716-s
## From Cutting Edge | m.20230629.linkandui-ce
!【優化】刪除部分棄用模組 (1898988 / 1cb3ea5)
=> 因傳統指令已於 **m.20221211-s** 結束支援，我們正式從程式碼刪除轉換模組，以減少機器人執行開銷及加快些許速度
=> utils.Command (Contexts and Interaction handler) deprecated in this release
!【套件】更新依賴套件並修改語法 (PR #18 / #19) 
=> Wavelink version bumped to v2.5.1
!【優化】優化搜尋/點歌模組 (1cb3ea5)
=> 優化及改善搜尋之準確性，並還原了些許功能

## From Cutting Edge | m.20230708.linkandui-ce
!【優化】修正點歌系統排錯問題 (482b161)
=> 點歌指令在接收點播之字串時，以往機器人無法很好的辨別傳入的是否為網址而導致機器人當機
=> 在此版本已經修復此問題

## From Cutting Edge | m.20230711.linkandui-ce
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

## From Cutting Edge | m.20230712.linkandui-ce
!【修正】修正部分時候搜尋失敗的問題 (fe837cc)
=> 部分歌曲名稱或作者名稱過長，導致搜尋結果模組出問題
=> 此版本已修正此問題
!【修正】修正混和連結無法記住設定的問題** (fe837cc)

## From Cutting Edge | m.20230712.1.linkandui-ce
!【改變】重新設計無人暫停的介面 (226a2d8)
=> 有任何更改的設計建議也可以到 Issue 跟我們說呦
!【修復】修正無法透過按鈕退出語音頻道的問題 (226a2d8)
!【修復】修正無法透過按鈕調用待播清單列表的問題 (226a2d8)
!【修復】修正無人暫停後，控制按鈕的部分行為 (226a2d8)
=> 無人在頻道，機器人暫停後，現在會停用「播放/暫停」、「跳過」及「自動建議控制」按鍵
=> 並在有人重新進入頻道後，跳過會正常依是否有可供跳過的歌曲來正常重新啟用/保持停用

## From Cutting Edge | m.20230716.linkandui-ce
!【改變】重新設計 /help 求助介面 (64d2be3)
=> 這玩意是很久之前做的，已經太久沒更新了
=> 順便寫成比較好閱讀的樣子，也附上了相關排錯指引
=> 同時也修改成了只有執行者能看到的形式
!【改變】退出語音頻道的訊息整合到播放介面中 (via DynEmbed) (64d2be3)
=> 這個概念一樣是來自於 DynEmbed，盡量將所有訊息整合在單一介面來減少刷頻的問題
!【改變】完成播放的訊息整合到播放介面中 (via DynEmbed) (64d2be3)
=> 概念同上，在退出語音頻道的訊息傳出後 3 秒即會變成此訊息
!【優化】優化部分程式碼 (推薦系統)** (64d2be3)
=> Done DRY programming on suggestion system
=> _get_suggest_track(...) / _process_resuggestion(...) / _search_for_suggestion (...) @ utils\playlist.py
=> Reference: https://github.com/TK-Entertainment/tkablent_music/commit/64d2be3b9e43089a5db49e50591a91e0ccc17697
```  
*檢視完整更新日誌，請點 [完整更新日誌](https://github.com/TK-Entertainment/tkablent/blob/main/CHANGELOG.md)*
## 如何對專案貢獻
**若遇到了些什麼問題**  
可以先到 [支援伺服器](https://discord.gg/9qrpGh4e7V) 提問或 [提交 Issue](https://github.com/TK-Entertainment/tkablent_music/issues)  
  
**若有修改的建議**  
可以運用 Fork 來建立分支或點擊此 Repo 右上角 Code 中的 Download ZIP 來下載原始碼  
修改完畢後也歡迎開 [Pull Request](https://github.com/TK-Entertainment/tkablent_music/pulls)，來與我們交流  

## 授權
**TKablent 開發計畫**  
本專案依 **MIT License** 授權  
授權詳細內容請參 **LICENSE** 檔案
## 貢獻者
### TK Entertainment
#### Kevinowo
- 使用者互動介面 (UI) 設計
- 新版核心設計 (based on Lavalink)

#### GrandTiger
- 機器人最初架構設計
- 核心播放架構設計
- 部分演算法改善工作

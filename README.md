<img src="https://i.imgur.com/wApgX8J.png" height=64 width=64></img>
### A Project of TK Entertainment
# TKablent
[![TKablent 支援伺服器](https://discordapp.com/api/guilds/1010564921005707335/widget.png?style=shield)](https://discord.gg/9qrpGh4e7V)
[![最新更新](https://img.shields.io/github/release/tk-entertainment/tkablent_music.svg)](https://github.com/tk-entertainment/tkablent_music/releases/latest)
[![CodeFactor](https://www.codefactor.io/repository/github/tk-entertainment/tkablent_music/badge)](https://www.codefactor.io/repository/github/tk-entertainment/tkablent_music)  
用 Python 製作的 Discord 音樂機器人  

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
穩定版 (Stable, s) | *正在提供更新，更新周期較慢*  
*目前更新到 m.20240318.1.e1-s*  

開發版 (Cutting Edge, ce) | *仍舊提供更新，供嘗鮮用戶使用*  
*目前測試項目: 搜尋系統及使用者介面優化 (linkandui)*  
*目前更新到 m.20231209.linkandui-ce*  

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
[m.20230716.7.e1-s...m.20240318.1.e1-s](https://github.com/TK-Entertainment/tkablent/compare/m.20230716.7.e1-s...m.20240318.1.e1-s)

```diff
=========================================
Codename TKablent | Version Stable
Copyright 2022-present @ TK Entertainment
Shared under MIT License
=========================================
# Version m.20240318.1.e1-s (緊急修復更新)
!【修復】修復上版更新後導致的無法點播多首搜尋結果的問題

# Version m.20240318.1-s
!【修復】修復嘗試點播播放清單時，機器人沒有反應的問題
=> ErrorFeedback-2024032101
=> 感謝 @Jimmy0423 回報問題
=> 此版本應已修復此問題

# Version m.20240318-s
+【新增】機器人播放 Spotify 歌曲時會顯示相關警告
=> 以前就已經確認 Spotify 音源準確性的問題
=> 從此版本開始會顯示警告
!【更新】機器人播放組件 API 更新到 Wavelink 3.0
=> 這是一個很大的 API 更新，很多語法都改變了
=> 還需要細項調整，此版本可能存在許多潛在問題
!【優化】棄用許多外置 API 套件
=> 因 Lavalink 4.0 帶來了新的插件功能，故此版本開始棄用了許多的外置 API
=> 可能可以為機器人帶來部分效能提升
!【優化】點播 Spotify 歌曲時，機器人將不再顯示等待畫面
=> 拜 Lavalink 4.0 所賜，現在機器人可以很有效率的抓到歌曲
=> 將不再需要等待
!【優化】播放介面簡化，減少字數
=> 為保持介面整潔，此版本簡化了播放介面的按鈕部分，減少了字數
!【改變】/restart 指令改變為 /replay
=> 從此版本開始，/restart 指令將重新命名為 /replay
!【修復】直接使用連結點歌會另外跳出訊息的問題
=> 此版本修復了這個問題
!【修復】其他沒有特別寫出來的修正內容
=> 修了蠻多有的沒的，已經忘記有哪些了 (*°∀°)
!【改變】節慶提示字將自行成行
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

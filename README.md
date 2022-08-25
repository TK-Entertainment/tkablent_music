# 內部代號 TKablent
用 Python 製作的 Discord 音樂機器人

## 開發狀態
20220410 Confidential -> Alpha | [Build 20220410-2](https://github.com/TK-Entertainment/tkablent/commit/9117b15dde26c1f8e9b4c7337f0493a61e09d4d8)

20220813 Alpha -> Cutting Edge | 20220813-ce

## 目前版本
正式版(Stable): *N/A*  
測試版(Cutting Edge): *20220825.2-ce*  
源碼(Source Code): *01d6dfd (20220825)*
  
**最新更新日誌**  
如需觀看更詳細的更新日誌，請點下方連結  
[6511239...01d6dfd](https://github.com/TK-Entertainment/tkablent/compare/6511239...01d6dfd)

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
```  
*檢視完整更新日誌，請點 [完整更新日誌](https://github.com/TK-Entertainment/tkablent/blob/main/CHANGELOG.md)*
## 授權
**TKablent 開發計畫**  
遵循 **CC-BY-NC-SA-4.0 International License (姓名標示-非商業性-相同方式分享 4.0 國際)**  
您可以自由使用，但不可用於營利
## 作者
By TK Entertainment / Kevinowo GrandTiger

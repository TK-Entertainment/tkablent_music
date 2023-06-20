# 內部代號 TKablent
用 Python 製作的 Discord 音樂機器人

## 開發狀態
穩定版 (Stable, s) | *正在提供更新，更新周期較慢*  
*目前更新到 m.20230611.1-s*  

開發版 (Cutting Edge, ce) | *仍舊提供更新，供嘗鮮用戶使用*  
*目前更新到 m.20230611.wl2.0-ce*  

前期開發版 (Alpha) | *已於 20220813 停止更新，由 Cutting Edge 代替*  
*最後更新到 Alpha 20220424 Update*  

內部開發版 (Confidential) | *已於 20220410 停止更新，由 Alpha 代替*  
*最後更新到 # Build 20220410-2*

## 目前版本
正式版(Stable): *m.20230611-s*  
測試版(Cutting Edge): *m.20230611.wl2.0-ce*  
源碼(Source Code): *8a4d564 (20230612)*
  
**最新更新日誌**  
如需觀看更詳細的更新日誌，請點下方連結  
[e0d8994...8a4d564](https://github.com/TK-Entertainment/tkablent/compare/e0d8994...8a4d564)

```diff
=========================================
Codename TKablent | Version Stable
Copyright 2022-present @ TK Entertainment
Shared under CC-NC-SS-4.0 license
=========================================
# Version m.20230611.1-s (8a4d564)
+【更改】重複播放標示的顯示方式 (圖三、四、五)
#=> 因為 DynEmbed 有點弄不出來，只好先下放一些部分功能到穩定版啦
#=> 先下放重複播放的標示方式，如圖
!【修正】重複播放按鈕的邏輯 (圖五)
#=> 這其實是一個遠古的問題，最近才發現 /w\
#=> 在輸入 /loop [次數] 後，介面不再多出同樣的重複圖案，而是顯示次數 (如果有指定次數的話)

# Version m.20230611-s (/)
## From Beta m.20230609.wl2.0-ce
+【更新】機器人播放伺服器連接套件更新
#=> Wavelink version bumped to v2.4.0
+【優化】程式碼部分優化，增進機器人效能

## From Beta m.20230611.wl2.0-ce
!【更改】播放及新增歌曲介面下，點歌者姓名顯示方式更改
#=> 因應 Discord 近期對於使用者名稱系統的更動，部分使用者已經更改成無後輟碼的新使用者名稱格式，故機器人修正部分顯示問題 (本來會顯示#0) (我知道有些人很不爽這個變更，但沒辦法ww)
#仍持有舊使用者名稱者會以左圖形式顯示，新的則會以右圖形式顯示
#可參 Discord 官方部落格說明: https://discord.com/blog/usernames
```  
*檢視完整更新日誌，請點 [完整更新日誌](https://github.com/TK-Entertainment/tkablent/blob/main/CHANGELOG.md)*
## 授權
**TKablent 開發計畫**  
遵循 **MIT License**  
授權詳細內容請參 **LICENSE** 檔案
## 作者
By TK Entertainment / Kevinowo GrandTiger

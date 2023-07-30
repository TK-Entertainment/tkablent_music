# TKablent | Structure Revolution (structure_rev)
[![CodeFactor](https://www.codefactor.io/repository/github/tk-entertainment/tkablent_music/badge/structure_rev)](https://www.codefactor.io/repository/github/tk-entertainment/tkablent_music/overview/structure_rev)
此為 TKablent 機器人組件架構改造計畫之分支，極為不穩定  
若要查看目前的穩定版或測試版的相關資訊，可以到 [master](https://github.com/TK-Entertainment/tkablent_music) 分支來了解更多  

## 專案目的
主要要徹底的讓功能及程式碼模組化，降低維護的成本及新增功能的難度  
並加上了本地化的支援，讓機器人可以不只有中文的版本  
修改錯誤字串時能更簡單的完成

## 架構介紹
**Helper**: 放置相關操作 Storage 區的模組 (如寫入及讀取等等)  
**Misc**: 放置雜物 (一些定義及全機器人共用的數值等等)  
**Player**: 核心程式區 (指令區域)  
**Storage**: 機器人的資料儲存模組  
**Tasks**: 管理背景工作的模組  
  
**UI**: 放置所有使用者介面相關的模組  
--| *以下為各模組子資料夾中的檔案*  
--| ***Button***: 放置按鈕相關模組  
--| ***...Embed***: Embed 生成模組  
--| ***...View***: View 生成模組 (按鈕/選單框架)  
--| ***...Enums***: 子模組專用數值區

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
## 作者
By TK Entertainment / Kevinowo GrandTiger

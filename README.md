# Resource Pack Updater (暫稱)

一個用於同步與更新 Minecraft 資源包的自動化工具，讓你在製作資源包可以同時維護多個版本，免去手動複製與整理檔案的麻煩。<br>
註:此工具並不會做格式轉換，這意味著若新版本修改了某檔案格式(e.g : json)，你需要自己手動修改。

## Features
- 以上個版本做比較更新資源包的內容，根據 `operations.txt` 設定進行更新。
- 協助刪除資源包中冗餘的檔案
- 支援處理新增、刪除、修改與移動/重命名的檔案
- 只複製日期較新的檔案 (更快)

## How to use

每個版本皆為一份完整的 Resource Pack，將根據 `operations.txt` 設定進行更新與同步。

---

```
請將所有資源包放置於 `resource/` 資料夾中，如下(以作者的舉例)：
resource/
├── battlecats_core ← 核心資源包（版本1.17.1）
├── battlecats_1.8.9
├── battlecats_1.10.2
├── ...
├── battlecats_1.21.5
```

---

#### ⚙️ 更新順序規則

- 正向升級（預設流程）：  
  `core`→ `1.17.1` → `1.18.2` → `1.19.2` → ... → `1.21.5` → `latest`

- 反向回溯（歷史版本補完）：  
  `core` → `1.16.5` → `1.16.1` → ... → `1.8.9`

---

#### 📄 結構

把`operations.txt`以及被新增、修改的檔案/目錄<br>
放置在`resource/{核心資源包}/vers/{版本號}`的資料夾中，結構如下(以作者的舉例):
```
resource/battlecats_core/vers/
├── 1.8.9
│   ├── operations.txt
│   └── ...
├── 1.10.2
│   ├── operations.txt
│   └── ...
├── 1.12.2
│   ├── operations.txt
│   └── ...
├── ...
├── 1.21.5
│   ├── operations.txt
│   └── ...
```
當前有根據作者需求設定好的各個版本的`operations.txt`，<br>
你可以選擇直接引用它並依照自己需求修改<br>
或者撰寫一個新的。<br>
#### operations.txt 格式
<br>

```txt
# 指定相對於資源包根目錄的資源路徑(assets 開頭)
# 不要使用絕對路徑
# #字號為註解
# 語法格式如下：
#   R: 舊路徑,新路徑（Rename）
#   M: 修改路徑（Modify）
#   D: 刪除路徑（Delete）
#   A: 新增路徑（Add）

# 範例：
R:assets/minecraft/textures/item,assets/minecraft/item
M:assets/minecraft/lang
D:assets/minecraft/sounds
A:assets/minecraft/models
# 錯誤範例:
# A:minecraft/models 沒有以assets開頭
# M:C:/Users/user/.../resourcepack/assets/minecraft/lang 使用絕對路徑
```

#### 舉例
##### 修改 
1.20.2修改了`assets/minecraft/textures/gui` (與1.20.1比較)<br>
將1.20.2版的`gui`放置在 `resource/battlecat/vers/1.20.2`中<br>
並且在`resource/battlecats/vers/1.20.2/operations.txt`加入:
```
M:assets/minecraft/textures/gui
```
##### 新增
1.19.2新增了`assets/minecraft/textures/item/echo_shard.png` (與1.18.2比較)<br>
將`echo_shard.png`放置在 `resource/battlecats/vers/1.19.2`中<br>
並且在`resource/battlecats/vers/1.19.2/operations.txt`加入:
```
A:assets/minecraft/textures/item/echo_shard.png
```
##### 刪除
1.16.5刪除了`assets/minecraft/shaders/core` (與1.17.1比較)<br>
在`resource/battlecats/vers/1.16.5/operations.txt`加入:
```
D:assets/minecraft/shaders/core
```
##### 移動/重命名
1.14.4是`assets/minecraft/textures/item` ,<br>
在1.12.2被重命名為`assets/minecraft/textures/items`,<br>
移除了`crossbow_arrow.png`,<br>
修改了`acacia_boat.png`,<br>
`book.png`被重命名為`book_normal.png`並且圖片有修改,<br>
在`resource/battlecats/vers/1.12.2/operations.txt`加入:<br>
(不同命名且不同名稱則視為不同檔案)
```
R:assets/minecraft/textures/item, assets/minecraft/textures/items
D:assets/minecraft/textures/items/crossbow_arrow.png
M:assets/minecraft/textures/items/acacia_boat.png
A:assets/minecraft/textures/items/book_normal.png
D:assets/minecraft/textures/item/book.png
```
若`book_normal.png`沒有修改過:
```
R:assets/minecraft/textures/item, assets/minecraft/textures/items
D:assets/minecraft/textures/items/crossbow_arrow.png
M:assets/minecraft/textures/items/acacia_boat.png
R:assets/minecraft/textures/item/book.png, assets/minecraft/textures/items/book_normal.png
```

## Running
### 1. 安裝 Python (最低版本需求為 3.9)
https://www.python.org/

### 2. 執行腳本
```sh
python update_resourcepacks.py
```

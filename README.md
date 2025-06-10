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
# 指定相對於資源包根目錄的資源路徑
# 不可使用絕對路徑
# 除了 D: 操作外，所有路徑必須以 assets/ 開頭。
# #字號為註解
# 語法格式如下：
#   R: <舊路徑>,<新路徑>         （Rename：重新命名或移動）
#   M: <路徑>,[子目錄]           （Modify：修改指定路徑內容）
#   A: <路徑>,[子目錄]           （Add：新增檔案或資料夾）
#   D: <路徑 (可使用 shell patterns)>  （Delete：刪除檔案或資料夾）

# 範例：
R:assets/minecraft/textures/item,assets/minecraft/item
M:assets/minecraft/lang
A:assets/minecraft/models
D:assets/minecraft/sounds
# 刪除所有以 unused 結尾的檔案/目錄
D:*unused
# 只刪除在 assets 底下以 unused 結尾的檔案/目錄
D:assets/*unused

# 錯誤範例:
# A:minecraft/models  ← 錯誤，沒有以 assets 開頭
# M:C:/Users/user/.../resourcepack/assets/minecraft/lang  ← 錯誤，為絕對路徑
```

#### 使用實例
##### 📁 修改 
1.20.2 相較 1.20.1 修改了 `assets/minecraft/textures/gui`<br>
將1.20.2的`gui`放入 `resource/battlecat/vers/1.20.2`<br>
並在`resource/battlecats/vers/1.20.2/operations.txt`加入:
```
M:assets/minecraft/textures/gui
```
##### ➕ 新增
1.19.2 相較 1.18.2 新增了`assets/minecraft/textures/item/echo_shard.png`<br>
將`echo_shard.png`放入 `resource/battlecats/vers/1.19.2`<br>
並在`resource/battlecats/vers/1.19.2/operations.txt`加入:
```
A:assets/minecraft/textures/item/echo_shard.png
```
##### 🧩 檔案名稱衝突
1.21.3 出現兩個`slot_highlight_back.png`但在不同子目錄，路徑如下：<br>
- `.../container/bundle/slot_highlight_back.png`<br>
- `.../container/slot_highlight_back.png`<br>
建議將第一個放入 `bundle` 子資料夾以避免衝突：<br>
```
A:assets/minecraft/textures/gui/sprites/container/bundle/slot_highlight_back.png, bundle
A:assets/minecraft/textures/gui/sprites/container/slot_highlight_back.png
```
##### ❌ 刪除
1.16.5 相較 1.17.1 刪除了`assets/minecraft/shaders/core`<br>
在`resource/battlecats/vers/1.16.5/operations.txt`加入:
```
D:assets/minecraft/shaders/core
```
你也可以將暫時用不到的檔案放入 `unused` 命名的資料夾中，然後加入：<br>
```
D:*unused
```
##### 🔁 移動/重命名
1.12.2 相較 1.14.4, `assets/minecraft/textures/item`<br>
被重命名為`assets/minecraft/textures/items`, 並且:<br>
- 移除了`crossbow_arrow.png`,<br>
- 修改了`acacia_boat.png`,<br>
- `book.png`被重命名為`book_normal.png` 並假設內容有修改:<br>
(不同名稱且不同內容則視為不同檔案)
```
R:assets/minecraft/textures/item, assets/minecraft/textures/items
D:assets/minecraft/textures/items/crossbow_arrow.png
M:assets/minecraft/textures/items/acacia_boat.png
A:assets/minecraft/textures/items/book_normal.png
D:assets/minecraft/textures/item/book.png
```
若`book.png`僅重新命名為`book_normal.png`，內容沒有修改:
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
python CLI.py
```
or
```sh
python GUI.py
```

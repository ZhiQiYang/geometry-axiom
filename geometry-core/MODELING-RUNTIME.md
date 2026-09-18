# GEO-130 確定性 3D 參考執行器

本模組把 GEO-129 公理轉成可執行的模型資料。既有場景由真正的 C parser／World 驗證；新增擠出、殼、複合空間、布林、拓撲與輸出使用 Python 標準函式庫的整數及精確有理數運算。

支援 `orthogonal-model/1` 五項子能力。座標使用整數 mm、右手系、+Z 向上；範圍仍是正交平面及有界實體，不包含曲面或任意斜面。未在舊 `.scene` DSL 中偷加 extension 指令，也沒有改動已發布的物件畫布。

## 直接執行

需要 Python 3.10+ 及 GCC／Clang 類 C 編譯器；驗證環境為 Linux。首次呼叫可在暫存目錄自動編譯 C adapter，也可指定 `GEOMETRY_MODEL_BASE` 為已編譯的程式路徑。Windows 原生編譯與手機介面未驗證。

從 repo 根目錄：

```sh
python3 geometry-core/modeling_cli.py capabilities
python3 geometry-core/modeling_cli.py example list
python3 geometry-core/modeling_cli.py example wall_through_hole -o wall.model.json --obj wall.obj
python3 geometry-core/modeling_cli.py example l_room_eight_faces -o room.model.json --obj room.obj
python3 geometry-core/modeling_cli.py verify wall.model.json -o rebuilt.model.json
```

一般輸入檔包含 `definitions`、`request`，可選 `presentation`，欄位依 `MODELING-CONTRACT.md`：

```sh
python3 geometry-core/modeling_cli.py build input.json -o model.json --obj model.obj
```

`model.json` 保留來源、引用、版本、狀態與衍生模型；OBJ 只有幾何，座標單位為 mm，不能單靠 OBJ 還原來源定義。兩個可直接檢查的輸出位於 `examples/wall-with-opening.*` 與 `examples/l-room.*`。

CLI exit code：成功含明示 partial 為 0；INVALID 為 2、INCOMPLETE 為 3、UNSUPPORTED 為 4、檔案／執行問題為 5。求值失敗不覆寫既有輸出；檔案以暫存檔加原子替換寫入。

## 其他專案呼叫

```python
import sys
sys.path.insert(0, "/path/to/geometry-axiom/geometry-core")
from modeling import build_package, verify_package, ModelWorld, ModelError

package = build_package(definitions, request)
rebuilt = verify_package(package)

world = ModelWorld(definitions, request)
preview = world.preview(changed_definitions)
world.confirm(preview["token"])
# world.cancel() 可丟棄預覽；失敗、取消、過期 token 都不修改已提交來源。
```

ModelWorld 每次變更先完整求值候選，再明示確認；確認前再驗證。來源定義及 package 的存取都回傳副本，不允許外部繞過守門直接改內部狀態。這個物件供單一呼叫端序列操作；未宣稱同一 ModelWorld 具備多執行緒交易安全。

來源定義完整保留，包括未被本次請求選取但已驗證的物件。只有所選根及其實際幾何依賴加入 R29 切分網格；無關物件不改輸出幾何。C adapter 提供舊角材的承載面、前置擋面及引用鏈，以及柱樑的空間成員依賴。畫布位置與註解不進正典來源。

匯入允許其他生成器的合法 `name/version`，仍嚴格檢查支援的 schema、profile、公理版本、能力、座標系及摘要，並重算逐位比對 definitions／request／derived。診斷須結構合法且涵蓋省略根；文字可不同。`verify_package` 回傳本執行器重建的新包，因此使用自己的 generator 與診斷。尚未以第二套完整引擎驗證所有跨實作情況。

## HTTP

`npm run build` 會建置原核心、原 bridge 及 model_base；`npm run dev` 啟動服務。

| 介面 | 用法 |
|---|---|
| GET `/model/capabilities` | 查詢 profile、子能力及 cell 上限 |
| POST `/model` | 傳入 `{definitions,request,presentation?}`，回傳交換包或狀態／診斷 |
| POST `/model/verify` | 傳入交換包，獨立於舊編輯器 World 重建及驗證 |

沿用本機來源檢查。HTTP 不接受使用者指定可執行檔路徑或編譯命令；輸入上限 16 MiB，每次請求獨立，失敗不改舊畫布 World。HTTP 成功提供 API 不代表手機建模操作介面已完成。

## 明確容量

| 項目 | 上限／行為 |
|---|---|
| 舊場景文字 | 1 MiB，另受既有 C 型別及單行容量限制 |
| 新擴充數量 | 512 |
| 擴充依賴深度 | 64 |
| 每個 KEEP 展開成員 | 10,000 |
| 每個布林的來源面引用 | 12,000，合併前檢查 |
| 精確切分 cell | 預設 200,000；Python／CLI 可明示 `max_cells` |

容量不足一律 UNSUPPORTED，不取整、不刪面、不選最大塊。EMPTY 是合法零幾何結果；開放殼可輸出面，但未封閉不能輸出確定體積。

## 模組

- `model_base.c`／`modeling/base.py`：既有 C 語意驗證與快照。
- `modeling/geometry.py`：幾何、殼拓撲、精確切分及標準網格。
- `modeling/engine.py`：定義圖、型別、依賴、能力與建模求值。
- `modeling/__init__.py`／`common.py`：交換包、摘要、匯入及原子候選交易。
- `modeling_cli.py`：命令列與 OBJ 適配器。

舊 C World 新增型別、畫布建立／編輯介面、GLB 與 SketchUp 專用適配器是後續接入項目。

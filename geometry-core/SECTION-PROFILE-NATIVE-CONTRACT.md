# Q38：第一個原生核心切片

本文件只記錄 D35–D40／I43–I51／R36–R40 已採納規格的有界實作接口，不新增公理。
此切片提供 World 定義、驗證、原生 scene 保存、原子交易與讀取，**不是完整 1A、完整 I49 影響預覽，或完整 `section-profile/1` 產品交付**。

尚未交付：建模執行器的 section-profile 根、D24/R39 renderer、3D 預覽／UI、完整 `.gcanvas` 保存、簡易定位 1B、完整來源檢查圖。
診斷採 first-error：整筆候選不合法即拒絕；尚未逐項彙整全部違規，也尚未計算精確超出形狀的所有區域。
回應明示 `diagnosticsComplete:false`，錯誤提供第一個違規構件及原矩形或交集；before/after 定義和可求值快取可供核對。
輪廓擴大時，按原有接觸線段提示 `PROFILE_CONTACT_LOST`；仍貼其他邊不會掩蓋原接觸的消失（AC18）。

## World 與容量

`SectionProfileState` 是 World 的獨立 POD；沿用既有候選副本、整筆 history、definition equality 與 dump hash。
profile、member、run 各自使用完整 uint32 id 域（含 0），名稱不是身分，可以重複。沒有新增 canvas-pos 種類。

| 項目 | 限制 |
| --- | --- |
| profiles | 16 |
| members（所有斷面合計） | 128 |
| runs | 32 |
| 每斷面頂點 | 4–32，最後一點回接第一點，不重複末頂點 |
| 每個 canonical JSON record | 最多 2047 UTF-8 bytes |
| 一筆交易 | 1–256 operations、1 MiB，沿用既有交易限制 |

Linux C11 實測 `sizeof(World)=2,454,832` bytes，新增狀態 `425,752` bytes；每份 World 增加約 416 KiB。
固定容量為這個核心子切片的工程選擇，超限拒絕，不截斷。
最大容量 fixture 同時保存 16 profiles／128 members／32 runs，fresh load 逐字等於完整 dump；這不是一般使用效能或手機記憶體驗收。

面材固定具名規格 `calcium-silicate-6`（`section-profile-read.panelSpecs`）：厚度 6、寬度嚴格小於 915、板長 1830。
板長不限制 run length，也不產生分段、接縫或料單。

## Native bridge 交易

`section-profile-read` 回傳 revision、定義、求值矩形、run 的局部／世界範圍，以及能力與限制。
`section-profile-preview <file>` 讀取完整 UTF-8 JSON：

```json
{
  "schema": "section-profile-transaction/1",
  "expectedRevision": 0,
  "operations": [
    {"op":"put-profile","value":{"id":1,"name":"L 斷面","outline":[[0,0],[400,0],[400,60],[60,60],[60,250],[0,250]]}},
    {"op":"put-member","value":{"id":1,"profileId":1,"kind":"timber","A":{"kind":"literal","value":27},"B":{"kind":"literal","value":33},"orientation":"A-u","u0":0,"v0":0}},
    {"op":"put-member","value":{"id":2,"profileId":1,"kind":"panel","panelSpec":"calcium-silicate-6","width":100,"orientation":"thickness-v","u0":27,"v0":0}},
    {"op":"put-run","value":{"id":1,"profileId":1,"length":{"kind":"literal","value":2400},"placement":null}}
  ]
}
```

revision 必須取自當次 native read，不能假定為 0。preview 不改 World／revision／undo；合法候選才可 `section-profile-confirm <token>`，一次確認只記一筆 history。
`section-profile-cancel <token>` 取消候選。來源修改、undo、redo 或另一筆候選會使舊 token 過期；engineering／assembly／普通 confirm 不得借用 section-profile token。
`line undo`／`line redo` 沿用完整 World 交易。解析拒絕、非法候選、取消及過期確認不清掉 redo。

`put-*` 是明示的同型別同 id 重宣告。刪除使用 `delete-profile`／`delete-member`／`delete-run` 和 `id`。
所有操作先修改候選，再重驗全 World；可同筆刪除 profile 與依賴者，不能留下孤兒，也不自動刪除依賴者。

位置只收直接整数 `u0,v0`；timber 的方位是 `A-u`／`A-v`，panel 是 `thickness-v`／`thickness-u`。
JSON 原生解析器拒絕浮點數；分數字串、布林、越界也不能當座標。凹形包含檢查重用完整矩形包含測試，不只检查四個角點；貼邊或貼點合法，正面積交集拒絕。

尺寸來源沿用既有具型別物件：

| 來源 | JSON |
| --- | --- |
| 直接整數 | `{"kind":"literal","value":27}` |
| D6b | `{"kind":"spec","name":"A"}` |
| D31 | `{"kind":"parameter","parameterId":0,"fieldId":0}` |
| D26 timber（只供 member A/B） | `{"kind":"material","id":"pine","version":1,"field":"A"}` |

material 欄位必須與 A/B 身分相符，旋轉不交换來源；run 不收 material/application 來源。
同一 batch 可用既有 engineering operations 修改參數／發布固定材料版本；另提供 `{"op":"put-spec","name":"A","value":27}`、`{"op":"delete-spec","name":"A"}`。
spec／parameter 改動須重新驗證既有斷面依賴；改來源造成出界或碰撞時完整 World 回滾。
既有 engineering-preview 及普通 DSL spec preview 也回傳 section-profile before/after，不私自凍結舊值。
native preview 的頂層 `before`／`after` 重用完整 engineering 候選狀態，包含具名 `specs`、材料／做法／套用、參數來源與既有幾何；原有 `sectionProfiles` 影響與提示仍保留。
同一來源也被既有 guide／角材使用時，預覽列出其新舊座標、姿態與長度，不能只顯示斷面影響；沒有斷面使用者的來源操作同樣須揭露來源變更。

run `placement:null` 合法且只回傳局部範圍，沒有世界位置。
進階定位保存 `{"kind":"advanced","origin":[1000,2000,2700],"N":"+Y","V":"-Z"}`；軸只收 `±X/±Y/±Z`，U 由 V×N 求得，不作另一份可編輯來源。
驗證輪廓拉伸的所有頂點均在 D1 範圍；同斷面可被多個 run 引用。
簡易定位、未識別欄位、孔、任意角度、逐 member 板厚、角色或裁切設定明確拒絕。

## Scene、能力與舊消費端

完整 native dump 先保存既有來源，再寫：

```text
requires section-profile/1
section-profile profile BASE64_CANONICAL_JSON
section-profile member BASE64_CANONICAL_JSON
section-profile run BASE64_CANONICAL_JSON
```

payload 就是各 `put-*` 的 `value`。三種類型依序保存；含零構件 profile、未定位 run 與全部尺寸引用。
records 只允許 atomic native `loadfile`／scene parser，不允許 `line` 逐筆注入。
每次 parse 重新檢查 required marker；移除 marker、未知版本、重複 id、損壞／截短 record 或非法依賴均拒絕，live World 不變。

能力分兩層：

- 有新資料的 scene／native `required_capabilities` 必須列 `section-profile/1`。
- bridge 的既有全功能 `capabilities` **不**宣告 `section-profile/1`；只在 `native_capabilities` 宣告本實作標記 `section-profile-native/1`。
- native read 額外明示 `rendererSupported:false`、`simplePlacementSupported:false`、`diagnosticsComplete:false`。
- 舊 `.gcanvas` reader/writer 對 required marker **及剝除 marker 後的 section-profile records** 都拒絕，不能默默保存缺資料的專案。
- 舊 Python modeling 執行器與直接 C `model-base` 都拒絕；直接 adapter 回 `UNSUPPORTED / CAPABILITY / I32`。
- 舊 source-inspector 尚未索引新型別；含新資料時回 `complete:false`，不偽稱來源圖完整。

`section-profile-native/1` 是工程接口標記，不能解讀成 `.gcanvas`、建模能力、UI 或完整公理驗收通過。
本輪沒有修改公理或閱讀器，也沒有合成另一套 renderer。

## 可重現驗證

專屬 build（每次來源變更後重建；sidecar 由既有 binary registry 產生）：

```sh
ulimit -s 16384
python -c 'from pathlib import Path; from tests import binaries as b; b.OUT_DIR=Path("/tmp/geometry-q38-native"); raise SystemExit(b.main(["build","bridge","core","model-base"]))'
GEOMETRY_TEST_BRIDGE=/tmp/geometry-q38-native/bridge GEOMETRY_MODEL_BASE=/tmp/geometry-q38-native/model-base python tests/test_section_profile_native.py -v
node --test tests/test_section_profile_compat.js
```

永久測試核對固定數字、真核心負例、完整 dump／fresh-process roundtrip、零 id、固定來源、不同 token、取消與過期、undo/redo、容量、舊消費端拒絕。
外部 oracle、aggregate／變異及最終 commit／binary 指紋另外記錄。
早期 dirty tree 結果保留原 head／狀態；可用完整受驗來源雜湊等值綁定後續 commit，但不得把原收據改標成當時已在最終 clean commit 上執行。

### 2026-10-08 本地驗證

產品提交 `569b229` 的永久原生測試 13／13、獨立外部原生 oracle 18／18、
舊 JS／Python／C 消費端拒絕檢查 6／6 均通過。
完整非瀏覽器 aggregate 實跑 **70 suites：2174 pass、0 fail、1 個具名 Windows GDI skip，exit 0**。
以該次完整執行更新 expected：只新增原生 suite 13 項，Node 共用 suite 由 510 增至 513；既有 floor 不降低。
這不是 CDP、實體裝置、Windows 或上述未完成產品層的驗收。

核心來源變更後也實際重新編譯／執行 mutation inventory，未只改收據雜湊：
未變異 baseline 139／139；48 筆為 40 killed、1 crashed、4 equivalent、3 retired，
0 survived／invalid／stale／blocked，exit 0。等價項亦經原 runner 的實跑核對。
工具保留執行當時的 HEAD `5cc1ffa`（加凍結中的本切片修改）；
收據的 source／closure 指紋與 `569b229` 核心來源相符，不能解讀為未修改 main 的測試。
提交中的 `tests/mutants_results.json` 是實跑生成的收據；`mutate.py --check` 是其後的 freshness 核對。

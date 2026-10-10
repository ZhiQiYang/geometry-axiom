# Q38 斷面模型介面

規範來源是已採納的 `公理層.md` D35–D40、I43–I51、R36–R40。本檔固定 `section-profile/1` 的模型交換欄位；不增修公理，也不代表整個 UI／存檔驗收已完成。

## 輸入與能力

使用現有 `build_package`／`/model`／CLI，來源仍是 `{base_scene,extensions}`。斷面資料存在原生 `base_scene` 的 `requires section-profile/1` 與 `section-profile profile|member|run BASE64` 中；完整原生 World 驗證成功後才產生模型。Python 不重算參數、材料來源、矩形包含／重疊或定位框架，不把來源引用改寫成數值。

```json
{"roots":[{"kind":"profile-run","id":1}],"role":"geometry","target":"solid-set","allow_partial":false}
```

根必須是已存在的原生 run。此能力只接受 `geometry/solid-set`；不把 run 隱式當作 composition 輸入、Space enclosure 或 obstacle。可與其他合法根一起請求，但各根的身分與座標範圍保留。未使用的 profiles、members、runs、規格、參數 AST 與固定材料版本仍全部存在於正典 `base_scene`。

套件維持 `geometry-model-package/1`、`orthogonal-model/1`，generator 為 `geometry-axiom-reference` 1.4.0。含斷面來源時 manifest 必宣告 `section-profile/1`；不含者不增加此能力。公理版本是 `3ad8012b6f01f9f46795a28a410ee444c5cce1a0`／LF SHA-256 `29ad0c657e53d364347862fddac23ba26a248a4fd8f83487d86f9e648bd1eaf2`。舊版套件可以照原能力重建，但不能用舊版公理夾帶斷面來源或新能力。

## 構件與包絡

每個構件產生一個完整、封閉、有來源的 mesh object；不能因貼齊或重疊其他 run 而合併身分或刪面。`root={kind:"profile-run",id:run_id}`，材料的 `member_path=[member_id]`（原生 uint32 身分，不是陣列索引），`role="geometry"`。不同 run 的同一 member 以 root 區分。

每個 run 另有一個 `member_path=[]`、`role="reference"` 的包絡。它是實際凹形輪廓沿長度擠出的體積，不是 AABB，也不是面板或材料填滿。零構件 profile 仍輸出這個參考包絡。包絡的 `volume_mm3` 是其幾何體積；**材料統計只加總 `section_profile.material_volume_mm3`**，包絡一律為 `"0"`。

每項在原有 mesh 欄位以外增加：

| `section_profile` 欄位 | 值與語意 |
|---|---|
| `run_id`, `profile_id` | 原生 uint32 身分，允許 0 |
| `member_id` | 材料構件的 uint32；包絡為 null |
| `kind` | `timber`、`panel` 或 `envelope`，供獨立顯示／隱藏 |
| `coordinate_space` | `local` 或 `world`，見下節 |
| `dimensions_mm` | 角材 `[A,B,L]`；板材 `[6,width,L]`；包絡 null |
| `orientation` | 原生 A-u／A-v／thickness-u／thickness-v；包絡 null |
| `bounds_mm` | 此座標範圍下的實際 `[[minx,miny,minz],[maxx,maxy,maxz]]` |
| `material_volume_mm3` | 構件精確體積十進位字串；包絡 `"0"` |

旋轉不交換 A/B 或厚度／寬度的來源身分。板材長度直接沿 L 連續擠出，不按 1830 mm 切段，不形成拼縫。每個材料 mesh 的精確體積須等於三個 `dimensions_mm` 的乘積。

`face_sources` 保持原有固定欄位。`origin={kind:"profile-run",id:run_id}`；材料 `operation_path=["members",String(member_id)]`、role=`boundary`；包絡 `operation_path=["profile",String(profile_id)]`、role=`reference`。feature 使用 `bottom_cap`、`top_cap`、`outer_side`，cap 的 loop/edge index 都為 −1，側面按原始輪廓邊序。`placement_id`、`boundary_id` 為 null：原始幾何是斷面構件，不冒充定位宿主的面。宿主依賴與簡易定位參數仍保留在來源。

## 座標與唯一化

未定位 run 的頂點是 D39 的 `(u,v,w)`，不能解讀為已有世界原點或世界 up。每個未定位 run 是獨立 local 範圍；只在該 run 的材料與包絡之間共享 R29 切分網格。其他 local run 或 world 物件不增加它的切分座標。

已定位 run 使用原生已求值 `O/U/V/N` 生成世界 XYZ；簡易定位與進階定位都用同一個 native frame。世界根按既有 R29 規則共享選定幾何依賴閉包的網格；live placement 宿主的有效面參與，複製的 `space-wall-values` 保留 snapshot 來源、輪廓和孔，沒有偷加對原 Space 的 live 引用。

manifest 仍用標準右手 mm、世界 up=+Z 的座標協定；它不覆蓋 `coordinate_space="local"` 的明示局部範圍。閱讀器必先按此欄位分開呈現，不能把多個 local 原點疊成世界場景。JSON 可存多個範圍。OBJ 單一 local run 會明寫 local `(u,v,w)`，世界輸出明寫 world XYZ；混合 world/local 或多個獨立 local run 明確 `UNSUPPORTED/OBJ_COORDINATE_SPACE`，不輸出誤導的合併世界模型。OBJ 物件前另註明構件／包絡身分及材料體積；語意完整交換仍使用 JSON。

## 拒絕與重建

原生來源無效、缺引用或未知能力不得變成空模型／部分成功。容量不足明確 `UNSUPPORTED`；`allow_partial` 不會略過無效或超容量斷面。`verify_package` 重放完整來源，對正典 definitions、request、derived 與雜湊核對，因此修改身分、範圍、材料體積、尺寸或 mesh，即使重算 geometry hash 也會被拒絕。ModelWorld 的更新沿現有 preview→confirm 邊界；取消或無效候選保全前一包。

永久測試 `tests/test_section_profile_modeling.py` 使用真原生 adapter，另以輸出三角形的有向四面體體積、封閉有向邊、Euler 特徵和手算 bounds 核對，不把重新呼叫同一產生器當作幾何 oracle。它是模型層定向 gate；完整 UI、原生歷史、`.gcanvas` 及跨層驗收另外記錄。

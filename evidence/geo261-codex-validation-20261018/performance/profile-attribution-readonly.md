# gprof 歸屬限制：既有 integration bridge 的局部唯讀證據

本輪只執行 `nm`、`readelf`、指定函式的 `objdump`，讀取既有 gprof 文字；沒有 rebuild、執行 bridge、測試或量測。binary SHA-256 `0e9a58d96e0079cef3c7897911cf2dc52636b41d1430af22a0d9770b3479190c`，與該 resident profile 的 `profile-inputs.json` 相符。

## 可以直接證明

1. `geo_candidate_provider_hash` 是 ELF LOCAL FUNC，起址 `0x279f0`、大小 634 bytes。完整局部反組譯沒有直接自我呼叫、間接呼叫或產品 callback；只呼叫 `mcount`、`strlen`、`malloc`、`memcpy`、`geo_sha256`、`free`。`geo_sha256` 下游只呼叫 `geo_sha_block`，block 只有 `mcount` 外部呼叫。故圖中的 provider→provider `1320` 不能解讀為該 metadata 函式真的遞迴。
2. `app_world_candidate_create` 有九處 `call app_candidate_bind_core`，位址為 `0xb8cec`、`0xb8d0e`、`0xb8d33`、`0xb8d58`、`0xb8d7d`、`0xb8da2`、`0xb8dc3`、`0xb8de4`、`0xb8e05`。每個成功 factory 都走完九筆；失敗路徑會提早返回。
3. `app_candidate_bind_core` 在 `0xb8c4c` 使用 tail jump 進入 `geo_candidate_bind_state.part.0`，而不是 provider。clone 在 `0x27c81` 呼叫自己的 `mcount`，在 `0x27e57` 呼叫 bound-state `geo_sha256`，沒有呼叫 provider。既有 callgraph 卻列 world factory→provider `2250`，同時 factory→bind_core 也是 `2250`；它與 factory `250 × 9` 相符。因此該文字邊不能當作真正 metadata provider 呼叫或成本。
4. 另有帶 `mcount` 的 `geo_candidate_check_state.isra.0`（`0x27ea0`）與 `geo_candidate_check.part.0`（`0x27fc0`）。後者真正在 `0x28029` 呼叫 provider；這些 clone 在 ELF 符號表存在，既有 callgraph 卻未保留同名獨立列。這支持編譯器 clone／tail-call 與 gprof 符號歸屬的失真，而非產品 provider 遞迴。

## 報告必須保留的限制

- 本輪沒有解析 raw gmon arcs，沒有追查 gprof 的符號過濾／位址映射實作；不能斷言是哪個 gprof 內部步驟造成，也不能僅憑數字扣除法重建正確 caller counts。
- `3615 + 1320`、`4935` 都應稱「gprof 顯示的 direct／recursive／合計 calls」，不能稱經產品 trace 證實的 provider 次數；其 caller 比例也不能精確代表 H/K/provider 邊界。
- resident `geo_sha256` 的 14.50 s children 依 `3145 / 6306` 分配約 7.23 s 給顯示為 provider 的 caller。因此 provider 的 7.25 s inclusive 同時受按次數分配與符號錯歸屬影響；不能當小 metadata 的實測耗時。
- 這不否定 `geo_sha_block` 14.50 s／99.66% 的取樣熱點證據；但它不是純函式吞吐量、cycles 或精確 H/K 成本分攤。

原命令與局部原文：`profile-attribution-readonly.txt`，SHA-256 `f8585c1f56d4ce7183d778d95dfc04876edf3d659342d6e6266ef7930ecf69da`。本文件只補充解讀限制，不修改任何正式原始報告。

# PF-4A：既有真宿主的活來源主格

固定基底：`11eddfdb4d7b1f76aedfe001e084a3840790bedc`。依據公理層 D10、D42／D43、I55／I8a、R41／R44，以及 issue #128 的 UI 方向 A。這份文件描述實作候選及驗收契約，不是正式 CI、完整 PF-4 或 L4 通過聲明。

## 為何先交這一片

main 已有 #380 的 C0 from-fill 原生能力，以及 #355 的完成面／鋪排工作區。獨立建立 live 主格不需要 R45 建議 builder，因此先把既有真宿主接到一般面設定入口。這明確調整 #128 歷史排程；沒有改變使用者已選的 UI 位置或任何公理。

PF-4B 的普通 D29 值快照仍待交付。PF-6 仍需無提交 builder、FIXED 外環邊材與主副支候選、明選集合完整重驗、外層前置／後置組合與一次提交。PF-5 仍需空間／障礙／下游的完整一般入口流程。R03 產品前置守門維持。

## 真正的原生入口

既有 `POST /panel-fill/preview` 使用原 `panel-fill-transaction/1`：

```json
{
  "schema": "panel-fill-transaction/1",
  "expectedRevision": 0,
  "operations": [
    {"op": "create-from-fill-grid", "value": {
      "fillId": 1, "hostId": 10, "mainAlong": "u"
    }}
  ]
}
```

`expectedRevision` 必須來自當次 read，範例的 0 不是固定值。`fillId` 為正 uint32，`hostId` 為 uint32（0 是合法原生身分），`mainAlong` 必須是 `u`、`v` 或明示 `null`。不接受 grid id、axes、座標副本或額外別名。表單的未選值不等於 `null`。

正式 before 必須已有該 fill 與同 fill 的衍生宿主；不得在同筆新建宿主而暗設 h。已有正式來源可在同候選修改，再用新來源值建立主格。原生在候選內找未占用 id；預覽／取消不消耗正式 id。

`wood_grid_create_fill()` 屬 W：同宿主已有同 fill／mainAlong 時保留原身分；不同來源、直接軸／system／binding 主格或不同偏好全部拒絕。`fs_create_fill_grid()` 屬 H：嚴格解碼並固定正式 before 的前置。`pf_actions_operation()` 只接入既有 batch。最後仍經全世界重驗、fresh token 檢查與原子 confirm，不在 JS 計算板縫／碰撞。

### 與 #128 §7.7 後續 wrapper 的邊界

這一片擴充已採入 UI-1 協議，沒有宣稱實作 §7.7 的完整 action wrapper。候選帶 candidate-local id；native 相同定義 NO_OP 可取得既有 batch token，確認回 `history_changed:false`，正式 dump／revision／history 不動。UI 同定義表單不發 POST。PF-6 的 tempKey／confirm idMap、無 token action NO_OP 與無提交 append 留在後片；不能把這個獨立 confirm 包進 history group 冒充可組合 builder。

## 完整讀取與保存

`panel-fill-workspace/1.supportedActions` 在原四項之後增加 `create-from-fill-grid`。全域仍 `complete:false`，不宣告 `panel-fill/1` 已完整交付。

`scope.fillGridIds` 精確覆蓋 before／after 聯集；`state.fillGrids`（預覽為 before／after）逐筆提供：

- `definition:{id,hostId,fillId,mainAlong}`；
- `derived:{indexSpace:"lattice",bandIndexSpace:"panel-row",side,staggerAxis,staggerDelta,axes:{u,v}}`；
- 每軸 `baseCoordinate`／`pitch`／`baseIndex` 為精確十進位字串。先在完成面算縫中心，再把 v 映至板背；負側不重新編號、奇數縫寬不重新取 floor，band 是 D43 板列而非 D29 cell。

來源主格、guide 與角材的完整原生前後依賴進入同一影響區。缺能力、缺宣告範圍、缺來源或漏掉本次主格依賴不能確認；不接受無關 grid 偷渡進候選。

scene 仍只保存 `grid G on P from-fill F [main-along ...]`，不存求值陣列。`.gcanvas` 不改版本，也不新增第四種 PF definition-reader record；保存保全檢查將既有 from-fill grid 定義納入，拒絕缺失、改來源／宿主／偏好或展開成直接座標的隔離讀取結果，且不替換現案。

## 驗收分層

| 層 | 判準 |
|---|---|
| 原生 | `test_panel_fill_grid_transaction.py`：預覽／取消零寫入與零配號、一次 revision／history、Undo／Redo、NO_OP、錯來源拒絕、正式宿主前置、stale、signed k／負側／交丁 band、D7 真碰撞拒絕、新程序 source-only 重開。 |
| 原生相容 | 原 `test_panel_fill_grid_source.py` 保留 13 方法、16 場／592 支真宿主見證；原 UI contract 精確加第五能力與空 grid scope，原斷言不移除。 |
| 前端 | 新 `test_panel_fill_grid_ui.js` 與原 UI contract，核表單發送、scope、候選能力及完整依賴；`test_panel_fill_project_store.js` 核正式保存的來源保全。Node 測試不是真瀏覽器收據。 |
| 瀏覽器 | 原 `cdp_test.js` 載入 P1284：一般入口 → 建立預覽 → 取消零寫入 → 確認一筆歷史 → 面內復原／重做 → 修改既有交丁 fill、核 signed guide 跟隨 → 保存 → fresh BrowserContext 正式開檔。fresh BrowserContext 不等於原生程序重啟；後者另由原生 suite 驗。 |
| 完整守門 | full CDP 成功後才可產生新 golden；P128=381 與其他舊段逐段不變，P1284 唯一歸第 2 片且 P359 最後。完整 native census、Mutation evidence、架構三檔仍由官方產生器在正式候選來源產生，不能用定向收據代替。 |

具名撤回與實際退出碼、stdout／stderr、來源 SHA-256 見 issue #128 本次交付原件；撤回綠→紅→恢復綠要求 0／1／0，紅段必須是行為斷言失敗，編譯錯誤、timeout 或未跑不算。

## L4 一般入口路徑

工程規格明選面材固定版本及 X 參數 → 物件面 → 屬性 → 面設定… → 完成面與鋪排… → 選正式 fill／同 fill 宿主（沒有宿主時先明設 h、獨立確認）→ 勾「建立跟隨此鋪排的主格」→ 明選主支偏好 → 預覽 → 取消並比對 dump／revision／history → 重做預覽、確認 → 一步復原／重做 → 修改該 fill 起點、核主格／guide／D7 前後影響 → 取消與確認對照 → 正式另存 `.gcanvas` → 全新瀏覽器儲存開啟，核 from-fill 身分、signed k／band、來源及依賴。

必須另列真正走過的排法、結構側、障礙與螢幕範圍。自動測試以 API 準備夾具的部分不得寫成全程一般入口；L4 必須從一般 App 入口準備所聲稱的來源。未實跑前，需求帳既有 UI-1 L4 只維持 11/13 已記範圍；PF-4A 不升 L4，PF-4B／5／6 與 R03 不升級。

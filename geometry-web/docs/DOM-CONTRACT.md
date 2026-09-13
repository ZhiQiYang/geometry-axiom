# DOM 合約(測試依賴清單)

> 立案 2026-09-13(Phase 0 產出)。本檔列出自動測試依賴的 DOM id / class / 全域名稱;
> 之後每階段改 DOM 都要對照本表,新增或改名需同步更新測試。
> 來源:UI-REDESIGN-PLAN.md 附錄 B §7(cdp_test.js 依賴清單)+ §7 測試合約。

## 必須保留的 DOM id

| id | 用途 | 測試依賴點 |
|---|---|---|
| `#cv` | 三視圖 SVG | `hasAttribute("hidden")` 切換檢查、rect 量測 |
| `#world` | `#cv` 內容群組 | `childElementCount` |
| `#overlay` | `#cv` 疊層 | 繪圖預覽層 |
| `#ocv` | 物件畫布 SVG(主畫布) | `hasAttribute("hidden")` 切換檢查、rect 量測 |
| `#oroot` | `#ocv` 內容群組 | 卡片/連線掛點 |
| `#topbar` | 頂列 | rect 量測(排除測試點落上層) |
| `#status` | 狀態列文字 | 中文文案比對(改文案必同步改測試) |
| `#btnObj` | 三視圖/物件畫布切換 | `.click()`、rect;D1 下語意改「三視圖總覽」,id 與切換行為不變 |
| `#btnNewRect` | ＋面·矩形 | `.click()` |
| `#btnNewPoly` | ＋面·多邊形 | `.click()` |
| `#btnNewSpace` | ＋空間 | `.click()` |

## 必須保留的 class

| class | 用途 | 測試依賴點 |
|---|---|---|
| `.ocard` | 物件卡片(SVG `<g>`) | `querySelectorAll(".ocard")` 計數、`getBoundingClientRect` 取座標;`dataset.kind` / `dataset.id` 須保留 |

## 必須保留的全域(classic script 頂層可見)

| 名稱 | 內容 | 測試依賴點 |
|---|---|---|
| `oc` | 物件畫布狀態物件 | 讀 `oc.on`、`oc.faces`、`oc.spaces`、`oc.focus`、`oc.panX/panY/zoom`、`oc.drawTool`、`oc.rect/card/pan` 等 |
| `api` | `api(cmd)` → bridge | 測試直接送 `api("line …")`、`api("objects")` |
| `layout` | 三視圖版面 | `screenToView` 等路徑間接依賴 |
| `leaveFocus` | 退出工作區焦點 | 測試呼叫 `leaveFocus()` |

## 測試自注入

| 名稱 | 用途 |
|---|---|
| `window.__pd` | cdp_test 注入的 pointerdown 探針(測試端自掛,非產品碼) |

## `#status` 文案比對點(cdp_test 引用的中文)

- 「面 N:拖頂點/邊編輯」進入面編輯後
- 「✓ 空間 N(空容器)已建立」建空間後
- 「已復原」/「已重做」undo/redo 後
- 其他成功訊息以「✓」開頭;改文案必須同步改 cdp_test.js

## 變更程序

1. 改 DOM id / class / 全域名 → 先改本表 → 同步改 cdp_test.js / canvas_test.js → 跑裁判。
2. 新增測試依賴 → 補進本表對應小節。

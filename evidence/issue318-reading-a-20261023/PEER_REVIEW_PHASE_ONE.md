# #318 第一批來源：靜態對抗審查

受審產品提交：`41cf5594011d9d13f401319ccf676c741263dbcc`。先自行 fetch handoff 到 `f6a174df42d5ff1ce670b6f8277da60c667b8965`；#318 原 review SHA-256 仍為 `0b1ddba6a201e9bdb779ca8733d5fb7d20e96f1067cde62efd3a0dd5c020cb66`，核可第 3 版未變。審查只讀不可變 Git tree，不靠正在改動的 worktree。

`review318-source-41cf5594/receipt.json` 保存原 argv、退出碼、完整 stdout／stderr、環境與 source SHA。metadata audit 原退出 0；沒有 import oracle、執行幾何、測試或編譯。

已核實的身份：

- committed 公理的 LF bytes SHA-256 `27b12f3838422f6c37c9c21d04f241112ddf7e6e8a8827132bd633fcf0ab5345`，與我先前從 main 獨立套核可四處的候選完全相同；沒有新增未核可條文改動。
- positive JSON SHA-256 `b5e4e707a4fc4b2710db237d0252d67104e0a555a50a875e79de2ad43c7d46c0`，與載入器聲稱的 hash 相同。
- step 528 與 step_mirror 1056 的逐筆 `(room, layout)` 身份，分別與受審提交父節點的原 `step_core`／`step_mirror_core` 完全相同；舊原因碼只有 `CORE_LIMIT_BOUNDARY_END_FREE`。這不代表現在幾何判定已轉綠。

Builder 與 C8 分別導出新例外；checker 不信 builder 的 edge／outer 宣告，先核定位邊、全固定段、真端點與 footprint，再要求正長度角材接觸。RC 先量原連續面再扣接觸，沒有拿短 free-gap 代替真 RC 面，沒有把目標料長軸當新限制。新單元檔明列 oracle 只代表全 FIXED、同承載面的模型；FREE／異承載面／returned FEATURE 仍待 native 測試。到本輪靜讀未見確立的額外語意放寬，但整合尚未完成，不能判整體通過。

待修／待驗範圍已告知 owner：

- `make_golden.py` 原 `core_limit_witness` 把 STEP20 當非空核心限制；採閱讀 A 後它應轉 buildable，不能只把非空 assert 放寬。應用仍有真 I22／其他未核可限制的 current witness 維持非空、四元組、料件矩形與 id 非排序 index 的反證；STEP20 另做當前正常正例。FZ120 只是尚待實跑確認的候選，不冒稱它在新 P182 下必定保留原幾何。
- legacy P182 fallback／C7 三種 tamper／core-limit matcher 可以在明標且有 finally 還原的 withdrawn-policy context 保留原牙齒；不能把整份當前 snapshot 包舊 policy，而漏驗新產品預設行為。新政策本身也要撤回即紅、恢復即綠。
- FZ120 原 `CORE_LIMIT_EXTENSION_END_FREE`、`no_ext_end_flag`、40 mm `MAIN_ON_EXTENSION`、45 mm `SHORT_FACE_SEAM_EDGE_UNSUPPORTED`、STEP20 的逐支副支與縫位／既有治具與淨距，都不是這次新數值決策。只有可逐項推導到核可例外的變化才更新期待，不直接按輸出批次重填。
- P182 候選從 phys-only 變 ok 可能改選縫位，須按未改的第一個可行偏好規則逐候選說明；舊 generic matcher 反證不能整段刪除。
- README 原 668 可保為明確歷史事實，再列當前結果；528／1056 在真正 full／quick sweep 必逐筆觀察到且 buildable。只有 CI 才可按明列 sample 過濾，不可用實際跑到的 room IDs 過濾掉漏房。

此提交尚未完成 native／canonical／舊 selftest 與 golden 遷移，來源 owner 也明列未完成。後續普通 merge 的新 source 與原始動態 streams、全掃描、reader 與 returned FEATURE 反證仍須第二輪對抗審查。

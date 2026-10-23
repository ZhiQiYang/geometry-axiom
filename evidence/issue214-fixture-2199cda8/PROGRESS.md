# #214 A4 preparation progress

Source S: `2199cda8896b47c7ad2b6c10479e5e0cbdb67c83`; base E: `3c6633575ec0f9dccf35898380202aad8d0ffddf`.

只修改 HTTP fixture 的 Thread kwargs，明示 `serve_forever(poll_interval=0.05)`。原 19 方法、全部斷言與 teardown 順序保持。單檔獨立靜審 14/0，外部 helper 獨立靜審 20/0；均未執行 subject。

正式 19 方法、component/CPU/wall、原/修正/等價撤回/恢復均 UNRUN；性能 UNMEASURED。原 suite 時限為 1200 秒，早先 900 秒準備文字保留更正原件。撤回輪詢優化預期 correctness 仍 0，不能冒充功能 kill。

薄 source 僅物化一個測試檔，未配置完整 runtime。`/tmp/geometry-tests` 為原共用 build/log cache，須由 root 給排程與 cache 租約，不能與完整 native/required-eight 寫者並行。無新增性能門檻；收益可零或負，更密集喚醒的 CPU 成本尚待量測。

包內保留 25 個 source publication 原命令與全部 streams。原 preparation recorder 將後 7 個 commit 後命令的 task/source 標籤仍記為 base E；實際 HEAD/commit/push/remote 輸出均為 S。原件不改，`SOURCE_AUDIT_BINDING_ADDENDUM.json` 另列每命令真實 base→S 身份；當時沒有任何測試執行。

下一步：root 配置 runtime/cache 租約後，以已獨審 helper 逐原完整 19 方法保留正式與 component 收據；不在靜審準備階段宣稱執行通過。

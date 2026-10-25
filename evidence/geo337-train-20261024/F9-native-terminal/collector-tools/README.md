# F9 native 真終態收件入口

只適配原 r2 collector `a320b22c…`；沒有啟動 native、沒有讀活動 JOB／ROOT／cache。原工具及舊證據完全不變。

固定 F9 `4f8a794f4167c3562eb182045102e86e9e37cca9`。root 先取得 session 41942 真 exec FINAL，將原完整工具回應另存 JSON；再綁定原 OUTER `RESULT.json`、JOB `RECEIPT.json`、workflow `native/receipt.json` 的實際 SHA256。四份都要真終態，不能以畫面進度或非 null 摘要推定完成。bound request 也須放入本工具獨立靜審的真路徑／hash。

真正執行（目前未跑）：

```sh
python3 -B /tmp/geo337-F9-native-terminal-preparation-v2-20261025/launch_collection.py --request /tmp/<root-bound-request>.json --request-sha256 <actual-sha256>
```

root 要保留 source/cache 收件租約。collector 取得 heavy、secondary、build、run_all 四個既存鎖後再讀收件內容；不啟新 consumer 掃描，不聲稱所有 OS 程序均可見。沒有 ROOT、cache 或產品寫入；只有新 package、metadata 與原 c387 收件輸出。鎖已忙會拒絕，不重跑 native。

沿原 scope：完整 OUTER、JOB（只排除原 preserved-global-geometry-tests 整份歷史 cache）、新 cache 的所有非普通已登記 ELF、sidecars、workflow steps/versions、每 suite run_all-logs、原 stdout/stderr/argv/environment/source-before/after、原 registry Git bytes、工具與本次真 exec FINAL。普通 ELF 只有與登記名稱及完整 fingerprint 大小/hash吻合才略去 payload；原 ELF 永久在原處。不明 ELF、壞 sidecar 或 mismatch 都保留完整 payload，不能因 native 紅而掉收原件。

原 35 分鐘 CI gate、230 列、strict registry、Windows-only GDI 唯一允許 skip 皆不改。collector 不解析或放寬原測試裁判；獨立 actual peer 仍須核230列及允許skip。原回傳非零或 metadata 相互矛盾都完整封存，`collectionExit=0` 只代表保存成功；`originalFormalCandidate` 不是最終正式判定。

封包前依**選定原件未壓縮大小＋tar/PAX/gzip metadata 上限＋完整 inventory/JSON metadata＋64 MiB reserve**做 fresh 准入，不靠預估壓縮率。只有計算預算所需的小型 registry/summary 可能先寫；不夠空間時保留該次失敗與所有原件，不封大 archive、不刪 cache/fixture/objects、不改門檻。

原 tar roundtrip 逐 member 比原 bytes；terminal 四檔在前後再核hash。原 internal `capture_output` 未獨立留下的管線、原測試自行清掉的 NativeBuild scratch 不會冒稱已封存。保留歷史 cache 原 BEFORE/PRESERVED manifest，該 payload 不遍歷也不刪除。

目前只做 Python AST parse 與原工具差分；不執行 collector，也不讀目前 native 進度檔。所有正式結果等待真終態與實際收件。

V2 獨審修正：peer 必須精確綁 collector 與 guard 兩個 SHA256；預算另列 default-deflate compressBound 各項向上取整加 gzip 1024B 餘裕，不假設壓縮後會縮小。exec FINAL output 身分若不可解析或不符，只列紅／formal false並仍保存失敗原件。V1原稿保留，未執行過。

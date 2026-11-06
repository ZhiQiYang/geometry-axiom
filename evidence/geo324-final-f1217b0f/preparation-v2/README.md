# #324 三 predicate 補充原件工具 v2（僅準備）

目前公開產品候選 source 為 `f1217b0fa5e933e14906833bf4981dad97061b04`，已普通 merge main及 train `f64d638f15c48d2b9723b7ae9d230fb5dacb82d9`；正式受驗 final SHA 尚待 root 排 source／架構刷新順序。沒有跑此工具、任何 unittest、native build或Chrome。

v1 `8c2be20fa70879d580e6eb77e702b7390982188da2f76ab76d8c46b9818e2054` 原件及先前PREPARATION保留，不能冒成已動態通過。v2路徑：`/tmp/geo324-owner-20261024/preparation/run_face_predicate_proofs_v2.py`，SHA256 `4b5c05f1a2d7a5cf24c1e2b4d21641c560a7fe7a25db1109a6127d315ddd406d`。

依獨立靜審補三點：

1. 載入 c387前先核 helper SHA256=`c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762`；tool-identity／receipt記driver/helper實際hash，不相符時不載入、不啟測。
2. 不再copytree工作目錄。只從同source的四packages＋三fixture test modules精確Git tracked inventory取bytes，逐一核原Gitblob／實際工作bytes，receipt保mode、blob、bytes、SHA256；輸出樹依該精確inventory構建，不帶ignored／untracked import或可執行檔。唯一合成檔為與原control相同的空 `tests/__init__.py`，明列bytes/hash／理由。
3. mutant除了正常unittest `FAIL: <原method>`／`Ran 1 test`／`FAILED (failures=...)`，另核原公開helper的具名失敗訊息：non-list的`null ... TypeError`、non-dict的`nested-list ... AttributeError`、non-string的`feature-list ... TypeError`，不以其它setup assertion冒反證。不改原test/assertion，不增數值閾值。

每個原method各自 baseline→單predicate撤回→逐bytes還原，60秒原subprocess上限。保存原0/1/0、完整stdout/stderr／env／SHA；error/import/syntax／timeout不算正常mutant。此工具不取代完整45-method模組或full aggregate／六browser。原v1及所有準備失敗仍保在舊E，沒有執行結果被改寫。

待root給真final SHA／clean受驗checkout與時槽才執行：

```bash
env -u PYTHONOPTIMIZE -u PYTHONPATH -u PYTHONSTARTUP -u NODE_OPTIONS \
  python3 -B /tmp/geo324-owner-20261024/preparation/run_face_predicate_proofs_v2.py \
  --repo CHECKOUT --expected-head FINAL_SHA --out /tmp/geo324-predicate-FINAL8-v2
```

這段argv含待填佔位，沒有被當成實際執行原件。架構三原裁判／四檔刷新、ledger原`--check`與full native＋expected／six browser／affected importer仍全部UNRUN。唯一current-state會在正文維持，不用AST0或出版0代替產品gate。

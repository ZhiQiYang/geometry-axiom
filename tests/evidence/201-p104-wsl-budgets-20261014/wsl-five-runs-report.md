【Codex】P-104四個容量案例各五次：本機WSL量測原值已出齊

固定量測head `90659e6190b592feeb06fab263a16175538eb64a`（第9班／原#201 `3f1664fb5c43ad49f76ee97853d8d5923197f7c3`）；owner `a09a90cbd13a13cf223ad4cdb0a1be76253e94e6` 僅一行註解與證據差異，案例本體及產品完全相同。原body／assertions／options不動；私有wrapper只把四案觀測上限設60秒，測得完整耗時。60秒是觀測上限，非建議的正式budget。

| 案例 | 五次test body毫秒（依序） | 本五次最大毫秒 | 最大的2–3倍毫秒 |
|---|---|---|---|
| P064 普通130956 | 1250.362254, 1200.500459, 1132.7223, 1297.788018, 1343.738923 | 1343.738923 | 2688–4031 |
| P064 普通131072 | 1263.811232, 1176.928883, 1146.021905, 1166.764208, 1424.0751 | 1424.0751 | 2849–4272 |
| B1 孤兒130955 | 2344.725358, 2188.547979, 2248.847361, 2083.151631, 2111.989356 | 2344.725358 | 4690–7034 |
| B1 孤兒130956 | 2170.516636, 2346.162281, 2249.445895, 2214.611276, 2242.090981 | 2346.162281 | 4693–7038 |

20個單獨Node程序actual exit皆0，整體WSL／實際工具exit0，原native before與真bridge照常執行。每個子集恰好1個目標test通過；TAP的其餘skip若有，來自test-name-pattern未選取的案例，沒有刪案例。24步（3 clone、1 bridge build、20測量）、944份來源與原bridge `9e0167a160e63ffe6277ab52ab271285bce31b35ebf831568fe026353d42e38f`、47個sidecar閉包引用均核符；7次WSL foreign取樣空，沒有人工節流或新增負載。只量本機所見耗時，不保證任意Windows主機負載。

來源封存最初漏列bridge閉包中一份證據目錄內的C檔，獨立檢查因此exit1；已從同一受測commit唯讀補回原blob，SHA-256與當次保存的sidecar逐byte一致。這1份明列為事後補存，不冒稱啟動前封存；首次檢查失敗也保留。

上述2–3倍只是這五次最大值的計算。第9班首紅及原補跑的更慢值仍保留在[原完整收據](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6153108396)，不能用本輪較快值改寫歷史。請owner依P-104比較完整WSL觀測後做成本或具名時限修正；本機未更動#201分支、最終budget或原斷言。正式七項仍需後續列車。

以下為本輪完整20筆measurement JSON：test_duration_ms與包括原before/native setup的process_seconds分開，命令、TAP stdout/stderr全文與所有來源稍後封包公開並獨立GET；此留言不宣稱完整封包已交付。
````json
[
  {
    "label": "case1-repeat1",
    "name": "K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 130956-byte boundary",
    "case_index": 1,
    "repeat": 1,
    "test_duration_ms": 1250.362254,
    "process_seconds": 2.635048,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "bede15983dabd17390513b22b6460c0ab06c36d2d0229bd2bd27bc878db021ee",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case2-repeat1",
    "name": "K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 131072-byte boundary",
    "case_index": 2,
    "repeat": 1,
    "test_duration_ms": 1263.811232,
    "process_seconds": 2.531584,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "4663deef289f4425f3625866a50abe2eaf2f6cb12902f72e9cf79b0d44878fcd",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case3-repeat1",
    "name": "K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130955-byte boundary",
    "case_index": 3,
    "repeat": 1,
    "test_duration_ms": 2344.725358,
    "process_seconds": 3.736241,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "60c02c3f749f8b8c4ae03e067a72591fe8d2a8acdbd87037de7f1b7503659685",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case4-repeat1",
    "name": "K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130956-byte boundary",
    "case_index": 4,
    "repeat": 1,
    "test_duration_ms": 2170.516636,
    "process_seconds": 3.384412,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "9a0ce150d7642b8091a188cb9a452837c5d383347da56b6836d8d7967fccf34f",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case1-repeat2",
    "name": "K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 130956-byte boundary",
    "case_index": 1,
    "repeat": 2,
    "test_duration_ms": 1200.500459,
    "process_seconds": 2.583456,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "4c71cd379e635aa8cb936c6c5aa96f637e4234f25002e2052ac37752df0428a5",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case2-repeat2",
    "name": "K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 131072-byte boundary",
    "case_index": 2,
    "repeat": 2,
    "test_duration_ms": 1176.928883,
    "process_seconds": 2.68197,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "351ce749c9b399049a30ce976660dbd7f2c02f94ec36bd4d2ee789d403df60ef",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case3-repeat2",
    "name": "K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130955-byte boundary",
    "case_index": 3,
    "repeat": 2,
    "test_duration_ms": 2188.547979,
    "process_seconds": 3.485156,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "a1174f17deac4e03ee1939ca454ed26c55a8d9238435a18e6e7e082f23ba275a",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case4-repeat2",
    "name": "K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130956-byte boundary",
    "case_index": 4,
    "repeat": 2,
    "test_duration_ms": 2346.162281,
    "process_seconds": 3.585885,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "ac8c0d47e54bfa3399f7aa0e06bca8076cf27cf627b5e1bd95454e8e5aa77913",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case1-repeat3",
    "name": "K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 130956-byte boundary",
    "case_index": 1,
    "repeat": 3,
    "test_duration_ms": 1132.7223,
    "process_seconds": 2.330115,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "dd2932a2beeb8155bdc95f1d7b709bbf4a37b44df5c0a7f5121357e779ec7b1d",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case2-repeat3",
    "name": "K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 131072-byte boundary",
    "case_index": 2,
    "repeat": 3,
    "test_duration_ms": 1146.021905,
    "process_seconds": 2.38374,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "e5f17693938a7190ed725560d71e9978bdae2d2b102606520f27a476adaea1fb",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case3-repeat3",
    "name": "K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130955-byte boundary",
    "case_index": 3,
    "repeat": 3,
    "test_duration_ms": 2248.847361,
    "process_seconds": 3.685282,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "f0b8032f070f2df80e7015549f8f4b417ee162155ae6394e84f8189a35ac56d3",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case4-repeat3",
    "name": "K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130956-byte boundary",
    "case_index": 4,
    "repeat": 3,
    "test_duration_ms": 2249.445895,
    "process_seconds": 3.535353,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "435d686f80c2b9310e8c02cded7c88b286d4884ac092b11b43daaea09b6d6673",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case1-repeat4",
    "name": "K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 130956-byte boundary",
    "case_index": 1,
    "repeat": 4,
    "test_duration_ms": 1297.788018,
    "process_seconds": 2.530849,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "7c81e467b0c211988273d261d716dd7ac4840fcc2d5600aee360c1b7309216e0",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case2-repeat4",
    "name": "K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 131072-byte boundary",
    "case_index": 2,
    "repeat": 4,
    "test_duration_ms": 1166.764208,
    "process_seconds": 2.384469,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "83bcc9a0ddb647447866181c48f0f862676a766a2fb3df288f8da7493e464097",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case3-repeat4",
    "name": "K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130955-byte boundary",
    "case_index": 3,
    "repeat": 4,
    "test_duration_ms": 2083.151631,
    "process_seconds": 3.338244,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "43647358f0c59f39b382d0cea26a6e51f349981875d72a693f31678f9884efe6",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case4-repeat4",
    "name": "K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130956-byte boundary",
    "case_index": 4,
    "repeat": 4,
    "test_duration_ms": 2214.611276,
    "process_seconds": 3.489311,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "2a2021673a3139b4da78e6486cc837068b8b1ab80efc5e567f01d4573b255e49",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case1-repeat5",
    "name": "K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 130956-byte boundary",
    "case_index": 1,
    "repeat": 5,
    "test_duration_ms": 1343.738923,
    "process_seconds": 2.837355,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "cf515dad603ee592bf79e27892418dc458f148b2970b486085c6b37d5f5541f5",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case2-repeat5",
    "name": "K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 131072-byte boundary",
    "case_index": 2,
    "repeat": 5,
    "test_duration_ms": 1424.0751,
    "process_seconds": 2.786597,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "a505313ce9f3a8c6fffb1cbf870d180fab973b349c8a0b06fac6170ed7d9b5f9",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case3-repeat5",
    "name": "K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130955-byte boundary",
    "case_index": 3,
    "repeat": 5,
    "test_duration_ms": 2111.989356,
    "process_seconds": 3.384755,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "af98be831adbd719964299dfc8ed41a69e1bd0e9021da3b37c847c1d4a12126b",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  },
  {
    "label": "case4-repeat5",
    "name": "K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130956-byte boundary",
    "case_index": 4,
    "repeat": 5,
    "test_duration_ms": 2242.090981,
    "process_seconds": 3.532725,
    "exit": 0,
    "counts": {
      "tests": 1,
      "pass": 1,
      "fail": 0,
      "cancelled": 0,
      "skipped": 0
    },
    "stdout_sha256": "a7e6e8e070408b6052eec499a79fdf4285f5e54e0404ef6924aa8abe769e8b2a",
    "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "case_bodies_unchanged": true,
    "observation_ceiling_ms": 60000,
    "source_sha256": "f08ae49059550915d0ae7bc380473de59a1c9609048a220e3546aa1b4a90fca2",
    "observation_source_sha256": "62e9ad4c4417f4256e0c9acfc43b256d4b211f108cd9b9402565f9fbca0e269c"
  }
]
````


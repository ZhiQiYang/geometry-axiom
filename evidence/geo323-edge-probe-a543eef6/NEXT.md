# #323 runtime 靜態分析交接

owner：backlog_resume；只准外部草稿，不另開 #323 分支、不改root／其他owner來源；無C時槽。root目前跑memo／效能驗收，重I/O/C獨占。

- 受驗L `7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`，來源 `/tmp/train337-323-f64d638f-source`；原件 `/workspace/g337323L`。perf原36樣本N64/main **1.4282954375紅**，小N/base綠；profile已terminal0，sourcecalls64/32 **4.4076184255綠**。
- `ROOT_CAUSE.md`：確切profile／熱路徑／#341已在L、#343尚未在L、#346/#347非該load熱路徑，不能預告#343足以達1.3。
- `EDGE_PROBE_PLAN.md`：L→S343產品差異僅contact_world.c＋Python model_sources.py（後者#339 faces）；native closure只有contact_world.c。完整原175scene／350trace＋guards、A/B/C及既定性能門檻不變。
- 最小一leaf產品draft `edge-probe-draft/EDGE_PROBE_ONLY.patch` SHA `c7bd55eebd0d7d3f602865a652fb7b0fc5a928db6e04367bb6bbb07db5ade8c3`。只重用edge miss空slot；resize丟棄slot、callocfallback原樣。nodehint/hash/publicAPI沒動；8替換完整撤回精確原L。root親審檔 `edge-probe-draft/ROOT_REVIEW.md`，未見靜態問題，仍要第二審與正式。
- 獨立純Python `edge_probe_algorithm_witness.py` 已exit0，`EDGE_PROBE_ALGORITHM_WITNESS.json`：12edges hash21／31／21；37edge有序線性oracle；9/17/33擴容與indexfailure1/9/17恢復；兩negative模型拒絕。這不是C／正式／mutation已殺。對照第9條的oldslot=9、newslot=25，舊槽在新32表仍空。
- 三leaf產品＋測試外稿 `edge-probe-companion-draft/THREE_LEAF.patch` SHA `b512899e05b161067dd9fc68b66ad92d52c119a01d333963345f6cf5ded41aaa`；`MANIFEST.json`釘before/candidate。原14 unittest方法與helpers AST、C原body逐byte保留，新3方法AST總17，registry未改／discovery未跑。
- companion來源新增稿 `PROBE_C_ADDITION.txt`／`PROBE_PY_ADDITION.txt`；組裝器 `assemble_probe_companion.py`只讀文本+AST，已exit0，沒有importsubject或C。
- 新controls設計：漏清resize slot、回傳錯empty slot各以完整有序圖duplicate-edge正常斷言紅；整段patch撤回三版獨立compile且語意皆綠，診斷hash成本21／31／21、正常0／1／0。原30秒case與原NativeBuild保持；原source-index8controls全保留。
- 已請combined_resume對產品draft、完整3leaf、報告做獨立對抗審；產品c7bd已有combined31/0靜審；companion v2尚待最終peer，不得算正式已審完或READY。

下一步：收peer找錯，若改草稿保原版本並重新釘pin；root一般merge前置到同列車後才決定套用與固定公開F。無新branch／C直到root授時槽；帳本與架構只由root最終統一處理。

補強v2：root要求第9條插入後立即讀回source9＋source1；本線補最後四種consumer/kind邊的倒序重讀，防後續重建掩蓋錯槽。獨立純Python exact-C-sequence模型已exit0，兩錯槽分別在第10／40操作拒絕；不是C。產品與Python companion不變，v1完整留存。

## 新授專項子分支與正式執行

root已授權在同列車之上隔離probe因果，先不merge343，後續由root一般合流；這不是另修舊#323分支。

- branch `codex/train337-edge-probe-20261024`；public S `9430bae568feb98805072930c92f9a03a1250d4e`，普通單親 `b621a4fbc3cdea359b3676fb22dc8ef566968b8a`；source publisher實際exit0且remote exact。
- own薄worktree `/workspace/geo323-edge-probe-work-20261024`，沿root common Git，約69leaf；不改root工作樹。產品＋2tests與expected唯一SourceIndex count14→17。
- source原件 `source-publication/RESULT.json`及逐command完整stdout/stderr。publisher獨審26/0＋env窄補5/0，companion124/0；均靜審不代替實跑。
- formal工具 `formal-tools/retain_source_index_streams.py` SHA65dac15dfbb5268c0471996dc10de8377bdafbe8c5d40cf5c1bd21af694e236b；runner a56c1d7c9bbfac48774eed9f316bd6cf8fdd920ba4f30b03265b517e0d913981。specials獨審24/0＋37/0。
- runner已啟動，session43352；輸出 `/workspace/geo323-edge-probe-formal-20261024`，原全17／10個既有與新增語意controls／whole21-31-21，尚待terminal不能宣稱通過。root指定primary `/tmp/g261r3/heavy.lock` NB與fresh80MiB；無效能/帳本/架構。
- wrapper純synthetic初測曾抓到借用後續case基準的parser強度缺口，v1與初失敗保留；v2強制native命令遞增及相鄰baseline/restored，7純parser正反例exit0，不是C驗收。

最新終態：S `a543eef67b81f8d8800f32d5dc4a5641840d2943` 已普通push；Sa543的C17 R2真0，17/0skip、56compile/link0、43native、10語意controls正常0/1/0、whole三版21/31/21與正常0/1/0。specials actual1427/0、source兩次combined390/0。原S9430的第一輪17真1（測試dir/exe撞名，3個linksubfailure）完整保留且不算kill。root已通知primary釋放。當下準備原包與E/D，尚未宣稱證據/正文已push；其他正式perf/175/350/最終帳本架構仍由root處理。

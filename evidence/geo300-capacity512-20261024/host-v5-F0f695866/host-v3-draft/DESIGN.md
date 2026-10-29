# #348 H 修正與真放置增項（外部 v3）

來源 S400a6d0ca50f3aca104fb569c77c8ef753c93355；未套用公開分支、未執行 generator、C、bridge 或反證。`HOST_V2.patch` 是沿既有檔名保存的 **v3** patch；MANIFEST 釘其 SHA `9b4ff0c483dd97e9af2ba2233c5384a294cc02275b370b58a362b1261f7e7c81`。v1/v2 原稿完整保留；v3 真 `git apply --check` 退出 0。

只含三個檔案：原 H suite 修正／新增兩個方法、原 P-189 generator 原 bytes 新 helper、expected 的 H count 5→7 單列。原五個方法名稱仍在；W7、report11、P2panel13、原73其餘方法不改，新增後局部 AST總75，仍非真 discovery 或通過聲明。

兩項舊測試缺陷：objects 排除未放置成員，不能計算全宣告；loadfile 依 I9 拒絕未放置成員，不能用 512-unplaced scene 作成功載入。這些是測試違反產品原契約，未改產品來遷就測試。修後 dump 全宣告逐 ID 順序／唯一性＋objects 空／無 place；滿容量用逐條互動宣告；原 unplaced scene 與其 canonical dump 兩個 loadfile 都保留，改驗正常 I9 拒絕且完整 rollback。canonical互動重放逐條送全部非空／非注解原 statement，保 text bytes 與 definition hash；不同編輯歷史的 revision 不強行相等。

真正成功的 loadfile 正例增加在兩個新方法：原 generator 的 N64、N512 逐案例真載入，完整 declarations／placed IDs／角色／surface／長度方向／長軸／四角矩形獨立驗證；兩個全新 replay 進程用同一完整 protocol，stdout 原 bytes 相等。另一方法把 N512 每條宣告與放置依原順序送 line，全部成功且不遺漏 preview；最後 geometry／canonical text/hash 等於 loadfile。正常 F 下的 valid513／missing-ID 都拒絕且完整 dump 回覆不變，delete→undo→拒絕→redo→undo 保葉節點與歷史。容量撤 guard 的原反證仍只送 safe missing-ID，不送 valid513。

新 batch 使用 `run_once(...,text=False,timeout=600)`，600 是原 P-189 sample timeout，不更改舊方法時限，也不是新性能 pass 門檻。原 stdout/stderr 仍由實際 subprocess.run 流保全；原五方法的 BridgeSession 是 Popen，正式封裝必另有真管線 capture，不能把 run observer 擴稱為全部管線證據。

撤回／恢復控制在 `EXACT_WITHDRAWALS.json` 分開釘 before/after：

1. 只撤 count helper，跑逐宣告方法，在首 count64 處由 objects=[] 正常 AssertionError 紅；不先撤 population，防早紅遮蔽。
2. 只撤 population 的互動建立，跑 full-capacity history 方法；原 I9 loadfile 拒絕造成正常 AssertionError，必保存對應 bridge 原 error。修後成功建立512宣告。
3. 只撤 canonical unplaced replay 的正確互動路徑，其他修正都保留；方法末段原 I9 loadfile 拒絕造成正常 AssertionError。此項防 population 的先紅掩蓋 replay 錯誤。

每項 fixed／withdrawn／restored 都須真執行並收指令／環境／SHA／exit／原streams。任何 compilation error、timeout、crash 或不相關首紅不算這三刀成功。新 true-placed 之容量整體撤回可在一致宏64 closure的真bridge上用N512正常第65筆容量拒絕；此控制和七個預期 compiler-failure ABI控制分開。所有這些現在仍 UNRUN。

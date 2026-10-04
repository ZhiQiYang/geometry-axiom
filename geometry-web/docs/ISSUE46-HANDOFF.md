# #46 完整獨立快照第一 slice

本分支由最新 main `d1a161f` 建立，只新增模組、測試及本文／未套用 patch。依使用者接受的第 4 項及 Q33：完整 A/B、原圖內容定址去重、B 不改 A、比較後整體採用可回復；不做 object merge，不攜舊 undo。`project-store.js`、`reference-workspace.js`、ContextHistory、app／serve／SSOT／native C 皆未修改。本 slice 不宣稱產品入口、整體採用或 recoverable history 已完成。

## 給唯一共享 owner 的需求

唯一格式／kind registry owner 為 thread `01a100b5-800b-75f2-9a02-71ee53e550ba`。下列是介面需求，**本分支沒有占用新 geometry-canvas 格式號或註冊 product kind**。

1. 決定正式 scenario kind/schema/capability 及 root ZIP 路徑；`geometry-scenario-snapshots/1` 只是此獨立模組的候選 archive schema，不是新 `.gcanvas` 格式。模組 ZIP 不能冒充現有 reader 支持的專案。`/10` 已由 PR104 提供 GridDraft，不另占號。
2. 提供完整讀取 adapter：同步 flush 所有已支持 raw 草稿，核對 context token／frame／revision，輸出 `{manifest,scene,sources:Map<hash,Uint8Array>}`；未可保存的新工具草稿仍須明確阻擋。不要只取 `.scene` 或省掉附件。active native preview 不由模組取消、覆寫或復活。
3. 提供有限附件 dispatch：`validate(envelope)`、`references(envelope) -> originalAssetHashes[]`，可選 `objects(envelope) -> typedObjects[]`。所有正式附件、其原圖及 native refs/pins 必須驗證。未知 schema/kind 或缺 dispatch 拒絕完整封存。#77 `source-plane.references()` 的 `sourceIds` 也須收進來源清單，不能只掃 face pages。
4. PR104 未合前維持 interface；有正式 `project-store`／`feature-attachments` validator 時注入使用。GridDraft 的空字串、非法分母、空選擇及 inactive raw 欄位原樣封存，不能用 unsupported 當作丟棄理由。其他未完成 schemas 未註冊前拒絕／列缺能力。
5. 後續 whole adopt 重驗 current A／context／revision／source closure／草稿處置，原子替換全部 World＋metadata，保留原 A，一筆 recoverable history；undo／redo 使用被保留的完整閉包。owner 的可回復歷史還持有的資產需另算 retention root，不能用模組 `remove()` 取代 shared history GC。

`ISSUE46-OWNER-WIRING.patch` 是以 main `d1a161f` 產出的兩個小接線 seam，**未套用**：read-only `readScenarioProject()` 沿原 save gate／snapshot stamp 取得完整資料；`/scenarios/verify-native` 只啟動 disposable 子程序，不用 `ask_bridge`／live `/upload`。已 `git apply --check`、臨時副本 JS/Python 語法檢查。PR104 或 stage145／44／77 shared 檔案改動後 owner 再套／重驗；本 patch 不是 UI 或 adoption 接線完成證據。WSL 多參數 executable 這個 seam 明確缺能力，不轉用 live bridge。

## 模組介面及保證

`scenario-snapshots.js` 為 UMD，browser `GeometryScenarioSnapshots`。建立時必須注入 `verifyProject({manifest,scene})`，它只准使用隔離原生／model verifier。`project` 預設目前正式保存器，可注入 PR104 或共享 owner 後續正式 validator，必須提供現有 `projectFormat(manifest,scene)`。封存先核對 reader 的場景依賴最低格式，再進 native；不能靠保留 capability 讓低版格式通過，也不用 `pack()` 自動升版／正規化掩蓋輸入問題。沒有實際場景需求的既有額外 capability pins 不造成誤升版。`getState()` 可提供 `{context,frame,contextToken,revision,blocked:false}`；每次 await 核對所有 stamp／generation，cancel 或晚到結果不會提交任何 snapshot／pool 部分資料。host callbacks 為受信任工程 adapter；輸入必須是普通 JSON，任意 JS Proxy 不在可攜資料契約內。

```js
const archive = GeometryScenarioSnapshots.create({
  project: GeometryProject,
  featureAttachments: owner.assetClosureDispatch,
  getState: owner.readScenarioStamp,
  verifyProject: async data => {
    // P.validate/finite feature dispatch 已先通過。只移除正式 reader-only 能力。
    const readerOnly = GeometryProject.readerCapabilities?.([]) || [];
    data.manifest.requiredCapabilities =
      (data.manifest.requiredCapabilities || []).filter(c => !readerOnly.includes(c));
    const response = await fetch('/scenarios/verify-native', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify(data)
    });
    const receipt = await response.json();
    if (receipt.ok !== true) throw Error(receipt.message || receipt.error || 'Isolated verification failed');
    return receipt;
  }
});
const read = await ReferenceWorkspace.readScenarioProject(); // 需先套 owner patch
read.assertCurrent();
await archive.capture(read.project, {scenarioId:'scenario-A', label:'A'});
await archive.fork('scenario-A', {scenarioId:'scenario-B', label:'B'});
// project() 給完整副本；在 B 自有 process/context 編輯及封存，永不上傳到 live World。
const b = archive.project('scenario-B');
// 隔離編輯結果的 sceneHash／原 bytes 必須已完整核對。
await archive.replace('scenario-B', b);
const difference = ScenarioDiff.compare(...archive.list());
const portableModuleBytes = await archive.pack(fflate);
```

每 snapshot 保留原始 manifest（models 的完整 input/source/result、formal scene、engineering/assembly drafts、face projections、reference pages/calibration/crop/observations/reviews、所有正式附件），不降版或 rebuild 成另一份定義。scene／asset hashes、完整 closure hash、typed native/model/draft/page inventory 及 copy basis 都會核對。資產 pool 私有，只共享不變 bytes 的儲存；輸入、讀取、list、verifier argument 都是副本，無 shared mutable Map／PDF runtime 物件。來源 hash 是內容身分；scenario namespace＋kind＋id＋version 才是 comparison key，不把相同數字／名稱／外形當同一物件。

只有明確 `fork` 自動記錄原案 exact closureHash 的 typed copy-origin；public `capture` 不接受自填 basis／origins。它表示獨立複製關係，**沒有實物數量合併的語意**。`replace(B)` 拒絕不同 `projectId`，同案 replacement 保留歷史 basis 並清除全部 current origin pairs；即使 bytes 或 kind/id/version 相同，也不代表 reset／delete-recreate 後物件沿革仍連續。diff／重新匯入均呈 unmatched／unknown；從已編輯 B 明確 fork C 時可建立新的 B→C 配對。ZIP 匯入有 origins 必須是 exact 完整 base snapshot 且 typed IDs 一致，所有有 basis 的 record 都須保持相同 projectId；重算 closure hash 不能讓 edited snapshot 延用舊 origins 或繞過 foreign-project 拒絕。原 A 和 assets 不變。被子方案使用的 exact basis 不能替換／刪除；單案刪除僅回收 archive 中無引用的 bytes。`pack/unpack` 全資料及 original bytes 真 ZIP round trip，解壓、semantic verification 完成才一次 publish。closure hashes 為內容完整性，不是簽章或不受信任 runtime 的授權證明。

`scenario-diff.js` browser `ScenarioDiff` 只接受已通過 archive hash／能力／native 檢查的 plain JSON 輸出。完整逐段 definition compare 保留同值換來源、同外形換接合／分件差異；只有 exact pinned typed copy-origin 配對，其他 unmatched。返回 `scope:'definitions'`、`geometry.status:'not-evaluated'`、`physicalIdentity:'unknown'`；不假稱幾何／料長／施工安全已求值。

`scenario_verify.py` 提供 `verify_project(data, bridge_executable=..., base_executable=...)`／`verify_bytes(bytes, ...)` 及 stdin JSON CLI。每次新 bridge／model-worker process，實際 `load-prepare` final objects、完整 source-inspector inventory、native capability 及每份模型重新 producer 求值。不要求獨立模型的 captured source 仍在 live World。粗粒 typed objects 可供 copy-origin；完整 field/member refs 保留在核驗 receipt inventory，這一 slice 未加入新的持久 field locator 契約。

每份原 model package 先走正式 `verify_package()`，重核合法 axiom tuple、generator、capability、hash、provenance／evidence；再與 saved input 的真 producer replay 逐字核對 definitions／request／derived、source/schema 及語意 summary。合法舊版 package 的原 manifest／generator／diagnostics／presentation 原樣保留，不以當前 producer 的新版描述覆写或誤拒；未知 result/summary/package/manifest 欄位、未支持版本／自洽假 mesh/provenance 仍拒絕。

binary 必須通過既有 `tests.binaries` 的當前 source＋binary build receipt；缺失、未知或 stale runtime 明確 UNSUPPORTED，不退回 unchecked exe。核驗前後重核 bridge/base bytes、source closure、validator 和 axiom pins；crash／timeout／輸出過量／失敗 protocol 不算成功。stdout／stderr 有界，模型逾時連同自己的子程序停止；不動 live pending token、undo、feedback 或使用者檔案。環境變數 `GEOMETRY_SCENARIO_BRIDGE/BASE` 或 `GEOMETRY_TEST_BRIDGE/GEOMETRY_MODEL_BASE` 可指 fresh adapters。

## 容量及 ZIP 邊界

首版工程上限：8 scenarios、256 unique assets、原資產每份 128 MiB、scenario 合併 metadata 8 MiB（包含 manifest／inventory／origins）、scene 16 MiB、descriptor 8 MiB、compressed ZIP 256 MiB、expanded archive 512 MiB；JSON depth 48／1,000,000 nodes、typed objects/origins 各 25,000。只允許降低上限。native scene adapter 保守限 1 MiB、總 native JSON 9 MiB／64 models；超過明列缺能力而不截斷。capacity 預檢在 clone/hash／decoder 巨大配置之前，合法完整資料沒有 silent truncation。

ZIP 設 central/local member 白名單及數量上限，拒重複 member、未知／路徑穿越、加密、多磁碟／ZIP64、截斷、size／CRC 不一致、unlisted bytes；streaming 展開逐 chunk 計費，實際大小／CRC 再核對，不能只信 headers。JSON key（含 escape 後同名）重複、getter、serialization hook、hidden/symbol、undefined／NaN／sparse+extra arrays 等都在複製前拒絕。所有失敗保留既有 archive 及 pool。

## 可重跑的驗收

```sh
python tests/binaries.py build bridge model-base
node --test tests/test_scenario_snapshots.js tests/test_scenario_diff.js
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base \
  node --test tests/test_scenario_review_native.js
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base \
  python -m unittest tests.test_scenario_verify -q
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base \
  node tests/scenario_browser_check.cjs
```

實際 PR104 compatibility 可把該 exact branch 的 `project-store.js` 和 `feature-attachments.js` 僅放到 `/tmp`，再執行：

```sh
GEOMETRY_SCENARIO_PROJECT_MODULE=/tmp/geometry-scenario/pr104/project-store.js \
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base \
  node --test tests/test_scenario_grid_interface.js
```

該 compatibility 未注入時會具名 skip，不能冒充 GridDraft 主線支持。已注入真 PR104 `b2163165` validator 跑到實際 isolated native／ZIP：非法 raw A/B、B 改 raw 不動 A、fresh reopen、unknown kind／能力剝除拒絕。不是另造 GridDraft schema。

browser harness 自建僅服務本 slice 的 ephemeral loopback server，實際 Chromium 1280／390、DOM 下載與 file input 重開、真 native CLI、bytes/diff/latecontext/tamper oracle，另明查 explicit fork 配對及 replacement 後 unmatched／unknown。證據及可重開兩份 archive 在 `/tmp/geometry-scenario/browser/`，未提交 build／私人圖紙／截圖。這是 module browser acceptance，不是正式產品 A/B 建立／採用 UI acceptance。shared whole adopt／history、保存附件 registry、產品入口及實體手機留给原 owner；沒有改 runner/goldens 或跟 #77/#48 競寫。

Refs #46 #45 #44 #48 #77 #43；不以本第一 slice 關閉 #46，draft PR 交 root 獨立 review，未 merge／deploy。

settings 在驗證允許欄位後立即深拷貝／凍結，在 state callbacks 及任何 await 前取得自有 options；fork 的 basis／origins 使用獨立私有參數，不能由 caller 在 pending verifier／hash await 期間晚注入。新增 held-verifier 回歸先在 `78b4e14` 重現非 fork 配對，再驗 capture 的原 namespace／label／空 basis／origins、外來或不存在 basis 注入無效、正常 fork 對應及 fresh ZIP 重開。

PR110 增量複審回歸涵蓋：真 native 接受但正式 raw ZIP reader 拒絕的 parameters／assembly／generation 保留能力降 `/5` 反例、正式 `/1`～`/9` 原資料與模型正例、真正 reset／delete-recreate 同 IDs、foreign project 同 IDs 以及 fresh ZIP／diff 不誤配；unit 另驗 public capture 自填 origins、重算 hash 的 edited／foreign／typed remap ZIP、完全相同 bytes 的 replacement 清配對與 B→C 新 fork。reader format 守門已與目前 main 和實際 PR104 的 raw ZIP reader 作 4,864 個矩陣案例獨立核對，零落差。完整 app CDP、產品 A/B adoption、recoverable undo/redo、正式手機入口未在此 slice 驗收。

本次同實作 bytes 驗證：snapshot/diff 41/41，加既有 model／parameters 保存回歸 63/63、0 skip；新增 JS＋真 native CLI 端到端 18/18、46 次隔離 CLI；native/model Python 33/33；注入實際 PR104 的 GridDraft compatibility 1/1；1280／390 browser 16 個 checks、12 次真 native CLI、0 forbidden live requests、0 browser exceptions。獨立 identity ZIP 複審含合法 fork、edited B→C、重算 hash 及 settings TOCTOU 的反例。

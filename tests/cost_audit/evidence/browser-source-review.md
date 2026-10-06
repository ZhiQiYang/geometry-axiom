# #118 browser / CI native 成本审计（只读）

基线：`11dc339152e05ea811972b8c0c15ff29520207cd`，读取目录 `/tmp/issue118-reporter-20261006/baseline`。先读 `AGENTS.md` 和 `tests/README.md`。本轮没有运行 native executable、build、browser、服务或全库测试，没有修改基线、PR149 或 shared writer。以下均为 source / 已合并公开证据审阅；新文件仅在此 TEMP 目录。

## 当前最小已确认减项：六次 browser core 编译

父任务最新main为 `5e0e92b850209e9e2895612148694c1d1e1e4815`（另一个checkout `/tmp/issue118-cost-audit-20261006`）。workflow、package.json、CDP、space、documents、P76六个文件与上述11dc339 baseline逐字相同；SHA256见 `equivalence.json`。native job冗余npm prebuild已由#122移除（`docs/CI-NATIVE-BUILD-118-20261004.md:9–22`），不是待修缺陷。

**六browser runner每个均编出无人消费的 `.build/core`；可提独立browser-only build入口仅编bridge/model-base，保留全部六个job及12次必需native编译。本轮不改workflow/package，不重跑。**

依赖闭包证据：

- package `:7` 的 `.build/core` 编译没有pre/post hook；workflow只向服务传 `.build/web_bridge` 和 `.build/model_base`（`:74–75`）。目录 `.build` 保留，bridge/base源码/flags/输出路径保留。
- CDP及其require插件没有core launch；三browser入口的实际spawn是Chrome（`cdp_test.js:82`、`space_model_test.js:625`、`documents_browser_test.js:22`）。`canvas_test.js`、`polydraft_test.js`没有被full CDP require，它们在native aggregate的不同入口执行。
- P76 `parameter_workflow_test.js:86–96` 只下载/读JSON/用DOM文件输入导入；`:71,108` 写TEMP截图，**不调用npm产物**。其参数/native请求经API bridge。P76需要 `/tmp/geometry-tests` 截图parent；`.build` mkdir不提供该目录，也不依赖core编译。现有 `cdp_test.js:459–461` 创建full默认截图parent；focused/manual override的parent问题独立，`CI-NATIVE-BUILD-118-20261004.md:127–135`已说明。
- 服务 `serve.py:57–66` launch显式 `GEOMETRY_BRIDGE`；bridge把C核心unity include进自身（`web_bridge.c:24–26`），无需外部core binary。
- 任何模型build/verify经过服务 `/model*` 路由（`serve.py:449–478`）→`modeling/__init__.py:124–126`→`modeling/engine.py:298–309`→`modeling/base.py:106,113–115`，选取并launch明确的 `GEOMETRY_MODEL_BASE`；不是 `.build/core`。
- `polydraft_test.js:987–1002` 是实际core消费者，但用 `GEOMETRY_TEST_CORE` 或TEMP registry路径，属于native aggregate，不消费这个browser runner的 `.build/core`。

最小owner proposal：新增明示的browser-only build命令（例如 `build:browser`），保持原 `npm run build` 一般入口行为；workflow `:62–63` 的browser step只调用browser-only入口。它依次mkdir `.build`、以同 `-std=c11 -O2 … -lm` flags编 `web_bridge.c` 与 `model_base.c`，不编core。native job、matrix六项、fonts、screenshots、runtime、floor、golden、exceptions皆保留。可静态确认删除 **6次core编译**；实际wall time收益未测。新脚本/package提案需新#118owner具体patch与针对实际browser消费路径的验证，不在本轮实施。

## 进一步重复入口候选

**默认 CI 已确定的整组重复是 assembly、grid focused 与 full canvas；最大静态 fan-out 是每个 browser job 都重编同样三支 native。没有当前 SHA 的分组耗时，不能将步骤数量排名伪装成秒数排名。**

| 项目 | exact source / flags | 已确认范围 | 当前节省时间 |
|---|---|---|---|
| 默认 focused assembly 重复 | `.github/workflows/integration-tests.yml:38–39,89`：`GEOMETRY_ASSEMBLY_ONLY=1 node geometry-web/cdp_test.js` | `cdp_test.js:7025–7026` 在 full 和 focused 均执行 `assembly_workflow_test.js` + `assembly_context_entry_test.js`。full golden `cdp_sections.golden.json:79–80` 有 P77=134、P82=16。重复 150 断言，不代表 150 个 E2E 场景。 | 未测 |
| 默认 focused grid 重复 | workflow `:42–43,90`：`GEOMETRY_GRID_SYSTEM_ONLY=1 node geometry-web/cdp_test.js` | `cdp_test.js:7008–7011` 在 full 和 focused 均执行 `grid_system_test.js` + `grid_rule_editor_test.js`；前者 `:244` 再执行 `grid_trial_test.js`。full golden `:71–72,88` 有 P70=113、P71=9、P87=60，共182断言。 | 未测 |
| browser 的 native 编译重复 | workflow `:36–49` 六项 matrix；`:62–63` 每项 `npm run build`；`package.json:7` 固定各 gcc core、web_bridge、model_base | 六个独立 runner 各做三次编译，共18次。native job `workflow:27` 另以 `run_all.py --build` 编同源 registry 原生套件。browser 实际只导出 `.build/web_bridge` / `.build/model_base`（`:74–75`）；core 没有被该 browser 流程使用。编译次数是 source 静态推断，不是本轮实跑计数。 | 当前 CI 未测 |
| space / timber 的局部重叠 | workflow `:92–93`；`space_model_test.js:1092,1365` | 两者都执行 font-layout 19条、各自 setup2/health2。**timber-material48和timber-source-guards8不在full-space-suite内**（`:34–36`、`space_test_floor.js:3–16`）。整组 timber 不可删除。 | 未测 |

assembly/grid 的 focused 调试能力仍有价值，但每次默认 PR/push 已强制 full canvas 时，另跑同组不是正式覆盖所必需。它们当前让反馈及截图更早出现（workflow `:84–86`），这个便利与额外 runner 成本应明示，不能宣称增加独立覆盖。若 full canvas 前段失败，focused 可提供后段局部诊断；它仍不能把未完成 full 变成通过。

## 第二个 owner proposal：默认 focused 重复（无需改测试逻辑或 golden）

1. 只修改 workflow：默认 matrix 保留 **documents、canvas、space、timber**；移除 assembly/grid 两个默认 entry 及对应 case（原 `:38–43,89–90`）。保留 `fail-fast:false`、独立 runner/server、TEMP feedback、fonts安装、16MiB stack和现有 timeout。需要逐组诊断时，保留现有 `*_ONLY=1` CLI 用法；未来可单独提供明示手动入口，不把 partial 当正式 full。
2. assembly 截图上传条件 `workflow:101` 改由 canvas 产物承接，保留 `:104–107` 路径/期限。相同 full 执行仍写 `/tmp/geometry-tests/assembly-desktop.png` / `assembly-mobile.png`（`assembly_workflow_test.js:57,62`）。grid 上传 `:109` 改仅 canvas，保留其路径/期限。否则减项会意外丢失截图交付。
3. 保持正式无 filter `node geometry-web/cdp_test.js`（原 workflow `:91`）。**不删 full 内的 assembly/grid 模块，不添加 skip，不设 UPDATE_GOLDEN，不调低任何 floor。** 当前 golden 83段/2054（`cdp_sections.golden.json:3–4,5–88`；`tests/INTEGRATION-GATES.md:188–190`）。
4. 继续独立无 filter `space_model_test.js`（202条）和 `GEOMETRY_TIMBER_ONLY=1 space_model_test.js`（79条）。最小方案保留这两者全部断言，包括重复的19条font-layout；去掉它需改 scope census/新模式，收益未测，不值得与第一减项捆绑。
5. documents 是独立入口（`documents_browser_test.js:19–96`），并未被 full CDP require；保留。`tests/INTEGRATION-GATES.md:74–103,150–158,161–190` 列的 formal owner、#77/#116/#48/#61等独立 gates，不因 full CDP 或本 CI 减项而取消；source 文件声明的独立范围继续成立。

单独这一改动静态减少 **2个浏览器runner/启动/服务、6次native编译、2次fonts安装及对应focused重复**，秒数未测。如果先做上述browser-only build，则这一步额外减少的是两个job的 **4次bridge/base编译**，不能双算core；组合旧18次→剩余4runner各2次=8次。适用前提是 full canvas 仍为 required 完成条件；若仓库分支保护绑定了 `browser (assembly)` / `browser (grid)` 名称，实施时须同步审查 check 配置，不能用假 pass 或长期 skip 掩盖。

## native build 交接候选（独立第二步）

现状 native 与 browser 没有 `needs` / artifact handoff；package build 是每次无条件 gcc，registry 是来源未变即沿用（`binaries.py:539–544`）。不能仅让 browser 改成 registry build 就宣称跨runner复用：六个runner各自有空TEMP，仍各编。也不能拿 `.build` 的手编产物当已有 freshness receipt：`tests/INTEGRATION-GATES.md:126–127` 明确区分。

候选 topology：一个新 `native-build` job 使用同 SHA、同 Linux compiler/platform 的 `tests/binaries.py build` 生成全部 native aggregate 所需适用产物；打包 **binary + 原sidecar + SHA/tree/平台/编译命令manifest**。native测试job与四个browser测试job仅 `needs:native-build`，都下载同一份本次run artifact。native沿 strict `run_all.py` 执行；browser把明确已验证的 registry bridge/model-base绝对路径赋给 `GEOMETRY_BRIDGE`/`GEOMETRY_MODEL_BASE`，删除 browser `npm run build`。这样 native测试失败仍不会取消browser siblings；若直接 `browser needs:native`，native assertion失败会使浏览器全部不跑，会削弱目前故障隔离，因此不建议。

交接必须复用现有 source/command + raw bytes freshness 核验：`binaries.py:297–330,338–343`。当前 sidecar还比对 `exe_size`/`exe_mtime_ns`（`:198–203,328–329,599`），普通直接upload/download可能改掉metadata；用保留纳秒mtime和execute mode的容器归档，并在接收端验原sidecar，不能根据下载文件补发sidecar或绕过mtime。归档往返与同编译平台兼容性本轮未测，是实施验证项。

服务 readiness 原 workflow `:79–83` 只有首页curl。交接设计必须同时保留/补上 exact `/runtime` 核验，而不是靠固定 release header：`AGENTS.md:90–92`；`runtime_version.py:169–176` 要求schema、`fresh:true`、版本等于当前source、root等于当前checkout。独立新服务不能继承别人的live state；测试freshness只读核验不触发build/原生launch。没有handoff的每个独立runner仍需自己的bridge/base，**不能把现有18次全部当可直接删**。若先做browser-only build，跨VMhandoff进一步可复用的编译量是六runner的12次bridge/base（或缩为四runner后的8次）。artifact传输/排队是否抵消部分wall time尚未量测，不能给预期秒数。

## 已有测量的正确解读

| 公开 evidence | 实际测量 | scope / 不能推论 |
|---|---|---|
| `docs/issue123-c-pending-tests/measurements/t3_cdp_b6_patch.json:3–4,5–22` + `t3_cdp_baseline.log:356–361` | 620s、exit1、未完成、322/1；P35此前14/14。fatal是`fe.timbers.length===1`。 | FROM_P31 partial；这是失败后重跑的诊断成本，原因未结案，不可标为已确认可避免重复。保留第一次失败证据。 |
| 同JSON `:24–37`、`t3_cdp_baseline2.log:809–813` | 1055s、exit0、completed、761/0 | partial，P1–P30未跑，golden未比；raw记录1次browser exception，不能称零异常。 |
| 同JSON `:39–52`、`t3_cdp_patched.log:809–813` | 1089s、exit0、completed、761/0 | 不同补丁状态的对照，不是同状态无意义重跑。也是partial，不能报full耗时。 |
| `t4_space-flow_baseline.log:55–57` / `t4_space-flow_font12.log:55–57` | 58s / 59s、partial43/43、0exceptions/consoleErrors | setup2+space-flow39+health2；不同字体补丁状态。非full202，不可据此删其余空间guards。 |
| `docs/issue123-evidence/RUN-LOG.md:19–33` | stage_g第1次未完成、第2次草稿confirm受阻、第3次成功；stage_h第1次受阻后重跑 | 失败/受阻后恢复，不能当默认重复入口成本。`:3–5`高CPU/低内存下环境归因是当时作者判断，产品因素未独立排除。 |
| `docs/assembly-validation/linux-{core,bridge,model-base}.fingerprint.json:4–6` | 2026-10-01历史build_seconds=18.3/22.0/17.2s，共57.5s | 源码不同的历史registry build+smoke耗时（`binaries.py:549,586,598`）；**不是main11dc339的npm build或CI测量**。旧sidecar也不满足当前raw SHA字段要求，不可用来授权binary复用。 |

测量显示“为P35单点问题执行FROM_P31尾段”是明显宽入口候选：两份完成结果761条里目标P35为14条，其余747条不等于747个独立场景。仅将其作为开发期新增P35专用focused入口的依据；现无P35-only flag，且 `waitForFaceViewport` 还在 `cdp_test.js:5821` 被后段调用，不能直接删/抽出共享helper。该入口需保留场景setup、实际trusted操作与viewport一致性断言（`:3969–3995`），声明partial、独立count floor，最后仍跑full CDP。没有section timer，**不能宣称能节省1055/1089s或某个百分比**；原历史对照/失败重跑不据此追认“浪费”。

## 必须留下的 guards

- CDP full严格每段golden比较（`cdp_test.js:318–344`、`cdp_floor.js:44–68`）、完成结果/致命结果分开（`:7035–7057`）、强制隔离URL/TEMPfeedback及唯一scope（`:11–25`）、owned browser CDP（`:150–158`）。partial不能更新golden。
- Browser exception不能用“exit0”抹掉；当前严格匹配单次预期探针，其余全部增fail（`cdp_test.js:165–170`）；P38 `fb-auto-probe` 测试完整保留（`:4344–4359`）。full预期有一次probe事件不等于未处理异常豁免通配。
- space census独立、精确每组count和completion（`space_test_floor.js:19–49`），全scope202 / timber79不合并计入场景数；space浏览器exceptions与console errors都为0（`space_model_test.js:1369–1396`）。
- formal app.js fullCDP与space独立必要（`AGENTS.md:271–275`、`tests/README.md:64,68`、`tests/INTEGRATION-GATES.md:102–103`）。不以canvas bridge测试、Python、VM adapter或prototype结果替代。
- fonts CJK、timeouts、16MiB stack、回报/截图/profile TEMP、exact runtime/source/native byte guards及正式保存/exception断言保留。`room_outline_test.js:12–15`的15000是条件等待上限，不是每次固定sleep；未测实际等待，不计为已确认可删除的15s成本。

## 支持证据与边界

本报告仅引用已合并source和公开evidence的文件/行号及筛选事实，不复制原始个人TEMP路径、PID或raw包。本轮不读取或发布旧held142 packages，不接触私人图纸或私有原始资料。当前SHA没有新性能测量；branch-protection配置、artifact往返metadata及当前runner耗时未核验。实施需要新#118具体patch后的验证，PR149(head `2c3ba8faf907737e33e4c1432e22525da284a75e`)保持不动。

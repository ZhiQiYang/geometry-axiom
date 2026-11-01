# #348 外部指令階段觀察器草稿

**外部工具草稿、Python反例及最小合成C協定校準已完成；產品 ELF、原512與根因仍未驗。** 沒有編譯產品、執行512/perf/browser或使用heavy鎖。新的C校準只編小stub加本wrapper，約1.16MiB原件另存於 `/tmp/geo348-synthetic-c-protocol-20261025/`；最初「未編C」的草稿文字完整保留在 `README.before-synthetic-c.md`。

來源界線與下一步見相鄰 `geo348-command-boundary-diagnostic-preparation-20261025/PLAN.md`／`FACTS.json`。原兩個600秒逾時仍是 F0f `0f695866c0ba12d2c70dfd7d40628d0fda0f905f` 的四指令批次，F73 `73b21e64dce72f0d16ca29e18559c51815b9724d` 沒有重跑它們。原 ELF hash-only，不能冒充已保留 ELF payload。

## 檔案與協定

- `trace_wrap.c`：額外 TU，以 GNU ld `--wrap=fgets`、`--wrap=fflush` 觀察主 loop。只對 stdin/stdout 包裝；scene/tmpfile 讀寫直接呼叫原函式一次。保留原 return/errno，stdout/stderr 不加 marker。C 為 Linux、單程序、單執行緒草稿，已在小stub完成編譯/link及實際符號命中；產品ELF尚未校準。
- `sidecar.py`：讀 JSONL 階段事件與64-byte native-endian status，檢查事件順序、四個原指令與實際 stdin 行長、flush配對、EOF/read-error、clock與status一致性。所有輸出 `product_gate_verdict`／`root_cause` 保持 null。完整 JSON 回應與幾何／golden 另由原裁判驗，不以階段事件代替。
- `launch_diagnostic.py`：固定單次 `subprocess.run(..., input=原bytes, capture_output=True, timeout=600)`，不拆4×600；保留 CompletedProcess／原 exception 物件、完整或 partial 原bytes。觀察器寫檔或close出錯不能替換原TimeoutExpired，且診斷會標不可判。它不編譯產品，也不接替原H7。
- `selftest_protocol.py`／`prove_python_protocol.py`：只用 Python 合成 events 與注入假 runner；沒有執行其 `synthetic-never-launched` argv，更沒有編C、啟bridge或跑效能。

兩個獨立FD透過 `GEO348_DIAG_EVENT_FD`、`GEO348_DIAG_STATUS_FD` 傳遞；都必須>2、可寫普通檔、不同FD與inode。status精確64bytes：`magic=0x3334384449414731, version=1, attached, attempts, successes, faults, 0, 0`，各為同機native uint64。父程序在原child被reap後才讀。wrap初始化失敗、漏事件、寫檔/clock錯誤均不可判；kill在event寫入與success累計之間也保守視為不可判。

## 已做的純 Python 自證

`python-proof-r2/RESULT.json` 保存32項工具檢查的三階段原指令、exit、stdout/stderr：**0／1／0**。撤回只移除實際input行長比較，唯一紅是 `reject-wrong-command-line-length`；恢復拒絕它。涵蓋四指令順序、原600只有一次、flush未結束、clock回退、錯標EOF、部分寫入、未附著wrapper、錯fixture、原partial bytes、原exception身份、recorder及close失敗、nonzero child prefix等。這個反證只證明工具規則，不能冒充任何產品反證。

初輪 `python-proof/`（27項）完整保留；對抗審查發現close可能蓋掉原例外、fixture只驗自洽hash、畸形flag邊界三點後已修，r2補足並重跑。後續若工具再改，須新增新phase目錄並重做同工具反例，不能覆寫r1/r2原件。

`repaired-guard-proofs/RESULT.json` 另外將四個修正各自撤回：固定512 fixture、close不蓋原TimeoutExpired、flush-enter的rc、非負libc flags；四組都取得原 **0／1／0**，共12個純Python原指令／完整stdout/stderr。沒有將一個input-line-length反證泛稱為所有修正的反證。

## 仍未做，不能寫成通過

另包真C首輪已有61checks／26CLI，正常13events、wrapped/unwrapped raw bytes、非匹配FILE/NULL及errno、stdin/stdout EBADF、eventFD故障、256KiB stderr、5段stdout、真0.25秒TimeoutExpired partial與kill/reap均核對；C漏flush-return使真正guard紅，恢復綠。actual獨審355項／exit0，SHA256 `cf629f40fafd55259ab3a61554b7de035ed55c855a32aafba4f931df9d5eb067`。0.25秒僅屬合成hang控制，不改產品600秒。首輪缺env/disk preflight照實保留；第二輪只有草稿/preflight且UNRUN，沒有為補記錄重跑已收件protocol。

1. **產品ELF編譯／link／ABI與原實際CLI命中校準**：F0f已釘原 `web_bridge.c:1032` 有stdin fgets、`:1183` handler後stdout fflush，相關原編譯為-O0。但這只是產品來源證據；已成功的小stub不是產品。compiler builtin、fortify或其他轉換可能繞過普通符號；須對新產品診斷ELF保存原nm/objdump/link命令及完整流，再由精確ELF校準兩個wrapper命中及原bytes。不得以Python或小stub資料冒充產品ELF校準。
2. **尚未涵蓋的C故障分支與正式launcher整合**：原Python injected runner之後已有小stub真pipe與C0/1/0；但C的錯FD初始化、實際partial write、clock錯誤等完整矩陣仍未注入。真pipe由獨立校準driver執行，不代表 `launch_diagnostic.py` 已與真C做端到端整合；PLAN第5項仍須依實際缺口完成，不能籠統稱所有觀察器故障皆驗過。
3. **原N512診斷**：仍UNRUN。CLI預設不執行，必須明示 `--execute-diagnostic`，加精確source、ELF、build receipt與同ELF的calibration receipts。收據SHA釘住只證明檔案身分；其內容仍須獨審原CLI，不能用手填成功摘要代真正校準。
4. **任何產品修正／正式門檻**：沒有更動；600秒、原O0、golden、四指令順序與後段所有512幾何/replay/history斷言保留。診斷ELF時間不混入正式資料，R8的有效36樣本完全不動。

CLI固定fixture為 SHA256 `760a7169ea3577341b4b0ec1b56ea39c21c85c777434325ec906debe0a816f10`／45,154 bytes，換N64即使自己提供一致hash也拒絕。這份原fixture是在第二次timeout期間補存，不能追認第一次preexecution bytes。新診斷必須執行前重新封存真正輸入及source/ELF；F0f到較新來源的輸入路徑變更要保存完整實際stdin，不正規化stdout。

新診斷由root排程在full123之後的獨占時槽。最終source SHA由root另固定，不能將這份草稿或新ELF套回原F0f的執行身分。

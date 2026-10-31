# F8 完整帳本終態收件草稿：尚未收件、尚未採用

本目錄現在只備工具，沒有掃描、凍結或雜湊正在執行的 JOB/cache/outer payload。只能由 root 收到原 exec 真終態後，另存新的 BOUND_REQUEST.json 與原工具 FINAL 回應，再以已審工具執行。原未綁 request 不覆寫。

沿 `/workspace/prepare_geo337_ledger_4f4_terminal.py` 的原範圍：JOB 與原 outer 全部 regular 原件；cache 只有 M*、_baseline、_bridge-baseline 中 `.stdout/.stderr/.json`；原 driver/observer/map/capture/reaper 以及此輪 launcher/resource helper。額外帶入本收件工具與真 terminal 控制原件。未加入 ELF、source tree、Git objects 或整個 cache payload；observer 原件中 inline source preflight 仍原樣保留。所有原路徑保留，無 delete/move/link/checkout。

`verify_terminal.py` 只核真終態 metadata；`collect_terminal.py` 再核同一綁定，才列出原範圍並封包。兩者都先取得既有 heavy＋secondary 非阻塞鎖，確認 original ROOT/job/cache/tmp/outer 沒有 argv 或 cwd consumer，且要求 root 獨占 lease。原 final tool JSON 必為原 exec 回應形狀：整數 exit_code、無存活 session_id，與原 outer/root 結束碼一致。若外部工具回應封裝不同，先另審精確 adapter，不捏造回應或擷取假 terminal。

只有 CLI0/root0/outer0、原完整4phase（舊tracked check如實保留，full/map/newcheck各0）、observer complete、原map/bridge完整、123列/120個自然F8 head/3 retired、來源前後一致，才列 `formal_accepted=true`。這是原條件交叉核對，不新增突變 verdict 裁判；保留原killed/equivalent/crashed分類。還必須由另一peer核原每列/原流與封包後才可採用。

失敗也能封存已結束的原件：`collection_exit=0` 只表示封包成功；terminal formal_accepted保持false並列所有失敗條件，禁止採用。若缺少原root/outer/tool真終態，工具拒絕，原件仍在原處，不能把正在跑或被截斷的狀態叫terminal。所有結果寫入全新OUT，不覆寫失敗原件。

封包前只在已終態的 scope 列檔/stat；依輸出filesystem計算完整未壓縮大小＋每葉padding/headers＋索引保守額度＋root指定reserve，入場失敗不建OUT。每葉讀取前後metadata一致；tar全部regular、逐葉hash回讀相等，scope與終態pin前後一致。該預算是collector資源入場，不是native/browser預算，不用其他device free抵帳。

root 執行形式（全部未綁，現在不可執行）：

```
python3 -B verify_terminal.py --request <NEW_BOUND_REQUEST> --request-sha256 <ACTUAL_SHA256> --preparation-sha256 <REVIEWED_PREPARATION_SHA256> --out <FRESH_METADATA_OUT> --root-terminal-lease
python3 -B collect_terminal.py --request <SAME_BOUND_REQUEST> --request-sha256 <ACTUAL_SHA256> --preparation-sha256 <REVIEWED_PREPARATION_SHA256> --out <FRESH_PACKAGE_OUT> --reserve-bytes <ROOT_ACCEPTED_SAME_DEVICE_RESERVE> --root-terminal-lease
```

root 需以原 c387 outer 收全 argv/env/exit/stdout/stderr；這兩指令本身不替 root 建另一正式驗收。metadata self-test為純合成分類反例0/1/0，不讀實際run，也不代表帳本已過。採用步驟僅寫在 ADOPTION_PLAN.md，沒有可直接跑的舊b6 IDs或Git寫入工具。當前F8/R8真execution不改標F9。

V2 修正：四個可缺子件 observer/map/bridge/ledger 即使 JSON 截斷、重複鍵、UTF8壞或非object，仍記 raw hash/bytes 並保原件入tar；parse_errors強制formal/adoption false。只有三個根終態綁定保持嚴格拒絕。V1保留未執行，不能用其收件結論替V2。

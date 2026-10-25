# R8 收件外稿狀態

來源 F8 `75a1e93811a52b69385cbdaf6a09d773ed9052ad`。正式五 stage 已由 root 執行，本工具不重跑產品或抽樣。

- `adapt_r7.py` 只讀小型既有 producer，寫出必要參數外稿與 unified diff；AST parse 完成。沒有跑任何新增自測鏡像。
- `summarize_terminal.py` 固定 SHA256 `7a9d89c5c0ef901e6b52dffe0385329d9837959a4cebd7872d18dbf624ef3e1e`。
- `launch_summary.py` 固定 SHA256 `8c7f5f3564134a3bfaffedbadf8d965fb5878035ca1c35a7bc3da29b95b5f03d`，c387 捕捉小摘要原命令／exit／stdout／stderr；不 freeze、不壓縮。
- Root 授權後、小稿獨審35/0後已產小摘要：31716B、SHA256 `23c0b08133a48285bb7fd75192a9b05a2fb190fa04ca5dc5cadfb28e28a4e5dd`，producer／outer 真0，路徑 `/tmp/geo323-r8-terminal-summary-20261025/SUMMARY.json`；原正式五stage outer exit1保留，不移標。小摘要actual獨審另送 reviewer。
- 原 API INITIAL/POLL01/POLL02 均真 session62076；POLL03 真 exit1/chunk2aff4e，完整原物件位於 stage tools。freeze 將保存原 bytes，不補造缺失回應。
- Root 放行後，freeze／collector／outer 真0。固定PLAN SHA256 `8c7758c125b3dc83ff10ae57dbeef85e3641f9d4648cd66f956c6bd46a290742`，9050選定原件（9043 payload＋7 ELF hash-only）；只有一次封包，無重跑產品。
- 真完整 archive `/tmp/geo323-r8-full-package-20261025/ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz`：31,362,296 bytes、9057members、SHA256 `4503955cefc6fb1a6491ad2a146c259e59a2185401d0fbebc09908a47e3bf9d0`。RAW_INVENTORY SHA256 `1136cfce6ec822b18bec2e782ca67eb24b5d02c25e4620a9f833453efe8e2c57`。
- Collector 於2026-10-25 06:58:45 UTC真終態0並釋heavy.lock；已通知root可接ROOT四鎖preflight。完整actualpeer已交 architecture_actual_review，尚未收到終態不得冒通過。
- 已入archive的README/PROVENANCE/工具與原件全部保持原byte，裡面的UNEXECUTED是準備時點；後續實際狀態以 PACKAGE.json、collection-outer/RESULT.json、execution/RESULT.json與本NEXT為準。不要為修改歷史狀態重寫已封存原檔。
- 狀態與引用如有後續，以原執行 RESULT 和 reviewer 回條為準；本 checkpoint 不宣稱正式 gates 全綠。

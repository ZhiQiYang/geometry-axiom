# 不帶木工模板子項：接續位置

唯一 owner `/root/own_kernel_no_wood`，預定 branch `codex/kernel-without-woodworking-20261023`。所有準備都在本目錄；尚無正式 source worktree／branch／commit／push，未碰 `/workspace/geometry-axiom`。目前不編譯、不開 Chrome、不跑掃描或測試，不重產全域帳本。

底本是 F13 `13d02c1db7022145a52ee063286a558e595eb212`。private bare metadata 在 `metadata.git`，只讀借整合 repo objects，不含 origin remote；fetch 請用公開 URL `https://github.com/ZhiQiYang/geometry-axiom.git`，或先只在這個 private bare 設 origin，不能改整合 repo。

候選只改 `tests/test_rectangular_template.py`：幾何木工根套件 blocker、真可匯入 sentinel 控制、K quoted-include 不能依賴可取得的 W header、有效 W include 編譯／執行後由原 source gate 抓到。原 11 項保留，新總數 13。

- `candidate/test_rectangular_template.py.patch` SHA-256 `2b14c750746c3c7912bc6fa8b3119ea4672e003a206f9a4eb71ffba0639aaaaa`。
- `candidate/test_rectangular_template.py` SHA-256 `7d0de74bbcbc436044aba1bb98cb197a21d77f46fb990847cb3dad5580d510c6`。
- `run_proof.py` SHA-256 `dc7444f5a00e9005d3e0dce533db5fb00087dcae2c00b4980299dae88be4dedd`；AST-only 0，尚未執行。完整 baseline 與撤回／還原兩個 guard，預期 `0/1/0/1/0`，內部實際 K→W include 的 source gate 再有 `0/1/0`。每個 phase 重新從固定 Git commit 的 11 檔安裝；用 `--test-override` 只能作明列 preflight，不能冒同 SHA 正式驗收。
- repo 外正文模板 `PR_BODY.template.md` 全待驗項明標 PENDING，沒有當正式正文推送。

已取得 #318 owner 的靜態對抗審，文件 `/workspace/geo318-reading-a-prep/REVIEW_NO_WOOD_PREP.md`，未見確立 blocker；它未編譯／執行測試，不能當正式動態驗收。原指定 #314 reviewer 的回覆仍待。

下一步等 root 安排極小 sparse worktree 與編譯時段。可以由本 private bare 建 `/workspace/kernel-no-wood-work`，只 checkout 11 個 SOURCE_FILES、AGENTS／vision，避免 full clone。先只動自己的葉檔，English commit／普通 push，再以 committed SHA 跑 `README.md` 的正式 proof 命令，封存完整原 streams。

共用順序 #323→#314→combined→#318→本子項。只有 #318 前棒正式推穩後，才普通 merge 其分支，再將 `tests/run_all.expected.json` 的 `py:test_rectangular_template.count` 11 改為 13（如前棒改過要先對真來源重新判斷）。共用 tests/mutate.py、全帳本及架構收據由 root 最後處理；不在本子項私產。最終 targeted proof 必須再綁正式合後可解析 SHA，最後 PR_BODY.md 推 `<branch>-prbody`。

獨立已做的讀取審查：

- `REVIEW288_SPACE.md/json`：原 F13 space 242/0/completed、15 分鐘內，明列沒有驗 timber 群組；未重跑。
- `REVIEW318_CANDIDATE.md/json`：核條文四項精確變更，保其他文字 bytes。指出目標長軸方向不得擅加限制、真 RC face 不能換 free-gap、returned FEATURE 負控、duplicate-ID 不能新創全域唯一假設與 caller 不能早回傳跳過 collision。正式 native/oracle/reader 收據仍未出，待後續對抗審。
- 最近自己 fetch/read handoff 於 `review-refresh-20261023T072414Z/`，handoff 仍 `ea2748248d47563f8559638ccb70ec0ed21910d9`；#318/#288 原 review bytes 未變。前次 refresh 因 private bare 未設 origin 而 exit128 的原輸出保留，改為明確公開 URL 後 exit0，沒有冒為產品紅或覆寫失敗記錄。

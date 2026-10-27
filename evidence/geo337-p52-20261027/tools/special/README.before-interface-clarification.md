# P52／P-189 最終來源參數綁定（只準備，未執行）

`L` 是 root 稍後提供、GitHub 可解析的完整 final 40 位 SHA；`R` 是該 SHA 的乾淨獨立私有來源 checkout。此工具不 clone、不 checkout、不改 R；可使用 root 瀏覽器 source pool 另配置的乾淨 checkout，但須沒有其他 consumer，且完整產品／fixtures 已物化。不得使用仍執行 ledger 的 ROOT/SEED。

先按 PREPARATION 的 SHA 核對工具；root 仍以原 c387 最外層包住以下完整 argv，外層不新增 timeout。每次 `O` 必全新；P52 因原 Chrome profile 長度及既有 formal guard，O 必在短的 `/tmp`；P189 可以 `/workspace`。TMP、測量、streams 都在 O 的私有子目錄。

```sh
env -u NODE_OPTIONS -u PYTHONOPTIMIZE python3 -B /tmp/train337-final-p52-p189-prep/run_special.py --gate p52 --repo R --sha L --out /tmp/g337p52L --main-repo /workspace/geo288-main-merge-20261023/reference/main --heavy-lock /tmp/g261r3/heavy.lock --preparation-sha256 PREP_SHA256
env -u NODE_OPTIONS -u PYTHONOPTIMIZE python3 -B /tmp/train337-final-p52-p189-prep/run_special.py --gate p189 --repo R --sha L --out /workspace/g337p189L --heavy-lock /tmp/g261r3/heavy.lock --preparation-sha256 PREP_SHA256
```

P52 formal `af5cfe9f…`、runtime inventory、四個 protocol 都逐 bytes 原件；直接使用已審 generic `--sha` 綁定。固定 main adba 的現有乾淨 reference/main 會再核 source/runtime inventory，原 npm build 未省略。原 main/fix/fix/main 各 8，共兩側各 16；五個原控制 0/0/1/1/1、原 900/5000ms、原 1200s/90s 皆不變。原 formal 自取 R3，外層不重拿；verifier 仍執行完整原 9 assert，僅 adapter 的寫死舊 final 改為顯式完整 SHA。正式 command/rc/log 投影明列 derived，不冒作原 stdout。這不是 P52 runtime 產品撤回／恢復的額外專項。

P189 固定 **main adbaebf9c73ea6801d7b4d5214e4b846b132923b／base 3e600772076465fc65a26ac09055028301c0fb0b／L**。只改 paths 與舊 baseline 的準備層：已存在的兩份基準 ELF 逐 byte/hash核原 provenance、source rev-parse、完整 archive 及原 gcc O2/-lm compile 證據後 copy2 到新 WORK。原完整 baseline stdout/stderr 以 lossless gzip 封存，附原／壓縮 bytes/hash；不聲稱重新編譯基準。final 仍執行原 git archive＋gcc。所有 dump、36 次交錯、每點 fix/main ≤2、原 600/900/1800s、原 single family、整個原 timing/裁判 tail 都未改；不換成 #323 的 b74 或 ≤1.3。P189 外層取 R3 並設 16 MiB stack，必須 root 獨占排程。

原 P189 dump 若第一個完整 stdout 差異即真 assertion 紅，原腳本會在 timing 前退出。保留全部原 exit/scene/streams，不放寬或 normalize；其它專項繼續。若 root 要同一輪另收性能，可在該真 dump 紅之後以全新 O 跑下列獨立階段（原 full 仍紅，**不是整項 P189 通過**）：

```sh
env -u NODE_OPTIONS -u PYTHONOPTIMIZE python3 -B /tmp/train337-final-p52-p189-prep/run_special.py --gate p189-timing --p189-full-out /workspace/g337p189L --repo R --sha L --out /workspace/g337p189L-timing-only --heavy-lock /tmp/g261r3/heavy.lock --preparation-sha256 PREP_SHA256
```

此補項需核原 full 是正常 dump AssertionError/exit1，將三份已建 ELF 精確複製到新的 WORK，執行原 `scale_compare2.py` 及原 verifier 的完整 timing tail。原時間樣本尚未開始才可執行，不做重抽；scope/overall_P189_passed=false 明列，原 full 原件完全不改。新 timing receipt 的 dump_count=0，只屬 timing。

磁碟：兩 baseline ELF 共 1,773,464 bytes，copy2 增量約 1.8MB；baseline 原 archive stdout 共 30,801,920 bytes，讀取驗證後在新原件中 lossless gzip，壓縮量待真跑。final archive/source/ELF 與 36 原 streams 的尺寸需在 L 固定後估計，沒有宣稱峰值已知。P52 source 不另 clone、歷史 main 不另複製；Chrome profiles／build 暫存仍需空間，root 執行前核 df。所有性能 phase 僅 root 排程；此目錄沒有執行量測、build、版本命令、clone 或 source import。

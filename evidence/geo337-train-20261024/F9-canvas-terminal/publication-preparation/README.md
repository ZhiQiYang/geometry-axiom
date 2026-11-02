# F9 canvas 本批出版範圍（外部草稿，尚未 push）

來源固定 F9 `4f8a794f4167c3562eb182045102e86e9e37cca9`。由 root 以一般 commit/push 出版；本工具只列 immutable 檔案及 SHA256，不寫分支、不重測、不另複製大 payload。母證據 E=`c32e70aa2c848f89a0e2e9fd92ed232a4dd27bcc`，母正文 D=`1c601b40a6f5e0e1d50461186736d469666db4b9`。

`FILES.json` 使用既有 publisher 的 source_path/destination/bytes/sha256 schema。scope 包含四個完整 tar、原 inventory/parts/budget/collector/requests、inventory 與 collector 的 c387 原命令／stdout／stderr／stdin／exit、真 tool FINAL、原 canvas 實績 peer 與包 actual peer、v1/v2 原工具與差異，以及母 E c32 的 CI 原查詢。母 E 的 total_count=0 只代表當時無 runs；新 E 的 CI 未讀。

四包保留全部選定 660 members：656 regular、45,780,854B，加 4 symlinks。原 launch/storage 的普通 ELF/cache/profile/診斷全收，沒有未知 ELF 排除。SOURCEPLAN 的 5 個 Git metadata／mutable latest 原葉僅精確 hash inventory，Unix socket 僅 metadata；原 payload 保留，private index 的完整封存另案，不聲稱已在本包。原 canonical source/seed 與 git objects 不打包。

`PR_BODY.template.md` 只有新 E 身分與 canvas link 使用 `{{EVIDENCE_HEAD}}`，待 root 真 push 後替換；PROGRESS 用所在提交／relative link，不能假造自己的 commit hash。原 E c32 的 110515 bytes PROGRESS 原文完整保留在 history，只最上矩陣代表 current。NEXT.delta 只供 root 更新 handoff，不改其他工作線，也不聲稱已寫入 handoff。

canvas workflow/wrapper/35-minute gate 均 0；1723.223173 秒、2267 assertions、85 段 golden、P73=69/P88=143。原件 peer170/0 和 package peer5396/0 分列。P38 expected fb-auto-probe exception1、P53 API 故障和取消網路請求均保真，不能把總診斷值改成0。這是一輪完整 canvas 通過，不外推重複穩定性、其他 browser 或專項。

新 F9 comparison 單項真 outer/stage0、12:14:21 UTC終態，逐列／175-350與完整原流由另線獨審、另批公開，本批沒有收其摘要或原 payload 充當已公開的完整 gate。歷史 F8 R8 outer1/exact1 與原36性能樣本不移標。native F9仍1；其餘五 browser／獨立專項未跑，整列車不標 READY-TO-MERGE。

本清單不含任何無關私人 GitHub profile。OWNER批准只沿 E c32 已公開的帳戶等同性 API 核實及管理代理接受條件，不外推真人手動輸入或本對話直接 B′ 回答，不改 P-189、性能、golden、assertion 或 timeout。

# 四份退役 WS 私有 index：只封存，尚未移除

固定範圍是 PLAN 中 R5、R6、L reading-A、F9 reader 四個退役 OWN checkout 的 `.git/index`。這是空間管理證據，不是產品 gate，也不將四個歷史來源改標成目前列車來源。

真封存外層與內層 exit 0；4 gzip 共 4,547,550 bytes，完整原始 index 共 23,386,440 bytes。獨立 actual 308 項核對通過：gzip 完整 bytes/SHA256／EOF／CRC、解壓原 bytes、48 條原 Git 命令與 1 條外層命令、12 份前中後快照、六次可讀程序檢查。四份原 index 仍以原 bytes/inode/mode/owner/times/xattrs 留原地，未 unlink，實際回收 0 bytes。23,400,448 bytes 只是日後可能釋放的實體配置量。

三個原 checkout clean；F9 reader 精確原三個 D 保留，沒有 reset、補檔或刪 dirty。程序檢查只涵蓋可讀欄位，未讀欄位照原 CONSUMERS.json 留存；不宣稱全系統程序均可見。原碼、fixtures、refs、objects、原收據都未移動或刪除。

## 發布後仍需另步驗證

所有 gzip、完整 Git/consumer/capture 原流、原 metadata、PLAN/request/tools、恢復方案與兩份 peer 都列入本清單。SHM 仍是暫存；本清單不是已遠端交付。root 必須一般 push，逐遠端 blob 下載核完整 bytes/SHA256/GitOID，再另授權精確四個 index 的移除；移除前重新核 effective private gitdir/common/index、HEAD/refs、完整 bytes/metadata、空 staged、原三 D、consumer/locks。不能由本次 archive peer 直接移除。

## 恢復依據

`archive-original/RESULT.json` 每一 archive 列完整目的地、原 SHA、mode/uid/gid/mtime/atime/ctime/inode/nlink/xattrs；`preparation/README.md` 列 no-clobber 恢復步驟。只在 index 不存在且 root 授權下取已驗遠端 gzip，完整解壓雜湊驗證後於同 .git 用 O_EXCL 新檔，恢復可還原 metadata，fsync，以不覆蓋方式原子建立 index。inode/ctime 不能重現，須記新值；Git 驗 HEAD／空 staged／精確原 status／refs 完成前不得解除 inactive 標記。原 source guard 為 25,165,824 bytes（24 MiB），不是 25 MiB，數值門檻未降低。

本次 actual reviewer 首輪將 outer EXECUTOR 誤當 archiver 而退出 1；INITIAL_REVIEW_ERROR 與 initial checker 保留，只修正 reviewer 身份判斷後通過，未改任何 subject 或重新封存。

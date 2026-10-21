# S3 公開來源與既有架構產物綁定

S3 `19401ca5448e162ee6140fed37b64b83b31ddec8` 的唯一父提交是 L2 `249571fe2477845d5330f6190dad965bf327f43b`，唯一變更為既有 `tests/test_geo261_host_authority.py` 突變錨點。候選分支為 `codex/geo261-host-authority-anchor-fix-20261021`；公開原件記錄普通 push 與 exact remote ref，這不是更新 PR #288 來源分支。

只讀綁定於 611 個原架構輸入與四 metadata 核 A2／L2／S3 同一 Git blob，並比對候選與仍固定 L2 的主工作樹原 bytes，以及 receipt 的 LF hash。四產物保持 A2 `cbefb39b47fb0edcfaf003d2c1101929fea244c8` 原 bytes，實際重產來源 sourceBaseHead 保留 S2 `cabe824128be31d0039dc6c94fa3f04cfb722a6b`。沒有在 S3 重產或重跑架構 CLI。

611 清單沿用原 receipt，並藉唯一 test 差異與三個完整 Git tree 驗證既有來源範圍不變；這不是重新執行架構掃描器。另存 expected JSON 及三個架構裁判檔案的相同 bytes 指紋。既有測試不在 611，仍觸發完整帳本及七項重跑，不能用本綁定代替。

所有 Git 命令的 argv、stdout／stderr／真碼與本次父 wait 都保存。工具觀察檔明示事後轉錄，不冒稱 raw transport；公開 ref 依本次 root publication 原件核對，本綁定沒有重新連網。方法原碼只以非執行的 `.txt` 保存。

L3 尚未建立，本包沒有 L3 成功收據，未執行帳本、產品測試、CLI、建置或推送。後續 L3 快照與驗收將另存新原件，不回寫此包。

`原件清單.json` 精確列出複製來源及 bytes/hash；除該索引、README 與 SHA256SUMS 三個產生檔外，檔集都在索引內。根 SHA256SUMS 覆蓋除自身外全部檔案。

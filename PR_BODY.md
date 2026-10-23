# #288：新 F 正式 grid 雲端驗收

正式 grid 已在獨立乾淨 checkout 的產品 F `3d681636902371ecc528b20f51eea33e272581c9` 完成，原 outer／workflow／browser exit 都是 0，耗時 473.79222212699824 秒，低於原 CI 15 分鐘。原完整指令、執行環境、退出碼、stdout／stderr、輸入與檔案 hash 都已封存；沒有改產品、測試斷言或原時限。

| 唯一 current state | SHA／原結果 | 範圍與限制 |
|---|---|---|
| 受驗產品 SHA | `3d681636902371ecc528b20f51eea33e272581c9` | 前後 HEAD 均為 F，checkout clean；16 個明列輸入前後 bytes／Git mode/blob 一致，此窄清單不替代 root 完整 closure |
| 證據 head | `b12172860c59fe091c0e490630b548281b2eb53a` | 本分支只在 `evidence/geo288-final-3d681636/` 保存收據；沒有在證據提交重新執行產品 |
| 正式 grid | outer／workflow／browser `0/0/0` | status完成，overCI=false、watchdog=false，原 build exit0 |
| 原 partial 結果 | 356 pass／0 fail／skip=[] | `GEOMETRY_GRID_SYSTEM_ONLY`；P70=121、P71=9、P78=23、P87=60、P88=143 |
| 原 golden／例外 | `not compared (partial mode)`／0 | 依原 footer 保存；沒有聲稱此 partial 比較完整 golden |
| 原 scope／資源隔離 | 19784／9634，獨立 TMP／profile | 完整沿原 workflow 的 grid 步驟；原 R3 鎖、16MiB stack 和 cleanup 保留 |
| 本地獨立 peer | 114 項 metadata 核對完成 | 原件核對不代替產品 exit；公開 Git 封包對抗審另由 P88 owner 完成 |
| 其他 #288 gates | 由 root 各項原收據判定 | 此正文只記本 grid job，沒有外推整個 #288 可合併 |

環境原輸出為 Google Chrome 156.0.8078.47、Node v24.19.0、Python 3.12.14，fonts-noto-cjk 已實際查得 installed；各版本命令 exit0 的完整輸出在原 versions/。工作全在雲端完成。

[原 grid 收據](https://github.com/ZhiQiYang/geometry-axiom/blob/b12172860c59fe091c0e490630b548281b2eb53a/evidence/geo288-final-3d681636/receipts/grid-final.json)、[進度與原封包索引](https://github.com/ZhiQiYang/geometry-axiom/blob/b12172860c59fe091c0e490630b548281b2eb53a/evidence/geo288-final-3d681636/PROGRESS.md)。原 node stdout SHA256 `e61179f88dad670839b183aee83fe02c89c8d22fe34bc19d353a1191f4599223`，原 receipt SHA256 `db8d3b1d49a1a86973e59e5deef58c7c4dd60f6c9358c6f5f55f3692bffd04b6`。

原通用 publisher 在加入證據路徑時被 .gitignore 擋住，exit1 完整保存在同一 E 的 `publication-original-attempt/`。只對已授權的本證據前綴做 `git add --force --sparse` 後一般 commit／push 成功；沒有改 .gitignore、沒有 force push，也沒有重跑 grid 挑結果。

最主要限制是本 job 的原 partial 範圍與未比較完整 golden；正式完整 canvas、P88 撤回／恢復及其他 gates 各有其獨立原件。這份 PR_BODY.md 只推到本分支的 -prbody，不宣稱已更新 live PR，也不合併 PR。

# F9 documents／grid／space／timber 完整原件

固定來源 `4f8a794f4167c3562eb182045102e86e9e37cca9`，四項各依原workflow、各自source／gitdir／port／TMP。下表出口依序為原workflow／wrapper／CI gate；時間上限為原值，沒有新增skip、改golden或放寬判定。

| Job | 原出口 | 通過／失敗assertions | 秒數／原上限秒 |
|---|---|---|---|
| documents | 0/0/0 | 47／0 | 63.197160／600 |
| grid | 0/0/0 | 356／0 | 464.984065／900 |
| space | 0/0/0 | 242／0 | 209.339005／900 |
| timber | 0/0/0 | 79／0 | 124.531604／1200 |

grid 是原 `GEOMETRY_GRID_SYSTEM_ONLY` job（356 assertions，原 partial-mode 不比較 full-canvas golden）；timber 是原 `GEOMETRY_TIMBER_ONLY` job（79 assertions），不冒完整space suite。space 的原 full-space suite為242 assertions；documents為47。原具體scope、各組完整性、診斷、截圖與完整取樣均在包中及各job獨審。

九包共31,278,535 B，保留2411 regular files／125,944,310原bytes及8 symlink targets。`package/INVENTORY.json`、`PARTS.json`逐一記錄原指令、完整stdout／stderr、環境、SHA、檔案hash/stat與分包位置；所有ELF／cache／profile／screens／診斷均收。20個sourceplan Git metadata／mutable latest葉作hash-only，2個Unix socket只記metadata；原件未刪，seed/source payload未複製。包內上千原葉沒有再逐一入Git。

`collection-original/`為原c387收件argv／exit／全流，`collection-EXEC_FINAL.json`為主機真exit0。`package-actual-peer/`的17156／0包含全members、原sourcehash/stat、mode／mtime／links與9個gzip EOF／CRC；它不代產品gate。`job-actual-peers/`保存各job獨審及其原checker，包括timber reviewer初版修正說明。

`collector-preparation/`保留原稿及精確v3差分；`terminal-bindings/`保留12份原host／plan／materialize身分綁定。首次metadata binder因yielded host封裝出現KeyError而exit1，記錄仍在；只修收件工具對真host封裝的解析，沒有重跑產品或改原FINAL。

這份清單只新增本prefix，不寫PROGRESS或PR正文。主代理將與其他證據合成唯一current-state矩陣。native原exit1仍保留；#314當次outer1／indexguard未因本包變綠，其新修補尚無本包驗收結論。也不代P52／P189／其餘專項，不標READY。

SHM是揮發性。原RESULT的delivered=false保留當時原值；正常push後還須GitHub API逐blob下載完整raw並核bytes／SHA256／GitOID，實際出版收據另列。此README與collector0均不能替代遠端驗證。

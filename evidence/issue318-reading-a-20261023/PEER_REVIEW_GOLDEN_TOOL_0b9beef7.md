# #318 targeted golden proof 工具：0b9beef7 靜態補審

被審不可變檔案：`0b9beef7bcebef2352657b4ae00a6a25dbc88f2e:evidence/issue318-reading-a-20261023/tools/prove_golden_witness.py`。只讀 Git blob；沒有啟動工具或任何 oracle build。發布身份由 owner 另外核對，本審讀不把 local object 稱為 remote 已推。

前輪草稿提出的收據範圍已補：四個實際輸入（oracle／generator／rooms／golden）都在各 variant 隔離，保留 source hashes 與末 bytes/hash、HEAD/status；正向 baseline/restored必有 CHILD 最後 PASS marker，撤回必正常exit1且 marker 來自原 generator非空assert的 traceback最後一frame／精確line。語法錯、import失敗、其他assert或timeout不符合這個marker，不可冒kill。

只替換一次 FZ120 witness常數成原STEP20幾何，原非空assert不動。三個 EXTRA房及 witness各八排法，故每variant約32build；`rooms={}`是明列的targeted scope，沒有稱完整64房排法或完整selftest。正向也逐欄比新golden witness、精確I22 tuple、矩形綁定和建構id≠排序index。

工具內持R3非阻塞排他鎖；忙時75且沒有child，不能標允許skip。三個child環境強制PYTHONOPTIMIZE=0並由CHILD再拒optimize，PATH/PYTHONPATH/PYTHONOPTIMIZE等相關環境已記錄。三階段順序收齊、不自動重試，不寫repository golden或ledger。固定45s僅為這個targeted程序的timeout分類，不把timeout當正常失敗反證。

未見補完後確立的新靜態阻擋。正式執行仍需保存原工具／source／輸出及核對每variant實際hash，期待0/1/0；這份報告不提供任何動態綠燈，也不關閉完整generator/selftest/64排法、掃描、native、reader或CLI次序未驗項。

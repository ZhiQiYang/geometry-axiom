# #314 獨立分支：單檔來源控制 anchor 維護

本輪產品／測試來源 S：`3b0b634feb54266700cc61f26c34d7aeac4c0314`，已一般push且ls-remote同一SHA。本輪沒有動態驗收，exit=null；本目錄是後續證據出版，不冒作S的測試執行。

root協調後，#318 owner明確確認停止編輯 `tests/test_geo261_wood_grid_application.py`，暫交此單檔給#314；其他shared/source仍屬#318。本輪完成後交回。來源是已獨立靜審的#318維護提交 `1cd2fc216299041a557654a874509a33884af819`，只挑其測試leaf，不帶#318其他產品、tests或expected修改。

新提交相對原#314證據head `25c15f7b81de07d3c9c66a5553bf9bb43aa8f3fb` **只改一檔一行**：legacy-value控制的old pattern由舊2參數呼叫改成真產品現有的6參數完整呼叫，與M102一致；replacement仍`if(0)`。原方法、stagger-w06、具名marker、stagger_control、所有斷言及23個方法不變，expected沒有改。產品C/H/JS、registry／M121、canonical、架構四檔及保護文字均沒有因本維護而改動。

## 原始 Git 操作結果

標準 `git cherry-pick --no-commit -x 1cd2...` 也帶入原commit的兩份#318 evidence，與本分支沒有該檔的狀態產生metadata衝突；原cherry-pick exit1保留。初次git restore拒絕unmerged PROGRESS，該原exit1與完整輸出亦保留，沒有改判。

完成階段先驗兩份incoming evidence在本身原HEAD不存在，只移除此兩份incoming metadata以解決排除，再驗stage僅有指定leaf、整檔bytes恰為一次指定字串替換、方法不變、diff-check0，正常commit。commit／普通push／ls-remote皆原exit0，remote完整head等S，工作樹clean。此為Git維護流程，不是產品／測試紅燈或語義反證。

原第一階段完整command／stdout／stderr／環境／SHA在 `original-attempt/`；完成階段在 `completion/`，並以原receipt hash引用第一階段。`review-318-anchor/REVIEW.json`是原#318提交的獨立靜審原件，保其真來源，不改標成S實跑。

## 尚未跑

- 本維護fix的原具名方法與真source-control baseline／withdrawn／restored尚未執行，沒有宣稱0／1／0已取得。
- 新M121、#314完整47方法／ordered facts／route、reader、native／6browser、ASM、架構三裁判與全帳本仍未在新S執行。
- 改tests/*.py後舊bridge oracle／帳本不可冒作新鮮；root最後統一整份帳本。既有#314四檔bundle仍明確stale，待最終合流重產；不因本維護聲稱架構已通過。

舊 feature／registry來源 `8033aa756c62f654333c24d1276d4b61beb31a45` 與證據 `25c15f7b...` 留歷史角色；舊cc67原驗收也仍綁舊SHA。source已交後棒的共用修改不回混進本分支。本次單leaf請combined在下一輪普通merge納入；不force push、不合併PR、不改integration。

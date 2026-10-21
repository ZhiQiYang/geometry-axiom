# L3五項瀏覽器獨立唯讀審查

來源為 `6589248c9a94bdf0460d8f84dd1610e51048188b`，分支 `codex/geo261-closeout-20261021`。本審查沒有啟動browser、build、產品測試或新突變，也沒有修改原run目錄。

主接受器 [peer-code-v2.txt](peer-code-v2.txt) 真wait為0，工具732ee4為0；補件接受器 [artifact-peer-code.txt](artifact-peer-code.txt) 真wait為0，工具2e140b為0。完整原stdout/stderr、argv與父wait見 [execution-v2.json](execution-v2.json) 及 [artifact-execution.json](artifact-execution.json)。結論分別在 [peer.json](peer.json) 和 [artifact-peer.json](artifact-peer.json)。

五項原Node均為0：assembly150、documents47、grid350、space242、timber79，合計868個斷言。assembly/grid是原partial scope，另核指定段golden；documents核凍結來源全部47個具名PASS的次序；space與timber各依原scope和固定census核對，不稱五項都是full canvas。原wrapper、launcher process及已保存工具回覆均為0；工具session85316的final chunk為b9d980。五個原job各在從npm build前計起的原期限內完成，依序執行，沒有延長期限。

獨立核154個browser來源與194個native依賴，聯集348個不同Git路徑，均與L3原blob相符。三支binary在這輪是reused；依當輪保存的sidecar、source與runtime前後收據核身分，沒有用後續live runtime回推執行時點，也不稱當輪重新編譯。來源前後clean且未變，runtime前後相同fresh，ownedcleanup無live/zombie殘留且兩port拒絕連線。

原manifest210件／81張PNG已核bytes/hash與PNG完整chunk CRC及尺寸，未逐張目視UI。assembly具名lost-success-response控制保留，不能因驗收成功宣稱沒有transport失敗。沒有新增突變自證，這次只核正式原結果及原控制。

補件24個原件全部逐bytes/hash/mtime核對：15個新增檔共107195bytes（7個raw宣告grid下載、5個相鄰JSON、documents的Markdown/PDF/notes JSON三個輸入），另9件已在原wrapper產物內，不重複copy。補件使用原job秒級mtime窗[start,finish+1s)，是job完成後封存，不算入原job期限。原suite manifest未改。

首版主接受器為1，原因是把P77控制誤定位到assembly_workflow_test.js；v2僅修成實際assembly_review_test.js並保留同樣具名條件，最小差分及首版完整輸出仍在本目錄。這是審查接受器錯誤，不是產品失敗。兩次資料探索錯誤只保有真工具碼與摘要，當時未另存完整stdout/stderr；[tool-observations.json](tool-observations.json)明列範圍，沒有補造raw。原L43接受器只曾inline執行，未另存碼；本輪依原報告條件新寫並保存方法，沒有宣稱逐byte移植舊碼。

最不確定的是未逐圖目視及本機Chromium與CI Chrome環境差異；本結果不替代native、Q38、§7或P189。製作者最後報告的核心數值亦與本獨審相符，見 [producer-final-comparison.json](producer-final-comparison.json)。

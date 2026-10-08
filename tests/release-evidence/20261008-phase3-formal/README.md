# Windows 正式入口的保存與重開

這包是草稿 PR #173 上的第三階段。產品提交仍是 `d44ad7fea531a94f67401d5b403565cd891770ae`。本目錄是事後收錄，不改 `geometry-web/app.js`。

它不是 PR #170 的格線輪。不要把這裡的 32 與 316、328、346 相加。也不是歷史 10/155 原稿。A/B/C 的 16/35/33 只按 PR #162 的來源範圍引用，這輪沒有重跑。

Headless Chrome 沒有可用的系統儲存對話框。`qa_cdp.js` 在每次文件載入前拿掉 `showSaveFilePicker`，所以保存走產品的下載備援。下載成功時 `downloaded` 為 true，`dirty` 仍是 true。這不是作業系統已寫入磁碟的那條路。

## 身分

見 `binding.json`。工作樹乾淨，HEAD `d44ad7fea531a94f67401d5b403565cd891770ae`。服務 `http://127.0.0.1:8915/`，runtime `f2804c8068805409ccc06cddea3fac6219f768706f9276e981948f1142a286b2`，fresh，pid 30184，session `10ecae1110974672866960d3c31047ab`。CDP 9516。bridge 沒有重編。既有 model-base 也沒有重編；缺少它的那一輪另記在下面，不能改標成這一輪。

## 最終一輪

`logs/final-round.log`。`PHASE3_SUMMARY {"passed":32,"failed":1}`，`NODE_EXIT 1`。逐項在 `results.json`，沒有把失敗項改成通過。

通過的項目核對的是 dump、來源、配置、主格引用、模型 id、來源摘要、組構讀回與專案 id，不只看畫面出現。

- 網格：命令建立 1200×800 面。來源預覽與配置預覽、套用預覽都還沒寫入世界。建立無限來源「假格網甲」，u repeat 0 200、v repeat 0 100。配置 id 1，boundary 1，system 1，vertexKey 1，cell 0,0。套用後主格 id 1，surface 1，bindingId 1，sourceSystem 1。
- 關閉網格工作區後，復原拿掉主格並留下配置。重做回到同一 dump、來源、配置與主格。
- 下載 `projects/grid-save.gcanvas`，867 bytes，SHA-256 `a34cb207ad1106762097bd3e42c04390939a3cb6b885bfd8ad5f580ff8c3ae3d`。新專案清空面與格網。再開這個檔，dump 與專案 id `d8d7b530-8cc9-4f1f-bd20-fd07cc2bea91` 相同。
- 390×844：保存控制 44×44，點得到，`scrollWidth` 不大於 391。語意快照不因縮放改變。畫面 `shots/grid-reopen-390.png`。
- 模型庫：矩形範例預覽不改網格世界。體積與淨空 `36000000000`，封閉，6 面，牆體積 `4320000000`。建立模型 `d8567423-c913-4f90-bc72-2de7edd12aaf`，來源摘要 `4669f32c993154b7ed7a830274c03c8a235f16b1217f2f47218fe9b4c1e2cdd6`，原生場景仍是網格 dump。刪除不改場景。復原恢復同一模型與摘要，重做再移除，保存前再復原一次。檔案 `projects/model-save.gcanvas`，37293 bytes，SHA-256 `49e05ad13914e62de974072abf7e904018e13c91052d7718404aa53b13b11edb`。新專案清空模型。再開後場景、模型 id 與來源摘要都在。
- 組構：正式檔案選擇器開啟 `geometry-web/examples/assembly-generation-v1.gcanvas`，1 條規則、1 個綁定、1 個實例。把截面改成 40 與 50。預覽不改已發布狀態。確認後三支角材都是 `40x50`。關閉工作區後復原回到改前實例，重做恢復 40×50 與 dump。`projects/assembly-save.gcanvas`，4287 bytes，SHA-256 `681ab22ba8e6ccd3a513f1b1625a13e4c30a011031a0945539f7eaebce15eabc`。重開保留組構讀回、dump 與專案 id `assembly-generation-v1`。
- 注入 `AbortError` 的保存取消、注入的寫入失敗，以及 14 bytes 的 `projects/corrupt.gcanvas`（內容 `not a zip file`），都沒有改掉當時的組構專案。壞檔狀態是「未能完成開啟專案：專案缺少清單或場景。」寫入失敗留下 `window.__phase3Aborted`，忙碌狀態是 false。

## 唯一失敗項

`復原新專案回到含模型的原專案` 比較了整個專案物件，所以結束碼是 1。隨後的 `phase3-undo.js` 對同一個 `model-save.gcanvas` 再做一次，`NODE_EXIT 0`。`logs/undo-followup.log` 只有三行，沒有重記 runtime 或 CDP port。`undo-new-project.json` 寫明：dump、專案 id、名稱、saved、downloaded、模型 id 與來源摘要、復原堆疊長度、標籤都相同。不同的是 `dirty` 從 false 變成 true，`redo` 從 0 變成 1。標籤在復原後回到「開啟專案「未命名專案」」。

這是既有行為。`project-store.js` 的 `snapshot()` 保留 context 參考，不複製 dirty、saved、downloaded。`reference-workspace.js` 的 `observe()` 對成功、非預覽、且不是 `line history-` / `preview` / `cancel-preview` 的 `line ` 指令呼叫 `dirty()`。`line undo` 會走到這裡，於是復原本身把 dirty 設為 true，並把 downloaded 清成 false。公理沒有定義這個旗標。幾何、來源引用、模型清單都還在，所以這輪不改產品。

## 先前中止，不能改標成最終輪

這些是 harness 或服務環境，不是最終輪的產品結論。原始堆疊含本機使用者路徑，不進 git。

- `URL is not a constructor`。`const URL` 蓋到建構子。`NODE_EXIT 1`。Chrome 還沒做產品斷言。
- 未知按鍵 Home。通過 4、失敗 3。`NODE_EXIT 1`。後來改用 Home 的虛擬鍵 36。
- 網格工作區還開著時，畫布 `#btnUndo` 的中心是 HEADER。`#btnNewAssembly` 在尚未打開的建立選單裡。通過 9、失敗 3。`NODE_EXIT 1`。
- 下載檔有 867 bytes，但門檻當時寫成大於 1000，SHA-256 `0fc26239dbb73346db67c0ec901062b27d49dd70c0dfa021d81cf7afd200761d`。那個 zip 不是本包的 `grid-save.gcanvas`。`#btnSpaceModelTrial` 不可見。組構工作區蓋住 `#btnUndo`。通過 18、失敗 3。`NODE_EXIT 1`。
- pid 30544，session `232819b6b6b64e3aa65384eba44d65b6`，同一 HEAD 與同一 runtime，但沒有掛 model-base。`#smPreview` 等到逾時。通過 21、失敗 2。`NODE_EXIT 1`。`shots/model-failed.png` 畫面是「讀取來源中」與「空間建模服務尚未就緒，請保存專案並重新啟動應用。」這支服務隨後換成 pid 30184，掛上既有的 model-base，沒有新編未簽章 exe。

`shots/model-failed.png` 是沒有掛 model-base 的那一輪。`shots/assembly-failed.png` 是更早的 harness 中止。`shots/grid-failed.png` 與 `shots/grid-applied-1440.png` 位元組相同，SHA-256 `be2c9cd42a27dbbaa5c388b89d61c72bc9c0c50d3beb4a0ee93faa397d546c99`，所以它不是另一張失敗畫面。

## 未驗

原生作業系統儲存對話框、實體滑鼠、IME、真實裝置、託管 CI、完整主 UI 與 golden。真實磁碟已滿沒有測，寫入失敗是注入的 picker。第二階段仍未驗的路徑（面內成功套用、三視圖晚回覆、390 格網工作區焦點、空間投影、刪除後的晚回覆、模型更新標題、面內格網預覽）這包沒有補跑。

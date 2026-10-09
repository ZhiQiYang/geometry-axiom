# P75 之後的既有部分模式

這四輪接在 P75 後面，一次只開一個瀏覽器。每一輪只設一個 `GEOMETRY_*_ONLY=1`。模式都是 partial。golden 都沒有比對。產品檔沒有改。HEAD 都是 `7dfda00df6da60baae4e9a5c846e8feae3b2885c`。app.js 仍是 `a0545004a061402b645f785bbc883d60137b417399f9c46c5d0323dc7f2297d2`。runtime 都是 `9db2394ed4b390e6a99b125fff34fda2fcf6e5cf534daeef6a6b600abbdce490`，fresh。model-base 仍是私有 fresh `2c0258cdf75f141a1eea5fd5355d7e3347e2a9e9e47512d7ad1ccf408a57e56c`。bridge 沒有重編。port 8915 沒有停。

每一輪的 `NODE_EXIT 0` 都是該輪 `node` 的 `$LASTEXITCODE`。`completed:true`，失敗 0，瀏覽器例外 0。下面的通過數各自獨立，不互相加總，也不和 37、52、1692 相加。

| 範圍 | 服務 pid | session | port | CDP | browser | 結果 |
| --- | --- | --- | --- | --- | --- | --- |
| `GEOMETRY_PARAMETERS_ONLY` | 31728 | `9c35496153524cfcb8478666689b0243` | 8943 | 9543 | 13276 | P76 87 |
| `GEOMETRY_ASSEMBLY_ONLY` | 38740 | `809f98a3ea6d480a8a55bbaf6fbe13e8` | 8944 | 9544 | 43240 | P77 134、P82 16 |
| `GEOMETRY_TIMBER_SCHEDULE_ONLY` | 27644 | `516e9a4ac68c40fba8dc92c68150561d` | 8945 | 9545 | 27860 | P80 23、P81 14、P85 31 |
| `GEOMETRY_ROOM_OUTLINE_ONLY` | 40384 | `3cbdd68b51f2406caf7a8a4639da8934` | 8946 | 9546 | 25952 | P79 87、P84 33 |

房間輪的結果裡出現 P84，是這個既有 flag 實際跑到的段落，不是另開的一套。

## 未驗

模型快照兩支外掛只在完整模式執行，這次沒有重跑完整主介面。golden 逐段相符、實體手機、人工 IME、真實裝置、託管 CI、原生作業系統儲存對話框仍未驗。第 5 段拖卡片仍是先前完整主介面的失敗，這次沒有重跑，也沒有改產品。

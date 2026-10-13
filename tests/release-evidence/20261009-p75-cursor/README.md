# P75 部分模式

這一輪只設 `GEOMETRY_SELECTION_CURSOR_ONLY=1`。模式是 partial。golden 沒有比對。通過 37、失敗 0。不要把 37 和 52、1692 或其他輪的通過數相加。

產品檔沒有改。HEAD 是 `1101e730b1b120c9d65b8a33329bb6698e529c0e`。app.js 仍是 `a0545004a061402b645f785bbc883d60137b417399f9c46c5d0323dc7f2297d2`。`cdp_test.js` SHA-256 `31fdf17c0a0e0c3f534504fe4cdfd9f30dfa16bdd4a91f1cda30ce85a7387687`。runtime `9db2394ed4b390e6a99b125fff34fda2fcf6e5cf534daeef6a6b600abbdce490`，fresh，服務 pid 38792，session `5de08f22f2344b248eac989f60e95dc3`，port 8942。CDP 9542，browser pid 23668。

`NODE_EXIT 0`。`completed:true`。`sections` 只有 P75:37。同一支 fresh model-base `2c0258cdf75f141a1eea5fd5355d7e3347e2a9e9e47512d7ad1ccf408a57e56c`，bridge 沒有重編。port 8915 沒有停。

這一段在完整主介面裡原先沒跑到，因為那輪停在 P74。這裡沒有重跑 P74 或完整主介面。

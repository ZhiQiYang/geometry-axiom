# H7 可讀原件（不是新測試）

以下檔案直接抽自固定 E `06b81e452c9d80c210cbf10fe2f5da8eebfc31e5` 的 `placed-h7-256747c5/RAW.tar.gz`，再與保留原檔逐byte核對。未重新序列化JSON、未改輸出、未重跑測試；execution仍 `256747c5c8f8f8934eeb08ae404dee1f67591508`，採入產品仍 `7a0e6dd81c54066995981393925fa46a815de2f8`。

原archive SHA256：`2a6798f772c50f88dc1fb4a10b51514ff767ab6144879a013dec7710bc797302`。

| 可讀原件／封包成員 | bytes | SHA256 |
|---|---:|---|
| [h7/REQUEST.json](h7/REQUEST.json) | 1052 | `784408f4c193d2e78bff79aa210a2e16dcb5f103c213ac8c9f220f7c1c6bc250` |
| [h7/RESULT.json](h7/RESULT.json) | 35950 | `1b3259b72305a1d96ad12a69b244869b0c1254a3f4408cf7fd6cb3f9100bb65b` |
| [h7/unittest.log](h7/unittest.log) | 1695 | `cb3143f9aba291bb94320ca9bc250c2d741ad56ae70c2a466aece307ac8e783e` |
| [h7-wrapper/REQUEST.json](h7-wrapper/REQUEST.json) | 1283 | `900be60170698c11a16d174a5f43bf9adb14b19be0723a41044d6ec511de1e5c` |
| [h7-wrapper/RESULT.json](h7-wrapper/RESULT.json) | 1412 | `4a629b806029425a426009f9ffc8779d315aac36e5067427e78f7f623ea5612e` |
| [h7-wrapper/outer.log](h7-wrapper/outer.log) | 26734 | `d4784a274a2641da529d365c5e932c6e7794c577c86476f41e9e241d8402f510` |

`h7/unittest.log` 是原八方法逐項摘要；inner RESULT 記8/0/0/0與九批結果，wrapper RESULT 記外層exit0／1142.2716743946075秒／未timeout。這次文字公開不增加新的驗收，也不代表整體native或browser完成。

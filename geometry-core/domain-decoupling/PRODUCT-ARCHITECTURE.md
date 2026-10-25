# Product architecture — integration train fixed-source receipt

產品／裁判實際來源 `9aec9a32630fc65f94c53d49e99969e546574d6e`。三條原命令 exit 0／0／0；generic 205、product 18，零 skip。完整604 inputs、334 owned／270 exclusions、798 edges／0 diagnostics。LF closure `71caf2df36a51b86da3d0553abd7ccebb7542d9dce2ec3f065e8d90a16ebbe0f`。來源 HEAD、604個Git blob／raw／LF、三個裁判及兩份 SSOT 前後不變。

本輪 manifest 唯一變更為 `geometry-web/cdp_test.js` 排除項LF雜湊 `bb66742aa10b603b84362277f9f2c4275da8904925e75c618f252bd7df42cc3e` → `1f3e2e36283ed7bbf6c4ad2cf3dc12c685667356d186d9fbd47bc5f0520f07ee`；其餘原bytes、forbiddenIdentifiers 937、forbiddenStrings 55、分類與全部政策不變。完整604輸入相較前份收據精確只有 `['geometry-web/app.js', 'geometry-web/cdp_test.js']` 變更，其餘602 Git blob相同。唯一hash撤回／恢復真0／1／0，撤回只得 `EXCLUSION_DIGEST`。

原完整W lexer盤點仍覆蓋全部W identifiers。九組既有guard在本次來源真0／1／0、兩neutral綠；歷史928 Git `ca7838e0f4950452b9befcf40899d606db9b81fa` 的原raw `80f44b8c870e097413e395d30ba029199ba66b7302985c0f325d4f446d0ce525` 原樣保留，實際撤回用另存衍生副本 `2661beb6a5223d2aeecd64d708194261d97f0a738c1fc3adb22ff431c07bbbb8`，只同步同一cdp排除hash，避免遮住W guard。衍生副本不是原歷史bytes，沒有移標歷史判決。

前份收據 source `e321026fb9bc9bc19c54b8034af6e6eaec2857f9`，產物提交 `6df0264f75e84f03adb70746b6ac3db07a9910fc`；本次完整輸入差異在 receipt／source-inputs.json，歷史報告保於該Git提交。四檔寫至來源外，receipt不hash自己。原native／browser／mutation ledger／效能需各自原收據，本四檔不代稱它們通過。

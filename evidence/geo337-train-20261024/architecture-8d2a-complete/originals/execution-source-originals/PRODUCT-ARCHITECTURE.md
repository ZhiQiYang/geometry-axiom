# Product architecture — integration train fixed-source receipt

產品／裁判實際來源 `b9c9fb818f031828530994a4d66f1976da0d8138`。三條原命令 exit 0／0／0；generic 205、product 18，零 skip。完整604 inputs、334 owned／270 exclusions、798 edges／0 diagnostics。LF closure `2373af45191d585e9f5b1652935e7802a9d154075d7d2de07a8ede37baa91773`。來源 HEAD、604個Git blob／raw／LF、三個裁判及兩份 SSOT 前後不變。

原完整 W lexer 盤點補9個已存在的 Reading A identifiers：forbiddenIdentifiers 928→937，forbiddenStrings維持55；舊guard全留，其餘manifest分類、路徑、exclusion、trust及政策全部相同。九組原scanner guard assertion在同一來源各0／1／0，兩個neutral probe通過；沒有用舊來源結果移標。

前份收據 source `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599`，產物提交 `38da31bcac91db631e6325e40b228f8604810e82`；本次完整輸入差異在 receipt／source-inputs.json，歷史報告保於該Git提交。四檔寫至來源外，receipt不hash自己。原native／browser／mutation ledger／效能需各自原收據，本四檔不代稱它們通過。

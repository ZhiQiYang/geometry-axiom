# 102ff 完整 CDP 原始 P76 失敗

實際完整受測 SHA `102ff28ecb005a85b42a8ae9cd7f22fdcf8cf01c`，before／after clean。既有unfiltered fullCDP已終端：1800通過／1失敗／0略過，actual exit1、completed:false，golden未比。1800個成功斷言不代表完整驗收通過。

P32 active-v3 host、P64原R→V／Escape與P75正式canonical37個原checks已於同full前段完成；這些前段不是另一份full通過。唯一P76失敗為390px parameter sheet高度523、canvas高度137，canvas低於原bounds門檻。P76實際54通過／1失敗，原預期87；P77／P82／P80／P81／P85／P79／P84／P83／P86未到；原bounds、全部後段、golden／floor保持，不放寬以取得通過。這是ROOT下一產品候選要修的版面問題，非外部阻塞；另已保留caption／正常Tab navclip27／1和唯讀診斷27／1，各自獨立、不相加。

原command-failed wrapper receipt、executionVerified:false、canonicalResult:null保持原樣。`executor-failure-index.json`只補充從已封原raw解析的terminal結果、部分census、source／實際執行檔證據，沒有回寫receipt。完整原raw、actualNode／Chromium ELF／owned native、clean完整SHA、wrapper／launch adapters／harness／golden bytes snapshots及精確owned-stop都收錄；收據／log／source原hash与公共路徑projection hash分開。公共副本沒有執行，synthetic World／result值與trace binary resources保原；私有feedback／profile／queueDB、native binary bytes及大張單獨截圖不公開。

原raw SHA `fd885211916b080bed5cf3c86573017dc8da62e57711b6d286ec3506dfb1ae6c`，receipt SHA `87242c6e76cc75a305b43c0df4502af86f49897d3ebb09e1d10299b76e1f1f29`，failure index SHA `2bc069766e33bb65a0db8a4e2c6746ec91d376af042743c269d8aebac1e755da`，owned-stop SHA `4fa84520d7a77bac33a7a540a96067ffe39e21de90aee2465658ea2c8d4ef83a`。附加independent census或來源checks是證據核對，不增加產品通過數。

下一乾淨候選需保原P76 bounds／正常keyboard目標及必要full驗收；不使用force、弱化斷言或无限重試。原2431713／6、0b37 506／4、cb8 1383／0但exit1 false等完整失敗保持各受測SHA與原件。歷史complete CDP2207／0／0只綁 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；Windows1692／2 exit1 false、七原件雲端未核收與golden未知亦保原。之後文件發布HEAD不改綁本實跑。

真正獨立readonly census actor另核原fullSHA／clean／source／actualELF／native與原raw，immutable review SHA `2b3808388ac1b20ca75cbbf997a3ac154b4e12747fdb17abce3feb3b544df53d`，不是executor副本。其resultIntegrity與actualObservedIdentity核對不代表full／golden acceptance；原fatal payload未提供uncaughtBrowserExceptions欄，維持unknown，不能補0。P76 proposal仍未執行，不當驗收。

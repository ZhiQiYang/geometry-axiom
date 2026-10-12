# PR #194 M3：歷史 driver 原件界線

依審查允許的限縮方式，原 README、正文與完成回覆的「外層 driver 紅燈原件已保留」聲明更正為：**已交付首次 parent `-S` partial 的子程序 stdout／stderr、receipt及suite logs；沒有交付當時外層 driver 的原 stdout／stderr、實際退出碼及原文，無法獨立核那筆歷史外層紅燈。** 不用後續 venv driver 或重跑代替历史。

該子程序的原 receipt 是actual exit0，suite JSON為21 pass／0 fail、error、skip；它沒有證明外層退出碼。這次也不是無套件證據，因child未繼承parent的 `-S`。後續真無cryptography venv局部aggregate的14pass＋7skip、exit3→0及M23的ERROR→指定FAIL→restorePASS，仍只承接已交付有效原件的既定範圍。

只改原包 README一句與其manifest條目。原75 payload中74份 bytes／hash全同，42份raw原件及所有receipt／script、21份來源綁定不變；原文件的舊字句與舊hash可由 `ee8dd5c` Git原文核查。本輪 `audit.py` 只唯讀核manifest、子程序計數和文字界線，actual exit0；不是產品測試或mutant，不重跑歷史、不補造外層traceback或退出碼。

产品、C／核心帳本、SSOT／白話／正典／🔒、原測試、runner、expected及安全策略全不變，未跑新的101／49／正式七job。B1根信任／iOS／完整安全承接及批准、B2正式最終SHA七job／真bridge多端界線保留；未排WSL全量。

@echo off
rem 測試 exe 必須編進 geometry-web\:Device Guard(Smart App Control)
rem 企業原則 {0283ac0f-...} 只放行本目錄的新編未簽章 exe;
rem 編到 knowledgebase 根目錄會被擋(WinError 4551)。
rem 用法:python tests\run_tests.py geometry-web\cg_new.exe
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /utf-8 /O2 /W3 /U_WIN32 /Fe:D:\knowledgebase\geometry\geometry-web\cg_new.exe D:\knowledgebase\geometry\current_geometry.c

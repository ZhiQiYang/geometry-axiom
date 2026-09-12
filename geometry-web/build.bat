@echo off
rem /U_WIN32: geometry layer only; the GDI window section is skipped entirely.
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /utf-8 /O2 /W3 /U_WIN32 /Fe:web_bridge.exe web_bridge.c

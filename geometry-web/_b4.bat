@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /utf-8 /O2 /W3 ..\current_geometry.c /Fe:cg2.exe

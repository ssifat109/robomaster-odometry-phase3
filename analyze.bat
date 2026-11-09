@echo off
setlocal
cd /d "%~dp0"
wsl.exe -d Ubuntu-24.04 -- bash -lc "cd '/mnt/d/robomaster 3' && python3 code/analyze.py"
set "RC=%errorlevel%"
pause
exit /b %RC%

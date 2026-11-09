@echo off
setlocal
cd /d "%~dp0"
wsl.exe -d Ubuntu-24.04 -- bash -lc "source ~/rm_venv/bin/activate && cd '/mnt/d/robomaster 3' && python code/phase3.py preflight"
set "RC=%errorlevel%"
echo.
echo Preflight exit code: %RC%. See results\preflight.json and results\preflight_latest.jpg.
pause
exit /b %RC%

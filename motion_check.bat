@echo off
setlocal
cd /d "%~dp0"
wsl.exe -d Ubuntu-24.04 -- bash -lc "source ~/rm_venv/bin/activate && cd '/mnt/d/robomaster 3' && python -u code/motion_check.py"
set "RC=%errorlevel%"
echo Motion check exit code: %RC%. Inspect results\motion_check.json.
pause
exit /b %RC%

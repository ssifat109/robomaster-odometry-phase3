@echo off
setlocal
cd /d "%~dp0"
wsl.exe -d Ubuntu-24.04 -- bash -lc "source ~/rm_venv/bin/activate && cd '/mnt/d/robomaster 3' && python code/make_report_graphs.py && python code/make_report.py"
set "RC=%errorlevel%"
echo Report build exit code: %RC%.
pause
exit /b %RC%

@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: trial.bat N ^(N = 1 through 10^)
  exit /b 2
)
wsl.exe -d Ubuntu-24.04 -- bash -lc "source ~/rm_venv/bin/activate && cd '/mnt/d/robomaster 3' && python code/phase3.py trial --trial %~1"
set "RC=%errorlevel%"
echo.
echo Trial exit code: %RC%. Inspect results before resetting the robot.
pause
exit /b %RC%

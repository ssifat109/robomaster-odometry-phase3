@echo off
cd /d "%~dp0"
set /p TRIAL=Trial number (01-10): 
if exist .venv\Scripts\python.exe ( .venv\Scripts\python.exe scripts\run_trial.py --trial %TRIAL% ) else ( "%LOCALAPPDATA%\Python\bin\python.exe" scripts\run_trial.py --trial %TRIAL% )
pause

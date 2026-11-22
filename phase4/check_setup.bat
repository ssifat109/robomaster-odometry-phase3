@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe ( .venv\Scripts\python.exe scripts\check_setup.py ) else ( "%LOCALAPPDATA%\Python\bin\python.exe" scripts\check_setup.py )
pause

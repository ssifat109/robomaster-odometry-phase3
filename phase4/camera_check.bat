@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe ( .venv\Scripts\python.exe scripts\camera_check.py ) else ( "%LOCALAPPDATA%\Python\bin\python.exe" scripts\camera_check.py )
pause

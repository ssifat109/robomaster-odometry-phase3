@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe ( .venv\Scripts\python.exe scripts\analyze.py ) else ( "%LOCALAPPDATA%\Python\bin\python.exe" scripts\analyze.py )
pause

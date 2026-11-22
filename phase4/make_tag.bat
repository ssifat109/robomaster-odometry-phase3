@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe ( .venv\Scripts\python.exe scripts\make_tag.py ) else ( "%LOCALAPPDATA%\Python\bin\python.exe" scripts\make_tag.py )
pause

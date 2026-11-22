@echo off
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\Python\bin\python.exe" ( "%LOCALAPPDATA%\Python\bin\python.exe" -m venv .venv ) else ( py -m venv .venv )
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pause

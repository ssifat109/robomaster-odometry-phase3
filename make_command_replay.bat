@echo off
setlocal
cd /d "%~dp0"
echo Making the Trial 8 camera and code replay from recorded evidence...
wsl.exe -d Ubuntu-24.04 -- bash -lc "source ~/rm_venv/bin/activate && cd '/mnt/d/robomaster 3' && python code/make_trial8_command_replay.py"
if errorlevel 1 (
  echo Replay creation failed.
  exit /b 1
)
echo Done: presentation\trial_08_camera_and_command_replay.mp4
exit /b 0

"""Screen-record the visible Trial 10 command replay console to JPG frames."""
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "tmp" / ("command_screen_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
FRAMES.mkdir(parents=True)
TITLE = "RoboMaster Trial 10 Command Replay"

user32 = ctypes.windll.user32
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = wintypes.HWND
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.MoveWindow.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_int,
                             ctypes.c_int, ctypes.c_int, wintypes.BOOL]

proc = subprocess.Popen([sys.executable, str(ROOT / "code" / "replay_trial10_console.py")],
                        cwd=str(ROOT), creationflags=subprocess.CREATE_NEW_CONSOLE)
hwnd = None
deadline = time.perf_counter() + 6
while time.perf_counter() < deadline:
    hwnd = user32.FindWindowW(None, TITLE)
    if hwnd:
        break
    time.sleep(.1)
if not hwnd:
    proc.terminate()
    raise RuntimeError("Replay console window did not appear")

user32.MoveWindow(hwnd, 90, 75, 1280, 770, True)
user32.ShowWindow(hwnd, 9)
user32.SetForegroundWindow(hwnd)
time.sleep(.2)

fps = 10
start = time.perf_counter()
i = 0
while proc.poll() is None:
    target = start + i / fps
    delay = target - time.perf_counter()
    if delay > 0:
        time.sleep(delay)
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        break
    shot = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
    shot.save(FRAMES / f"frame_{i:05d}.jpg", quality=86)
    i += 1
    if i > 250:
        break

proc.wait(timeout=5)
print(FRAMES)
print(f"frames={i} fps={fps}")

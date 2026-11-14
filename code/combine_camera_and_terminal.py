"""Pair Trial 10 robot footage with the captured command-replay screen."""
import bisect
import csv
from pathlib import Path

import cv2
import numpy as np

root = Path(__file__).resolve().parents[1]
camera_path = root / "results" / "trial_10_camera.mp4"
screen_path = root / "presentation" / "trial_10_command_replay_screen_recording.mp4"
out_path = root / "presentation" / "trial_10_camera_and_screen_recording.mp4"
with (root / "results" / "trial_10.csv").open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
times = [float(r["elapsed_s"]) for r in rows]

camera = cv2.VideoCapture(str(camera_path))
screen = cv2.VideoCapture(str(screen_path))
if not camera.isOpened() or not screen.isOpened():
    raise RuntimeError("Cannot open both videos")
if int(camera.get(cv2.CAP_PROP_FRAME_COUNT)) != len(rows) + 1:
    raise RuntimeError("Camera and telemetry do not align")
fps = screen.get(cv2.CAP_PROP_FPS)
count = int(screen.get(cv2.CAP_PROP_FRAME_COUNT))
width, height = 2560, 736
writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps,
                         (width, height))
if not writer.isOpened():
    raise RuntimeError(f"Cannot write {out_path}")

camera_index = -1
camera_frame = None
try:
    for i in range(count):
        ok, screen_frame = screen.read()
        if not ok:
            raise RuntimeError(f"Cannot read screen frame {i}")
        t = i / fps
        # Frame 0 is START; frame k+1 is telemetry row k.
        target = bisect.bisect_right(times, t)
        target = min(target, len(rows))
        while camera_index < target:
            ok, camera_frame = camera.read()
            if not ok:
                raise RuntimeError(f"Cannot read camera frame {camera_index+1}")
            camera_index += 1
        canvas = np.full((height, width, 3), (32, 28, 22), dtype=np.uint8)
        left = cv2.resize(camera_frame, (1280, 720), interpolation=cv2.INTER_AREA)
        canvas[8:728, :1280] = left
        canvas[:, 1296:2544] = cv2.resize(screen_frame, (1248, 736))
        cv2.line(canvas, (1288, 0), (1288, height), (220, 180, 80), 2)
        writer.write(canvas)
finally:
    camera.release()
    screen.release()
    writer.release()

print(out_path)

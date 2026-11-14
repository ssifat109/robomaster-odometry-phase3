"""Play the recorded Trial 10 command log in a visible Windows console."""
import csv
import ctypes
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TITLE = "RoboMaster Trial 10 Command Replay"
ctypes.windll.kernel32.SetConsoleTitleW(TITLE)
os.system("mode con: cols=116 lines=39")

with (ROOT / "results" / "trial_10.csv").open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print("=" * 110)
print("RO B O M A S T E R   P H A S E   3     |     T R I A L   1 0")
print("Recorded command log replay  •  robot is not being commanded now")
print("Source: results/trial_10.csv  |  Camera: results/trial_10_camera.mp4")
print("=" * 110)
print("Prediction: d_pred = d_previous - delta_x")
print("Correction: d = d_pred + 0.35 * (d_tag - d_pred), if innovation <= 0.15 m")
print("Stop: d <= 0.63 m or a sensor/time safety condition")
print("Command: ep.chassis.drive_speed(x=speed, y=0, z=0)")
print("-" * 110, flush=True)

start = time.perf_counter()
last_shown = -1.0
for row in rows:
    t = float(row["elapsed_s"])
    if t - last_shown < .24 and row["phase"] == "MOVING" and float(row["commanded_speed_m_s"]) > 0:
        continue
    while time.perf_counter() - start < t:
        time.sleep(.01)
    speed = float(row["commanded_speed_m_s"])
    print(f"t={t:5.2f}s  x={float(row['odometry_x_m']):.3f}m  "
          f"pred={float(row['predicted_distance_m']):.3f}m  "
          f"tag={float(row['tag_forward_distance_m']):.3f}m  "
          f"est={float(row['corrected_distance_m']):.3f}m  "
          f"drive_speed(x={speed:.3f}, y=0, z=0)  [{row['phase']}]", flush=True)
    last_shown = t

print("-" * 110)
print("END OF RECORDED RUN  |  TARGET_STOP  |  final estimate 0.622 m", flush=True)
time.sleep(2.0)

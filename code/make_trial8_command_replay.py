"""Create a frame-aligned camera + code/telemetry replay from Trial 8.

This is an evidence-based replay. It is not a screen recording of commands
typed during the original run. Each saved camera frame corresponds to one
saved telemetry row, after the first START frame.
"""
import argparse
import csv
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--trial", type=int, default=8)
args = parser.parse_args()
VIDEO = ROOT / "results" / f"trial_{args.trial:02d}_camera.mp4"
CSV = ROOT / "results" / f"trial_{args.trial:02d}.csv"
OUT = ROOT / "presentation" / (f"trial_{args.trial:02d}_live_camera_and_commands.mp4"
                               if args.trial != 8 else "trial_08_camera_and_command_replay.mp4")
OUT.parent.mkdir(parents=True, exist_ok=True)

with CSV.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
has_command_log = "commanded_speed_m_s" in rows[0]

cap = cv2.VideoCapture(str(VIDEO))
if not cap.isOpened():
    raise RuntimeError(f"Cannot open {VIDEO}")
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
if frame_count != len(rows) + 1:
    raise RuntimeError(f"Frame/CSV mismatch: {frame_count} frames, {len(rows)} rows")

WIDTH, HEIGHT = 1920, 720
LEFT = 1200
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(str(OUT), fourcc, fps, (WIDTH, HEIGHT))
if not writer.isOpened():
    raise RuntimeError(f"Cannot create {OUT}")

BG = (34, 28, 18)
PANEL = (47, 42, 31)
WHITE = (244, 247, 249)
MUTED = (182, 197, 205)
CYAN = (218, 171, 50)
GREEN = (136, 206, 104)
ORANGE = (82, 162, 230)

def put(canvas, label, x, y, scale=.72, color=WHITE, thick=1):
    cv2.putText(canvas, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thick, cv2.LINE_AA)

def val(row, key):
    value = row.get(key, "")
    return float(value) if value else None

def fmet(value, unit="m"):
    return "--" if value is None else f"{value:.3f} {unit}"

def draw_frame(camera, row, index):
    canvas = np.full((HEIGHT, WIDTH, 3), BG, dtype=np.uint8)
    cv2.rectangle(canvas, (0, 0), (WIDTH, 55), PANEL, -1)
    put(canvas, "ROBOT CAMERA", 24, 37, .78, WHITE, 2)
    put(canvas, "SYNCED CODE + COMMAND LOG" if has_command_log else
        "CODE + TELEMETRY REPLAY", LEFT+24, 37, .78, WHITE, 2)
    # The original camera image contains the tag-ID and range overlay.
    resized = cv2.resize(camera, (LEFT, HEIGHT-55), interpolation=cv2.INTER_AREA)
    canvas[55:HEIGHT, :LEFT] = resized
    cv2.line(canvas, (LEFT, 55), (LEFT, HEIGHT), CYAN, 2)

    x0 = LEFT + 25
    if row is None:
        put(canvas, f"Recorded Trial {args.trial}  |  START", x0, 92, .78, CYAN, 2)
        put(canvas, "Waiting for first telemetry update", x0, 132, .68, MUTED)
        return canvas

    elapsed = val(row, "elapsed_s")
    odom = val(row, "odometry_x_m")
    delta = val(row, "delta_x_m")
    predicted = val(row, "predicted_distance_m")
    observed = val(row, "tag_forward_distance_m")
    corrected = val(row, "corrected_distance_m")
    phase = row["phase"]
    innovation = None if observed is None or predicted is None else observed - predicted
    accepted = innovation is not None and abs(innovation) <= .15
    if phase != "MOVING" or corrected <= .63:
        command = "STOP  x=0, y=0, z=0"
        command_color = ORANGE
    else:
        speed = (val(row, "commanded_speed_m_s") if has_command_log else
                 min(.10, max(.03, .5*(corrected-.63))))
        command = ("LOGGED " if has_command_log else "NEXT ") + \
                  f"x={speed:.3f}, y=0, z=0 m/s"
        command_color = GREEN

    put(canvas, f"Trial {args.trial} | {phase} | frame {index}/{frame_count-1}", x0, 92, .70, CYAN, 2)
    put(canvas, f"Elapsed {elapsed:5.2f} s", x0, 124, .63, MUTED)
    cv2.line(canvas, (x0, 143), (WIDTH-25, 143), (89, 94, 92), 1)

    code = [
        ("171  dx = x_now - x_prev", 178),
        ("172  d_pred = d_prev - dx", 215),
        ("179  if abs(d_tag-d_pred) <= 0.15:", 252),
        ("180      d = d_pred + 0.35*(d_tag-d_pred)", 289),
        ("192  if d <= 0.55 + 0.08: STOP", 326),
        ("194  speed = min(0.10, max(0.03,", 363),
        ("               0.5*(d-0.63)))", 398),
        ("196  drive_speed(x=speed,y=0,z=0)", 435),
    ]
    for line, y in code:
        color = ORANGE if (y == 326 and command.startswith("STOP")) else WHITE
        put(canvas, line, x0, y, .54, color, 1)
    cv2.line(canvas, (x0, 455), (WIDTH-25, 455), (89, 94, 92), 1)

    metrics = [
        ("Chassis x", fmet(odom)),
        ("Delta x", fmet(delta)),
        ("Predicted", fmet(predicted)),
        ("Camera tag", fmet(observed)),
        ("Corrected", fmet(corrected)),
        ("Innovation", fmet(innovation)),
    ]
    for j,(name,value) in enumerate(metrics):
        y = 486 + j*29
        put(canvas, name, x0, y, .57, MUTED)
        put(canvas, value, x0+360, y, .57, WHITE)
    put(canvas, command, x0, 686, .67, command_color, 2)
    return canvas

try:
    for i in range(frame_count):
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError(f"Could not read camera frame {i}")
        row = None if i == 0 else rows[i-1]
        writer.write(draw_frame(frame, row, i))
finally:
    cap.release()
    writer.release()

print(OUT)

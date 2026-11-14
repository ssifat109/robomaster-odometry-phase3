"""Encode captured command-console screenshots as a screen-recording MP4."""
import argparse
from pathlib import Path

import cv2

parser = argparse.ArgumentParser()
parser.add_argument("frames")
args = parser.parse_args()
folder = Path(args.frames)
files = sorted(folder.glob("frame_*.jpg"))
if len(files) < 50:
    raise RuntimeError(f"Too few screen frames: {len(files)}")
first = cv2.imread(str(files[0]))
first = first[34:, 32:]  # trim the small area behind the rounded terminal window
height, width = first.shape[:2]
out = Path(__file__).resolve().parents[1] / "presentation" / "trial_10_command_replay_screen_recording.mp4"
writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), 10.0,
                         (width, height))
if not writer.isOpened():
    raise RuntimeError(f"Could not create {out}")
try:
    for file in files:
        frame = cv2.imread(str(file))
        if frame is None:
            raise RuntimeError(f"Cannot read {file}")
        writer.write(cv2.resize(frame[34:, 32:], (width, height)))
finally:
    writer.release()
print(out)

"""Attended, short low-speed odometry and stop-response check."""
import json
import time
from pathlib import Path

from phase3 import connect, forward_range, load_config, sample_tag
from vision import TagDetector

cfg = load_config("config/phase3.yaml")
if not cfg.get("calibration_verified") or not cfg.get("tag_visible_at_start_verified"):
    raise SystemExit("Camera gates are not verified")
ep = connect(cfg)
position = {"x": None, "stamp": -1e9}
def on_position(data):
    position["x"], position["stamp"] = float(data[0]), time.monotonic()

result = {"motion_command_m_s": 0.06, "command_duration_s": 0.6}
try:
    ep.chassis.drive_speed(x=0, y=0, z=0)
    if not ep.chassis.sub_position(cs=0, freq=20, callback=on_position):
        raise RuntimeError("No odometry subscription")
    if not ep.camera.start_video_stream(display=False, resolution="720p"):
        raise RuntimeError("No camera stream")
    detector = TagDetector(cfg)
    tag, _ = sample_tag(ep, detector)
    if tag is None or position["x"] is None:
        raise RuntimeError("Fresh tag/odometry unavailable")
    initial_range = forward_range(tag, cfg)
    if abs(initial_range-cfg["start_distance_m"]) > cfg["start_tolerance_m"]:
        raise RuntimeError(f"Start range {initial_range:.3f} m is outside tolerance")
    start_x = position["x"]
    result["initial_estimated_range_m"] = initial_range
    ep.chassis.drive_speed(x=0.06, y=0, z=0, timeout=0.7)
    time.sleep(0.6)
    ep.chassis.drive_speed(x=0, y=0, z=0, timeout=0.5)
    time.sleep(0.8)
    result["odometry_delta_x_m"] = position["x"]-start_x
    result["odometry_direction_ok"] = 0.005 < result["odometry_delta_x_m"] < 0.10
    tag, _ = sample_tag(ep, detector)
    if tag:
        result["final_estimated_range_m"] = forward_range(tag, cfg)
    print(json.dumps(result, indent=2))
    Path("results/motion_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
finally:
    ep.chassis.drive_speed(x=0, y=0, z=0, timeout=0.5)
    try: ep.chassis.unsub_position()
    finally:
        try:
            conn = ep.camera._liveview._video_stream_conn
            conn._sock_queue.maxsize = 0
            ep.camera.stop_video_stream()
        finally: ep.close()

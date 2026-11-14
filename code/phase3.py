"""Phase 3: stationary tag preflight and guarded straight-line trials."""
import argparse
import csv
import json
import math
import socket
import sys
import time
from pathlib import Path

import cv2
import yaml
from robomaster import config as sdk_config, robot

from vision import TagDetector


def finite_positive(value, name):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return value


def load_config(path):
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    for key in ("start_distance_m", "stop_distance_m", "max_speed_m_s",
                "max_duration_s", "max_tag_age_s", "max_odometry_age_s"):
        cfg[key] = finite_positive(cfg[key], key)
    if not 1 <= cfg["start_distance_m"] <= 2:
        raise ValueError("start distance must be 1 to 2 m")
    if not cfg["stop_distance_m"] < cfg["start_distance_m"]:
        raise ValueError("stop distance must be less than start distance")
    if not 0 < float(cfg["correction_gain"]) <= 1:
        raise ValueError("correction_gain must be in (0, 1]")
    return cfg


def connect(cfg):
    if cfg.get("local_ip"):
        sdk_config.LOCAL_IP_STR = cfg["local_ip"]
    elif cfg.get("conn_type") == "ap":
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.168.2.1", 20020))
            sdk_config.LOCAL_IP_STR = sock.getsockname()[0]
    ep = robot.Robot()
    if not ep.initialize(conn_type=cfg.get("conn_type", "ap")):
        raise RuntimeError("RoboMaster SDK connection failed")
    return ep


def sample_tag(ep, detector):
    frame = ep.camera.read_cv2_image(timeout=2, strategy="newest")
    if frame is None:
        return None, None
    return detector.detect(frame), frame


def forward_range(tag, cfg):
    if not cfg.get("calibration_verified"):
        raise RuntimeError("Camera range calibration is not verified")
    return cfg["range_scale"] * tag["camera_forward_m"] + cfg["range_offset_m"]


def preflight(ep, detector, cfg, out, known_distance=None):
    samples = []
    image_name = (f"preflight_{round(known_distance*1000)}mm.jpg"
                  if known_distance is not None else "preflight_latest.jpg")
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        tag, frame = sample_tag(ep, detector)
        if frame is not None:
            cv2.imwrite(str(out / image_name), frame)
        samples.append({"time_s": time.monotonic(), "tag": tag})
    valid = [s["tag"] for s in samples if s["tag"]]
    valid_times = [s["time_s"] for s in samples if s["tag"]]
    max_gap = max((b-a for a, b in zip(valid_times, valid_times[1:])), default=None)
    camera_ranges = sorted(v["camera_forward_m"] for v in valid)
    ranges = sorted(forward_range(v, cfg) for v in valid) if cfg.get("calibration_verified") else []
    report = {"frames": len(samples), "detections": len(valid),
              "detection_fraction": len(valid) / max(1, len(samples)),
              "max_between_detections_s": max_gap,
              "median_camera_forward_m": camera_ranges[len(camera_ranges)//2] if camera_ranges else None,
              "median_calibrated_forward_range_m": ranges[len(ranges)//2] if ranges else None,
              "known_bumper_to_tag_m": known_distance,
              "calibration_verified": bool(cfg.get("calibration_verified"))}
    candidate_path = out / "range_candidate.json"
    if camera_ranges and candidate_path.exists():
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate_range = (candidate["range_scale"] * report["median_camera_forward_m"]
                           + candidate["range_offset_m"])
        report["candidate_bumper_to_tag_m"] = candidate_range
        if known_distance is not None:
            report["candidate_error_m"] = candidate_range - known_distance
    name = (f"preflight_{round(known_distance*1000)}mm.json"
            if known_distance is not None else "preflight.json")
    (out / name).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


def run_trial(ep, detector, cfg, out, trial):
    if not cfg.get("calibration_verified"):
        raise RuntimeError("Calibration is unverified. Complete measured near/far checks first.")
    if not cfg.get("tag_visible_at_start_verified"):
        raise RuntimeError("Far-start tag visibility is unverified.")
    if not cfg.get("safety_stop_verified"):
        raise RuntimeError("Physical stop response has not been verified.")
    if not cfg.get("operator_present"):
        raise RuntimeError("Set operator_present only while an operator is beside the robot.")
    if (out / f"trial_{trial:02d}.csv").exists():
        raise FileExistsError("Trial output exists; refusing to overwrite evidence")

    odo = {"x": None, "stamp": -1e9}
    def on_position(position):
        odo["x"], odo["stamp"] = float(position[0]), time.monotonic()

    if not ep.chassis.sub_position(cs=0, freq=20, callback=on_position):
        raise RuntimeError("Chassis position subscription failed")
    rows = []
    video_writer = None
    video_path = out / f"trial_{trial:02d}_camera.mp4"
    def record_frame(frame, tag, distance, phase):
        nonlocal video_writer
        if frame is None:
            return
        if video_writer is None:
            h, w = frame.shape[:2]
            video_writer = cv2.VideoWriter(str(video_path),
                                           cv2.VideoWriter_fourcc(*"mp4v"), 25.0, (w, h))
            if not video_writer.isOpened():
                raise RuntimeError("Could not open camera video file")
        annotated = frame.copy()
        if tag:
            for corners, tag_id in zip(detector.last_corners, detector.last_ids):
                if tag_id == 3:
                    cv2.polylines(annotated, [corners.astype("int32")], True, (0, 255, 0), 3)
        label = f"Tag 3: {'DETECTED' if tag else 'LOST'} | {phase} | estimate {distance:.3f} m"
        cv2.rectangle(annotated, (0, 0), (min(frame.shape[1], 980), 45), (0, 0, 0), -1)
        cv2.putText(annotated, label, (12, 31), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (255, 255, 255), 2, cv2.LINE_AA)
        video_writer.write(annotated)
    start = time.monotonic()
    last_console = start
    last_odo = None
    estimate = None
    last_tag_time = -1e9
    reason = "TIMEOUT"
    try:
        # Stationary acquisition; no command before a valid fresh tag and odometry.
        while time.monotonic() - start < 10:
            tag, frame = sample_tag(ep, detector)
            now = time.monotonic()
            if tag and odo["x"] is not None and now - odo["stamp"] < cfg["max_odometry_age_s"]:
                forward = forward_range(tag, cfg)
                if abs(forward - cfg["start_distance_m"]) <= cfg["start_tolerance_m"]:
                    estimate = forward
                    last_odo = odo["x"]
                    last_tag_time = now
                    record_frame(frame, tag, estimate, "START")
                    break
        if estimate is None:
            raise RuntimeError("No fresh tag/odometry at the measured start distance")

        while True:
            now = time.monotonic()
            if now - start >= cfg["max_duration_s"]:
                reason = "TIMEOUT"; break
            if odo["x"] is None or now - odo["stamp"] > cfg["max_odometry_age_s"]:
                reason = "ODOMETRY_STALE"; break
            delta = odo["x"] - last_odo
            last_odo = odo["x"]
            predicted = estimate - delta
            tag, frame = sample_tag(ep, detector)
            now = time.monotonic()
            observed = ""
            if tag:
                observed = forward_range(tag, cfg)
                # Reject discontinuous pose solutions before the correction.
                if abs(observed - predicted) <= cfg["max_innovation_m"]:
                    estimate = predicted + cfg["correction_gain"] * (observed - predicted)
                    last_tag_time = now
                else:
                    estimate = predicted
            else:
                estimate = predicted
            if now - last_tag_time > cfg["max_tag_age_s"]:
                reason = "TAG_STALE"; break
            # Guard includes a margin for one camera/control cycle of travel.
            if estimate <= cfg["stop_distance_m"] + cfg["stop_margin_m"]:
                speed = 0.0
                reason = "TARGET_STOP"
            else:
                speed = min(cfg["max_speed_m_s"], max(0.03, 0.5 *
                            (estimate-cfg["stop_distance_m"]-cfg["stop_margin_m"])))
            rows.append([now-start, odo["x"], delta, predicted, observed,
                         estimate, now-last_tag_time, "MOVING", speed])
            record_frame(frame, tag, estimate, "MOVING")
            if now - last_console >= 0.25 or speed == 0:
                print(f"t={now-start:5.2f}s x={odo['x']:.3f}m "
                      f"d_pred={predicted:.3f}m d_est={estimate:.3f}m "
                      f"drive_speed(x={speed:.3f}, y=0, z=0)", flush=True)
                last_console = now
            if speed == 0:
                break
            ep.chassis.drive_speed(x=speed, y=0, z=0, timeout=0.25)
    finally:
        ep.chassis.drive_speed(x=0, y=0, z=0, timeout=0.5)
        # Record the estimate after the chassis has had time to settle, so the
        # reported final estimate refers to the same stopped pose as the tape.
        if estimate is not None and last_odo is not None:
            settle_end = time.monotonic() + 0.8
            while time.monotonic() < settle_end:
                tag, frame = sample_tag(ep, detector)
                now = time.monotonic()
                if odo["x"] is None:
                    continue
                delta = odo["x"] - last_odo
                last_odo = odo["x"]
                predicted = estimate - delta
                observed = ""
                estimate = predicted
                if tag:
                    observed = forward_range(tag, cfg)
                    if abs(observed - predicted) <= cfg["max_innovation_m"]:
                        estimate += cfg["correction_gain"] * (observed - predicted)
                        last_tag_time = now
                rows.append([now-start, odo["x"], delta, predicted, observed,
                             estimate, now-last_tag_time, "POST_STOP", 0.0])
                record_frame(frame, tag, estimate, "STOPPED")
        ep.chassis.unsub_position()
        if video_writer is not None:
            video_writer.release()
        path = out / f"trial_{trial:02d}.csv"
        if rows:
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["elapsed_s", "odometry_x_m", "delta_x_m", "predicted_distance_m",
                                 "tag_forward_distance_m", "corrected_distance_m", "tag_age_s", "phase",
                                 "commanded_speed_m_s"])
                writer.writerows(rows)
            (out / f"trial_{trial:02d}.json").write_text(json.dumps({
                "trial": trial, "stop_reason": reason, "estimated_final_distance_m": estimate,
                "measured_final_distance_m": None, "reference_point": cfg["reference_point"],
                "camera_video": str(video_path) if video_writer is not None else None}, indent=2),
                encoding="utf-8")
        print(f"Stop: {reason}; estimated final distance: {estimate}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preflight", "trial"])
    parser.add_argument("--config", default="config/phase3.yaml")
    parser.add_argument("--trial", type=int)
    parser.add_argument("--known-distance", type=float,
                        help="Tape-measured front-bumper-to-tag-plane distance (m), stationary preflight only")
    args = parser.parse_args()
    cfg = load_config(args.config)
    if args.mode == "trial" and (args.trial is None or not 1 <= args.trial <= 10):
        parser.error("--trial must be 1 to 10")
    if args.known_distance is not None and args.mode != "preflight":
        parser.error("--known-distance is only valid in preflight")
    if args.known_distance is not None:
        finite_positive(args.known_distance, "known distance")
    out = Path("results")
    out.mkdir(exist_ok=True)
    ep = connect(cfg)
    try:
        ep.chassis.drive_speed(x=0, y=0, z=0)
        if not ep.camera.start_video_stream(display=False, resolution="720p"):
            raise RuntimeError("Camera stream failed")
        detector = TagDetector(cfg)
        if args.mode == "preflight":
            preflight(ep, detector, cfg, out, args.known_distance)
        else:
            run_trial(ep, detector, cfg, out, args.trial)
    finally:
        try: ep.chassis.drive_speed(x=0, y=0, z=0)
        finally:
            try:
                # SDK disconnect puts a sentinel into a bounded stream queue.
                # If the decoder has stopped while it is full, that put hangs.
                liveview = ep.camera._liveview
                stream_conn = getattr(liveview, "_video_stream_conn", None)
                if stream_conn is not None:
                    stream_conn._sock_queue.maxsize = 0
                ep.camera.stop_video_stream()
            finally: ep.close()


if __name__ == "__main__":
    main()

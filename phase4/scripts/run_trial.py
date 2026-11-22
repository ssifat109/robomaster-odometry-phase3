"""Capture timestamped odometry and camera tag detections while driving straight."""
import argparse
import csv
import json
import math
import queue
import threading
import time
from pathlib import Path
from datetime import datetime

import cv2
from robot_connection import connect

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', help='two-digit trial number, 01 through 99')
    parser.add_argument('--pilot', action='store_true', help='2-second non-report movement check')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--video', action='store_true', help='save a separate robot camera MP4')
    args = parser.parse_args()
    if not args.pilot and args.trial not in [f'{i:02}' for i in range(1, 100)]:
        parser.error('trial must be 01 through 99')
    cfg = json.loads((ROOT / 'config.json').read_text())
    duration = 2.0 if args.pilot else cfg['duration_s']
    destination = ROOT / 'raw' / ('pilot.csv' if args.pilot else f'trial_{args.trial}.csv')
    if destination.exists():
        parser.error(f'{destination} exists; refusing to overwrite a trial')
    if args.dry_run:
        print('Would record', destination)
        print('Speed/duration:', cfg['forward_speed_mps'], duration)
        return

    from robomaster import camera
    events = queue.Queue()
    start = time.monotonic()
    last_odom_time = [None]

    def timestamp():
        return time.monotonic() - start

    def on_position(pos):
        t = timestamp()
        last_odom_time[0] = t
        events.put(('odom', t, float(pos[0]), float(pos[1]), float(pos[2]), ''))

    def on_attitude(att):
        events.put(('attitude', timestamp(), float(att[0]), float(att[1]), float(att[2]), ''))

    ep = connect(cfg)
    chassis, cam = ep.chassis, ep.camera
    detector = cv2.aruco.ArucoDetector(
        cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, cfg['tag_dictionary'])),
        cv2.aruco.DetectorParameters())
    running = threading.Event()
    running.set()

    def video_worker():
        while running.is_set():
            try:
                frame = cam.read_cv2_image(timeout=1, strategy='newest')
            except queue.Empty:
                continue
            if frame is None:
                continue
            if video_writer is not None:
                video_writer.write(frame)
            corners, ids, _ = detector.detectMarkers(frame)
            if ids is None:
                continue
            for points, tag_id in zip(corners, ids.flatten()):
                if int(tag_id) != cfg['tag_id']:
                    continue
                xs = points.reshape(4, 2)[:, 0]
                cx = float(xs.mean())
                events.put(('tag', timestamp(), cx, float(frame.shape[1]),
                            float(xs.max() - xs.min()), int(tag_id)))

    ROOT.joinpath('raw').mkdir(exist_ok=True)
    collected = []
    video_writer = None
    try:
        if args.video:
            ROOT.joinpath('videos').mkdir(exist_ok=True)
            video_path = ROOT / 'videos' / ('pilot_camera.mp4' if args.pilot else f'trial_{args.trial}_camera.mp4')
            video_writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*'mp4v'),
                                           15.0, (1280, 720))
            if not video_writer.isOpened():
                raise RuntimeError(f'Could not open camera video file: {video_path}')
            print(f'Camera recording: {video_path}')
        chassis.sub_position(cs=0, freq=cfg['sample_hz'], callback=on_position)
        chassis.sub_attitude(freq=cfg['sample_hz'], callback=on_attitude)
        cam.start_video_stream(display=False, resolution=camera.STREAM_720P)
        worker = threading.Thread(target=video_worker, daemon=True)
        worker.start()
        print('Waiting for initial odometry and tag detection...')
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                collected.append(events.get(timeout=0.2))
            except queue.Empty:
                pass
            if (any(x[0] == 'odom' for x in collected)
                    and any(x[0] == 'attitude' for x in collected)
                    and any(x[0] == 'tag' for x in collected)):
                break
        else:
            raise RuntimeError('No initial odometry/tag. Check connection, lighting and tag visibility.')
        print('Starting forward run. Keep the path clear; Ctrl+C stops the robot.')
        events.put(('drive_start', timestamp(), '', '', '', ''))
        drive_start = time.monotonic()
        while time.monotonic() - drive_start < duration:
            if last_odom_time[0] is None or timestamp() - last_odom_time[0] > 0.6:
                raise RuntimeError('Odometry stale; stopping robot')
            chassis.drive_speed(x=cfg['forward_speed_mps'], y=0, z=0, timeout=0.25)
            time.sleep(0.10)
        chassis.drive_speed(x=0, y=0, z=0)
        events.put(('drive_stop', timestamp(), '', '', '', ''))
        time.sleep(0.5)
    finally:
        running.clear()
        try:
            chassis.drive_speed(x=0, y=0, z=0)
            if 'worker' in locals():
                worker.join(timeout=2)
            if video_writer is not None:
                video_writer.release()
            while not events.empty():
                collected.append(events.get_nowait())
            if collected and not destination.exists():
                collected.sort(key=lambda x: x[1])
                with destination.open('w', newline='') as fh:
                    writer = csv.writer(fh)
                    writer.writerow(['type', 'time_s', 'value_1', 'value_2', 'value_3', 'extra'])
                    writer.writerows(collected)
                print('Saved', destination, '|', len(collected), 'events')
            chassis.unsub_position()
            chassis.unsub_attitude()
            cam.stop_video_stream()
        finally:
            ep.close()


if __name__ == '__main__':
    main()

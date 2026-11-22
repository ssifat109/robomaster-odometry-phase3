"""Stationary robot connectivity and ArUco visibility check. Never drives chassis."""
import json
from pathlib import Path
import time
import cv2
import numpy as np
from ekf import bearing, camera_bearing_from_tag
from robot_connection import connect

ROOT = Path(__file__).resolve().parents[1]


def main():
    cfg = json.loads((ROOT / 'config.json').read_text())
    from robomaster import camera
    ep = connect(cfg)
    cam = ep.camera
    detector = cv2.aruco.ArucoDetector(
        cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, cfg['tag_dictionary'])),
        cv2.aruco.DetectorParameters())
    seen = 0
    frames = 0
    bearings = []
    try:
        cam.start_video_stream(display=False, resolution=camera.STREAM_720P)
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            frame = cam.read_cv2_image(timeout=1)
            if frame is None:
                continue
            frames += 1
            if frames == 1:
                ROOT.joinpath('results').mkdir(exist_ok=True)
                cv2.imwrite(str(ROOT / 'results' / 'camera_check_raw.png'), frame)
            corners, ids, _ = detector.detectMarkers(frame)
            if ids is not None and cfg['tag_id'] in ids.flatten():
                seen += 1
                index = list(ids.flatten()).index(cfg['tag_id'])
                cx = float(corners[index].reshape(4, 2)[:, 0].mean())
                bearings.append(camera_bearing_from_tag(cx, frame.shape[1], cfg))
                if seen == 1:
                    cv2.aruco.drawDetectedMarkers(frame, corners, ids)
                    ROOT.joinpath('results').mkdir(exist_ok=True)
                    cv2.imwrite(str(ROOT / 'results' / 'camera_check.png'), frame)
        print(f'Camera frames: {frames}; target-tag frames: {seen}')
        if len(bearings) > 1:
            expected = bearing((cfg['initial_x_m'], cfg['initial_y_m'],
                                cfg['initial_heading_rad']), cfg)
            print(f'Mean observed bearing: {np.degrees(np.mean(bearings)):.2f} degrees; '
                  f'geometry prediction: {np.degrees(expected):.2f} degrees')
            print(f'Stationary bearing std: {np.degrees(np.std(bearings, ddof=1)):.2f} degrees')
        if seen:
            print('Saved results/camera_check.png. Check framing before a run.')
        else:
            print('Tag not detected. Check printing, lighting, distance, and camera aim.')
    finally:
        try:
            cam.stop_video_stream()
        finally:
            ep.close()


if __name__ == '__main__':
    main()

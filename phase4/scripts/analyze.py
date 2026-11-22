"""Replay captured data and make assignment tables, plots, and report skeleton."""
import csv
import json
import math
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from ekf import BearingEKF, camera_bearing_from_tag, wrap

ROOT = Path(__file__).resolve().parents[1]


def read_events(path):
    with path.open(newline='') as fh:
        return sorted(csv.DictReader(fh), key=lambda row: float(row['time_s']))


def replay(path, cfg):
    ekf = BearingEKF(cfg)
    odom0 = None
    last_odom = None
    latest_raw = None
    yaw0 = None
    last_yaw = None
    previous_heading = 0.0
    odom_trace = [[cfg['initial_x_m'], cfg['initial_y_m']]]
    ekf_trace = [ekf.x[:2].copy()]
    gain_trace = []
    tags = 0
    odom_count = 0
    started = False
    for event in read_events(path):
        typ = event['type']
        if typ == 'attitude':
            # DJI attitude callback: yaw, pitch, roll in degrees.
            yaw = math.radians(float(event['value_1']))
            if yaw0 is None:
                yaw0 = yaw
            last_yaw = wrap(yaw - yaw0)
        elif typ == 'drive_start':
            if latest_raw is None or yaw0 is None:
                raise ValueError(f'{path}: missing odometry/attitude before drive start')
            odom0 = latest_raw.copy()
            last_odom = np.zeros(2)
            previous_heading = 0.0
            started = True
        elif typ == 'odom':
            raw = np.array([float(event['value_1']), float(event['value_2'])])
            latest_raw = raw
            if not started:
                continue
            # Rotate the SDK's global x/y into the marked run frame.
            c0, s0 = math.cos(yaw0), math.sin(yaw0)
            delta_from_start = raw - odom0
            relative = np.array([c0 * delta_from_start[0] + s0 * delta_from_start[1],
                                 -s0 * delta_from_start[0] + c0 * delta_from_start[1]])
            delta = relative - last_odom
            last_odom = relative
            # The SDK cs=0 position frame is aligned with chassis at subscription.
            # Convert its world-frame increments into body-frame control increments.
            raw_heading = last_yaw if last_yaw is not None else 0.0
            c, s = math.cos(raw_heading), math.sin(raw_heading)
            forward = c * delta[0] + s * delta[1]
            left = -s * delta[0] + c * delta[1]
            dtheta = wrap(raw_heading - previous_heading)
            previous_heading = raw_heading
            ekf.predict(forward, left, dtheta)
            odom_trace.append([cfg['initial_x_m'] + relative[0],
                               cfg['initial_y_m'] + relative[1]])
            ekf_trace.append(ekf.x[:2].copy())
            odom_count += 1
        elif typ == 'tag' and started:
            obs = camera_bearing_from_tag(float(event['value_1']),
                                          float(event['value_2']), cfg)
            # Reject extreme detections near image edges.
            if abs(obs) > math.radians(cfg['camera_horizontal_fov_deg'] * 0.47):
                continue
            gain, innovation = ekf.update(obs)
            ekf_trace.append(ekf.x[:2].copy())
            gain_trace.append([float(event['time_s']), *gain, innovation])
            tags += 1
    if odom_count < 2:
        raise ValueError(f'{path}: too few odometry samples')
    if tags < 2:
        raise ValueError(f'{path}: too few tag detections')
    return dict(odom=np.array(odom_trace), ekf=np.array(ekf_trace),
                P=ekf.P, gain=gain_trace, tags=tags, odom_count=odom_count)


def main():
    cfg = json.loads((ROOT / 'config.json').read_text())
    actuals = {}
    with (ROOT / 'measurements.csv').open(newline='') as fh:
        for row in csv.DictReader(fh):
            if row['actual_x_m'] and row['actual_y_m']:
                actuals[row['trial']] = np.array([float(row['actual_x_m']),
                                                   float(row['actual_y_m'])])
    paths = sorted((ROOT / 'raw').glob('trial_*.csv')) if (ROOT / 'raw').exists() else []
    excluded = json.loads((ROOT / 'excluded_trials.json').read_text())
    if not paths:
        print('No raw trials yet. Run the robot and fill measurements.csv.')
        return
    output = ROOT / 'results'
    output.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 6))
    rows = []
    for path in paths:
        trial = path.stem.split('_')[-1]
        if trial in excluded:
            continue
        try:
            result = replay(path, cfg)
        except ValueError as exc:
            print('Skipping:', exc, file=sys.stderr)
            continue
        odom_final = result['odom'][-1]
        ekf_final = result['ekf'][-1]
        actual = actuals.get(trial)
        sigmas = np.sqrt(np.diag(result['P']))
        row = dict(trial=trial, odom_x_m=odom_final[0], odom_y_m=odom_final[1],
                   ekf_x_m=ekf_final[0], ekf_y_m=ekf_final[1],
                   actual_x_m='' if actual is None else actual[0],
                   actual_y_m='' if actual is None else actual[1],
                   odom_error_m='' if actual is None else np.linalg.norm(odom_final - actual),
                   ekf_error_m='' if actual is None else np.linalg.norm(ekf_final - actual),
                   ekf_sigma_x_m=sigmas[0], ekf_sigma_y_m=sigmas[1],
                   abs_x_error_over_sigma='' if actual is None else abs(ekf_final[0]-actual[0])/sigmas[0],
                   abs_y_error_over_sigma='' if actual is None else abs(ekf_final[1]-actual[1])/sigmas[1],
                   tag_updates=result['tags'])
        rows.append(row)
        ax.plot(result['odom'][:, 0], result['odom'][:, 1], '--', alpha=.65,
                label=f'{trial} odom')
        ax.plot(result['ekf'][:, 0], result['ekf'][:, 1], '-', alpha=.8,
                label=f'{trial} EKF')
        if actual is not None:
            ax.scatter(*actual, marker='x', color='black')
        with (output / f'gain_{trial}.csv').open('w', newline='') as fh:
            writer = csv.writer(fh)
            writer.writerow(['time_s', 'K_x', 'K_y', 'K_heading', 'innovation_rad'])
            writer.writerows(result['gain'])
    if not rows:
        print('No valid trials to analyze.')
        return
    with (output / 'summary.csv').open('w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    ax.scatter(cfg['tag_x_m'], cfg['tag_y_m'], marker='s', s=90, color='red', label='tag')
    ax.set(xlabel='x (m)', ylabel='y (m)', title='Phase 4 trajectories')
    ax.axis('equal')
    ax.grid(True)
    ax.legend(fontsize=7, ncol=2, loc='best')
    fig.tight_layout()
    fig.savefig(output / 'trajectories.png', dpi=180)
    plt.close(fig)
    complete = [r for r in rows if r['odom_error_m'] != '']
    mean_odom = np.mean([r['odom_error_m'] for r in complete]) if complete else None
    mean_ekf = np.mean([r['ekf_error_m'] for r in complete]) if complete else None
    report = f'''# Phase 4 report draft

## Experimental setup
Describe floor frame, tag center ({cfg['tag_x_m']}, {cfg['tag_y_m']}) m, measured tag size, camera offset, initial pose, straight path, lighting, and independent endpoint measurement method. Add setup photo/video link.

## Method
State: x, y, heading. Prediction uses odometry displacement and heading. Bearing update uses the tag center and camera FOV. Explain the motion and bearing Jacobians, Kalman gain, covariance propagation, and Joseph covariance correction. See `scripts/ekf.py`.

## Noise
Q diagonal per odometry step: {[cfg['motion_std_x_m_per_step']**2, cfg['motion_std_y_m_per_step']**2, math.radians(cfg['motion_std_heading_deg_per_step'])**2]}. R: {math.radians(cfg['bearing_std_deg'])**2} rad². These are provisional until calibrated. Record repeated stationary bearing measurements and motion repeatability; explain the estimates used in the final report.

## Results
See `summary.csv` and `trajectories.png`. Completed trials: {len(complete)}. Mean odometry position error: {mean_odom}. Mean EKF position error: {mean_ekf}. Discuss per-axis absolute errors against sigma x/y, and count how many lie within one sigma. Avoid statistical claims from only 8–10 trials.

## Discussion
Discuss bearing geometry, gain, uncertainty, tag visibility, camera calibration, odometry slip, heading drift, timestamp lag, and independently measured endpoint error. Add observed findings after data collection.

## Submission
Add GitHub repository link and demonstration video link.
'''
    (output / 'report_draft.md').write_text(report, encoding='utf-8')
    print('Analyzed', len(rows), 'trials; complete measurements:', len(complete))
    print('Results:', output)


if __name__ == '__main__':
    main()

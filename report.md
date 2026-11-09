# RoboMaster Odometry - Phase 3

**Course:** SCE-672 Advanced Robotics

**Instructor:** Professor Aamer Iqbal Bhatti

**Student:** Md. Shakib Al Sifat (202613880)
**Experiment date:** 10 November 2026

## Objective

The RoboMaster EP Core detected a fixed tag and drove straight toward it from
the same measured 1.50 m starting distance on eight successful trials. The
robot stopped before the tag. Its remaining-distance estimate combined
chassis-position odometry prediction with camera-based tag correction. The
estimated distance after stopping was compared with an independently measured
bumper-to-tag distance in every trial.

## Equipment and experimental setup

The printed target was AprilTag family 36h11, ID 3, mounted upright on a
freestanding cardboard support, facing the robot. The measured black-square
width was 0.142 m. Its lower black edge was about 0.01 m above the floor, so
the centre was about 0.081 m high. The tag and camera arm pose remained fixed.
The robot travelled on the same indoor tile floor and began each successful
trial with the **front bumper centre** 1.50 m from the flat front plane of the
tag. The same two physical surfaces defined the final tape measurement.

The nominal stop distance was 0.55 m. The controller applied an 0.08 m early
stop margin, so it commanded zero speed when its estimate reached about
0.63 m. The maximum forward command was 0.10 m/s; lateral and yaw commands
were zero. An operator stayed beside the robot. A separate phone recording
captured the full first approach, and `results/trial_08_camera.mp4` shows the
onboard camera view with tag and estimate overlays.

## Detection, prediction, and correction

OpenCV detected ID 3 in the 1280 x 720 camera frames and estimated its pose
from the four marker corners, measured square width, calibrated camera
intrinsics, and an IPPE square PnP solution. Frames were read using the SDK's
`newest` strategy. A two-position tape survey mapped camera-axis range to
front-bumper-to-tag distance:

`camera_distance_m = 0.97387735 * camera_axis_depth_m - 0.23056594`.

The survey pairs were 0.57 m tape / 0.8220 m camera-axis depth and 1.50 m tape /
1.7770 m camera-axis depth. An independent check at 0.40 m yielded 0.3621 m
(-0.0379 m error); a check at 1.45 m after a short motion yielded 1.4776 m
(+0.0276 m error). This uncertainty motivated the conservative stop. The old
Phase 2 camera-to-body transform failed a physical height check and was not
used to calculate the forward-range correction. The detector retained it as
compatibility metadata and a forward-facing filter. The front ToF returned zero in prior checks,
so it was **not** used for correction.

The SDK chassis position subscription supplied forward odometry at 20 Hz. If
the previous corrected distance is `d`, and the new odometry increment is
`delta_x`, the prediction is `d_pred = d - delta_x`. For a fresh camera range
`z`, the corrected estimate is `d_new = d_pred + 0.35*(z - d_pred)` when the
innovation magnitude is at most 0.15 m. Otherwise, the prediction is retained.
The robot commands zero speed if the tag has been stale for over 0.50 s,
odometry for over 0.30 s, the time limit of 25 s is reached, or the target
stop guard is reached. A short post-stop sensing interval produces the final
estimate at the stopped pose rather than at the first stop command.

## Preflight and trial procedure

Stationary checks detected the tag in 86/86 frames at 0.57 m, 113/113 at
1.50 m, and 111/111 at 0.40 m. A brief 0.06 m/s, 0.6 s attended motion check
commanded a stop; the robot visibly moved about 0.05 m by tape while chassis
odometry reported +0.034 m. After each successful full trial, the robot was
returned by hand to the 1.50 m bumper-to-tag mark before the next run.
The final distance was independently measured with a tape after the robot had
stopped, before it was moved. The first tape reading was reported as
"almost 61 cm"; calculations use 0.61 m, so the first error is approximate.

## Results

Error is **estimated final distance minus measured final distance**. Values
below are rounded to 0.1 cm from the logged estimates and reported tape
measurements. Trial number 7 was an aborted attempt and is described below.

| Trial | Estimated (cm) | Measured (cm) | Signed error (cm) |
|---:|---:|---:|---:|
| 1 | 63.2 | ~61.0 | ~+2.2 |
| 2 | 61.6 | 63.0 | -1.4 |
| 3 | 61.9 | 65.0 | -3.1 |
| 4 | 63.1 | 65.0 | -1.9 |
| 5 | 61.6 | 64.0 | -2.4 |
| 6 | 62.9 | 64.5 | -1.6 |
| 8 | 62.8 | 64.5 | -1.7 |
| 9 | 62.5 | 64.0 | -1.5 |

Across the eight successful trials, mean absolute error was **0.0197 m
(approximately 2.0 cm)**. The signed error range was **-0.0310 to +0.0216 m
(-3.1 to +2.2 cm)**, a width of **0.0526 m (5.3 cm)**. These statistics use
the unrounded estimates in `results/summary.json`. Trial 1's approximate tape
reading limits the precision of the aggregate figures.

## Discussion

All eight successful runs reached the target stop before the tag. Measured
final distances were between 61.0 and 65.0 cm, a 4.0 cm spread. Seven of the
eight signed errors were negative, which suggests a small tendency for the
camera/odometry estimate to understate the actual stopping distance in this
setup. The measured error size is consistent with the independent camera
range checks. Tape placement, printed-marker scale and stand flatness, camera
pose uncertainty, floor traction, SDK odometry error, frame timing, and motor
stop latency are plausible contributors. The brief low-speed check showed a
1.6 cm difference between tape displacement and chassis odometry; camera
correction was therefore useful for limiting accumulated prediction drift.

Prediction maintained an estimate between camera frames. Correction pulled
the estimate toward the tag-based range when a plausible fresh pose arrived.
Attempt 7 stopped early at an estimated 0.832 m after a camera-frame pause
exceeded the 0.50 s tag-age limit; the user measured about 0.85 m after that
stop. It was excluded from the eight target-stop results and demonstrates the
loss-of-tag stop. A separate Trial 2 connection attempt failed before any
motion when Windows left the RoboMaster Wi-Fi; the successful Trial 2 was
run only after reconnection. No ToF measurement is claimed in these results.

## Submission artifacts

- Code and configuration: `code/`, `config/phase3.yaml`, and launcher `.bat` files.
- Raw per-trial telemetry: `results/trial_*.csv` and `results/trial_*.json`.
- Computed result table: `results/summary.csv` and `results/summary.json`.
- Robot-camera video: `results/trial_08_camera.mp4`.
- Phone demonstration video: captured by the student and sent directly to the TA.
- GitHub repository link: pending connection/publication.

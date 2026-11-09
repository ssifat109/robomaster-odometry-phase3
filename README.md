# RoboMaster EP Core odometry - Phase 3

This project implements a fixed AprilTag 36h11 ID 3 approach with wheel/chassis
odometry prediction and camera pose correction. The course brief calls the target
a QR tag; this implementation uses the AprilTag already prepared in Phase 2.
The robot stays straight: forward chassis command only, zero lateral and yaw.

## Current status

Eight successful physical trials were completed on 10 November 2026. The
mean absolute final-distance error was about 2.0 cm; signed errors ranged
from -3.1 to +2.2 cm. Attempt 7 stopped early on stale camera frames and is
excluded from the eight target-stop trials. The report and raw results are in
`output/pdf/phase3_report.pdf`, `report.md`, and `results/`.

This setup uses the 142 mm printed black square, camera surveys at 0.57 and
1.50 m, and independent 0.40 and 1.45 m checks. The 0.40 m check had -0.038 m
error; the chosen target stop is therefore 0.55 m with an 0.08 m early-stop
guard. The old Phase 2 body transform is not used to compute range. The ToF
sensors returned zero. `operator_present` is reset to false after the trials.

## Setup and measurement

1. Print `tags/apriltag3_140mm_A4.pdf` at actual size. Measure the **black square**
   edge (measured as 0.142 m on this print). Mount the fixed tag perpendicular to the travel
   direction, with its ID 3 face visible throughout 1.5 m to the stop point.
2. Mark the centre of the robot's **front bumper**. Measure from that mark to
   the tag plane for both the initial and final distances. Keep the same floor,
   arm pose, lighting, tag position, and 1.5 m start for every trial.
3. Connect the Windows PC to RoboMaster AP Wi-Fi. Run `preflight.bat`. It does
   not move the robot. Check `results/preflight.json` and the saved frame.
4. With the arm/camera fixed, independently measure and verify camera-derived
   ranges at near (0.57 m recorded) and far (1.50 m recorded) distances. The
   stationary command `python code/phase3.py preflight --known-distance 1.50`
   saves each survey. Run `python code/fit_range.py` for a candidate camera-axis
   to bumper-distance map. Check that candidate at an independent third distance
   near the stop point before copying its scale and offset into the config and
   marking calibration verified. The 0.40 m independent check produced -0.038 m
   error; the selected stop is kept above 0.55 m. Confirm continuous ID 3 visibility at the
   1.5 m start and during a slow manual approach. Confirm the physical stop
   response and keep an operator beside the robot. Only then set the three
   verification fields true. Set `operator_present: true` only for attended runs.
5. Verify `start_distance_m`, `stop_distance_m`, and margins. Place the robot at
   the same start mark, set `operator_present: true` only while an operator is
   ready beside it, and run `trial.bat N` with a new trial number.
   Never reuse a trial number. The robot stops on tag loss, stale odometry,
   time limit, or the target guard. A non-target stop is not a successful trial.
6. After each stop, independently measure the bumper-to-tag distance with a
   tape. Record it in `results/measurements.csv`. Film at least one complete
   detection and approach, showing the final tape measurement.
7. Run `analyze.bat`. It computes signed error = estimated minus measured,
   mean absolute error, and minimum/maximum error. Run `build_report.bat` to
   regenerate the PDF from the recorded results.

## Method

The prediction is `d_pred = d_prev - (x_odom,new - x_odom,old)`, where x odometry
is the SDK chassis position subscription in metres. A camera frame detects the
fixed tag, estimates its pose with calibrated intrinsics and tag size, and maps
the camera-axis range to bumper-to-tag distance using stationary tape surveys.
The old Phase 2 body transform failed a height check and is not used for range.
If the pose innovation is within 0.15 m, the correction is
`d = d_pred + 0.35 * (d_tag - d_pred)`. Corrections never use the ToF because
Phase 2 observed zero readings. The estimated final distance is logged at the
stop; the measured final distance is entered separately after the run.

## Submission

The PDF report, code, and trial results are ready. The student will send the
demonstration videos directly to the TA. Publish the code to a GitHub repository
and provide its URL. Do not describe the old simulations as Phase 3 data.

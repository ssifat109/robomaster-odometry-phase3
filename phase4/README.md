# Phase 4 — Bearing-aided EKF localization

**Author:** Shakib Al Sifat  
**Student ID:** 202613880  
**Course:** Advanced Robotics (SCE 672)  
**Robot:** RoboMaster EP Core

## Submission files

- [Final report (PDF)](output/pdf/SCE672_Phase4_EKF_Localization_Report.pdf)
- [Cover image](output/covers/cover_page.png); three alternate cover designs are in the same folder.
- [Final report source](results/phase4_final_report.md), [summary data](results/summary.csv), and [figures](results/report_figures/).
- Source scripts, setup and run batch files, AprilTag print file, configuration, measurements, and trial exclusions.
- Raw event logs and robot-camera videos for the eight analyzed trials, 06–13, are in the raw and videos folders.

The command-panel screen recording is not included here; it was recorded separately by the student. Trials 01–05 are excluded from the quantitative report because they lacked comparable ground truth, did not complete, or had uncertain setup. The selected trial videos are the camera recordings corresponding to analyzed trials 06–13.

## Result

Across eight fixed-start runs, mean Euclidean endpoint error was **3.30 cm for odometry** and **6.00 cm for the EKF**. The bearing-aided EKF did not improve accuracy with the current settings and showed a systematic lateral bias. Process and bearing noise values are provisional assumptions rather than empirically calibrated values; the report discusses this limitation.

## Reproduce the analysis

From this directory in Ubuntu/WSL:

~~~bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/analyze.py
python scripts/build_report.py
~~~

The analysis replays raw odometry and AprilTag bearing events, compares final estimates with independently tape-measured endpoints, and generates the summary and figures. The report builder creates the PDF in output/pdf.

For robot operation, use the supplied batch files only with an operator beside the robot and a clear test path. The run script controls the physical robot when started without dry-run mode.

## Experiment frame

The initial chassis-center mark is the origin, +x points forward, and +y points left. The stationary AprilTag 36h11 ID 3 black square measured 0.142 m. The configuration records the tag center as (1.17 m, 0.40 m), camera geometry, initial pose, motion speed, and provisional filter noise values. See the report for setup details and caveats.

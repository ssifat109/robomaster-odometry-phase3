# Phase 4 — Bearing-Aided EKF Localization

**Author:** Shakib Al Sifat  
**Student ID:** 202613880  
**Course:** Advanced Robotics (SCE 672)  
**Robot:** RoboMaster EP Core

## Submission files

- [Final report (PDF)](output/pdf/SCE672_Phase4_EKF_Localization_Report.pdf)
- [LaTeX report source](results/SCE672_Phase4_EKF_Localization_Report.tex)
- [Cover image](output/covers/cover_page.png); three alternate covers are in the same folder.
- [Report summary](results/phase4_final_report.md), [trial summary data](results/summary.csv), and [report figures](results/report_figures/).
- Analysis source, robot setup and run batch files, AprilTag print file, configuration, endpoint measurements, and exclusion record.
- Raw robot event logs for trials 06–13 and the corresponding camera clips are in the raw and videos folders.

## Results and trial selection

I used trials 06–13 for the quantitative comparison. I excluded trials 01, 03, and 04 because they were earlier setup attempts without comparable ground truth for this fixed-start series. Trial 02 did not produce a valid run. I excluded trial 05 because its endpoint and start setup were uncertain, so I could not compare it reliably.

Across the eight analyzed runs, mean Euclidean endpoint error was **3.30 cm for odometry** and **6.00 cm for the EKF**. The current EKF settings did not improve endpoint accuracy and showed a leftward bias. The report explains that the process and bearing noise values are provisional assumptions, not empirically calibrated values.

I combined footage from my phone and the RoboMaster camera side by side in one video covering all trial attempts: [watch the video on YouTube](https://youtube.com/shorts/OIwx5EAHnV4).

## Reproduce the analysis and report

From this directory, run the analysis in Ubuntu/WSL:

~~~bash
python3 scripts/analyze.py
~~~

To compile the included LaTeX source to PDF, install Tectonic and run:

~~~bash
tectonic --outdir output/pdf results/SCE672_Phase4_EKF_Localization_Report.tex
~~~

The generated PDF is written to output/pdf. The LaTeX source uses the bundled report figures. The analysis replays the raw odometry and AprilTag bearing events and compares final estimates with independently tape-measured chassis-center endpoints.

For robot operation, use the supplied batch files only with an operator beside the robot and a clear test path. The run script controls the physical robot when started without dry-run mode.

## Experiment frame

I used the initial chassis-center mark as the origin, +x forward, and +y left. I printed AprilTag 36h11 ID 3 with a measured black-square edge of 0.142 m. The configuration records the tag center as (1.17 m, 0.40 m), camera geometry, initial pose, motion speed, and provisional filter noise values. The PDF report contains the setup details, equations, trial table, charts, interpretation, and limitations.

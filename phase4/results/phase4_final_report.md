# Phase 4: Bearing-Aided EKF Localization

I evaluated bearing-aided EKF localization on the RoboMaster EP Core using eight fixed-start trials (06-13). My mean endpoint error was 3.30 cm for odometry and 6.00 cm for the EKF. The current EKF settings did not improve the endpoint estimate and produced a consistent leftward bias.

I excluded trials 01, 03, and 04 because they were earlier setup attempts without comparable ground truth for this fixed-start series. Trial 02 did not produce a valid run. I excluded trial 05 because its endpoint and setup were uncertain, so I could not compare it reliably. These decisions apply to the quantitative analysis; the combined YouTube video shows all trial attempts.

- Author: Shakib Al Sifat, Student ID 202613880
- Course: Advanced Robotics (SCE 672)
- [YouTube video with phone and robot-camera views side by side](https://youtube.com/shorts/OIwx5EAHnV4)
- [Phase 4 files on GitHub](https://github.com/ssifat109/robomaster-odometry-phase3/tree/main/phase4)
- [Final PDF report](../output/pdf/SCE672_Phase4_EKF_Localization_Report.pdf)
- [LaTeX source](SCE672_Phase4_EKF_Localization_Report.tex)

The full report includes the setup, EKF method, noise assumptions, per-trial data, charts, discussion, limitations, and trial-selection rationale.

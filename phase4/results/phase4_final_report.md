# SCE 672 Phase 4: Bearing-aided EKF localization

## Executive result

Eight valid fixed-start trials were analyzed. Mean Euclidean endpoint error was 3.30 cm for odometry and 6.00 cm for the EKF. The current EKF configuration performed worse on these data and shows positive-y bias.

## Per-trial results

| Trial | Actual x | Actual y | Odom x | Odom y | EKF x | EKF y | Odom error | EKF error | sigma x | sigma y |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 06 | 1.330 | -0.010 | 1.351 | 0.005 | 1.320 | 0.060 | 0.026 | 0.070 | 0.076 | 0.071 |
| 07 | 1.320 | -0.010 | 1.352 | 0.016 | 1.326 | 0.056 | 0.041 | 0.066 | 0.076 | 0.071 |
| 08 | 1.410 | -0.010 | 1.407 | 0.004 | 1.385 | 0.030 | 0.014 | 0.047 | 0.080 | 0.077 |
| 09 | 1.410 | -0.035 | 1.414 | 0.010 | 1.393 | 0.016 | 0.046 | 0.054 | 0.081 | 0.078 |
| 10 | 1.420 | -0.015 | 1.425 | 0.011 | 1.403 | 0.032 | 0.027 | 0.050 | 0.081 | 0.078 |
| 11 | 1.420 | -0.020 | 1.414 | 0.002 | 1.391 | 0.019 | 0.023 | 0.048 | 0.080 | 0.077 |
| 12 | 1.490 | -0.005 | 1.451 | 0.026 | 1.431 | 0.044 | 0.050 | 0.077 | 0.081 | 0.079 |
| 13 | 1.470 | -0.020 | 1.454 | 0.015 | 1.429 | 0.034 | 0.038 | 0.068 | 0.080 | 0.079 |

Coordinates and errors are in meters; sigma values are sqrt of final diagonal covariance entries. x is forward, y is left positive.

## Figures

See `report_figures/` for endpoint comparison, per-trial error, coordinate error versus sigma, signed residuals, error distribution, mean error with sample standard deviation, and squared-error coordinate share.

## Noise assumptions

The configuration uses provisional Q standard deviations of 7 mm forward and lateral per odometry sample and 0.5 degrees heading per sample; R uses 3 degrees bearing standard deviation. These were not empirically calibrated and should be labeled as assumptions. The Joseph covariance correction and FPF^T+Q propagation are implemented.

## Interpretation

All eight EKF x and y residual magnitudes are within their reported one-sigma values, but this is not evidence of calibrated coverage: Q and R are provisional and EKF y residuals show systematic positive bias. The bearing correction raised the mean error from 3.30 cm to 6.00 cm. Geometry, camera yaw, timestamp alignment, odometry-frame alignment, and wheel slip need calibration before claiming improvement.

## Excluded attempts

Trials 01, 03, and 04 lacked comparable complete ground truth; 02 had no valid run; 05 was excluded because the endpoint/setup was uncertain. The eight analyzed trials are 06-13.

## Submission

Author: Shakib Al Sifat (Student ID 202613880). Course: Advanced Robotics (SCE 672). Repository: https://github.com/ssifat109/robomaster-odometry-phase3/tree/main/phase4. Eight robot-camera videos for trials 06-13 are included in the repository; the separate command-panel screen recording is not included.

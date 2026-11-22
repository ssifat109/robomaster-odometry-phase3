"""Build the Phase 4 report and supporting comparison figures from measured data."""
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table,
                                TableStyle, PageBreak, KeepTogether)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'pdf'
FIG = ROOT / 'results' / 'report_figures'
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)


def load_data():
    cfg = json.loads((ROOT / 'config.json').read_text())
    with (ROOT / 'results' / 'summary.csv').open(newline='') as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k, v in list(r.items()):
            if k != 'trial':
                r[k] = float(v)
    return cfg, rows


def arr(rows, key):
    return np.array([r[key] for r in rows], dtype=float)


def make_figures(cfg, rows):
    trials = [r['trial'] for r in rows]
    actual_x, actual_y = arr(rows, 'actual_x_m'), arr(rows, 'actual_y_m')
    odom_x, odom_y = arr(rows, 'odom_x_m'), arr(rows, 'odom_y_m')
    ekf_x, ekf_y = arr(rows, 'ekf_x_m'), arr(rows, 'ekf_y_m')
    odom_e, ekf_e = arr(rows, 'odom_error_m'), arr(rows, 'ekf_error_m')
    odom_dx, odom_dy = odom_x-actual_x, odom_y-actual_y
    ekf_dx, ekf_dy = ekf_x-actual_x, ekf_y-actual_y
    plt.rcParams.update({'font.size': 9, 'axes.titlesize': 12, 'figure.facecolor': 'white'})

    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    ax.plot([0, 1.5], [0, 0], color='#aab4c0', lw=1, ls=':', label='nominal straight path')
    ax.scatter(actual_x, actual_y, marker='x', s=70, c='#222f3e', label='tape-measured endpoints', zorder=5)
    ax.scatter(odom_x, odom_y, marker='o', s=34, facecolors='none', edgecolors='#2584c5', label='odometry endpoints')
    ax.scatter(ekf_x, ekf_y, marker='s', s=34, facecolors='none', edgecolors='#e17c35', label='EKF endpoints')
    ax.scatter([cfg['tag_x_m']], [cfg['tag_y_m']], marker='^', s=95, c='#d64545', label='tag center')
    for i, t in enumerate(trials):
        ax.plot([actual_x[i], odom_x[i]], [actual_y[i], odom_y[i]], color='#2584c5', alpha=.25, lw=.8)
        ax.plot([actual_x[i], ekf_x[i]], [actual_y[i], ekf_y[i]], color='#e17c35', alpha=.30, lw=.8)
        ax.annotate(t, (actual_x[i], actual_y[i]), xytext=(3, 3), textcoords='offset points', fontsize=7)
    ax.set(xlabel='x from start (m)', ylabel='y, left positive (m)', title='Measured and estimated final positions')
    ax.grid(alpha=.25); ax.axis('equal'); ax.legend(fontsize=8, ncol=2, loc='upper left')
    fig.tight_layout(); fig.savefig(FIG/'endpoints.png', dpi=200); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.2, 4.7)); x=np.arange(len(rows)); w=.36
    ax.bar(x-w/2, odom_e*100, w, label='Odometry', color='#2584c5')
    ax.bar(x+w/2, ekf_e*100, w, label='EKF', color='#e17c35')
    ax.axhline(np.mean(odom_e)*100, color='#2584c5', ls='--', lw=1, label=f'Odometry mean {np.mean(odom_e)*100:.2f} cm')
    ax.axhline(np.mean(ekf_e)*100, color='#e17c35', ls='--', lw=1, label=f'EKF mean {np.mean(ekf_e)*100:.2f} cm')
    ax.set_xticks(x, trials); ax.set(xlabel='Trial', ylabel='Euclidean position error (cm)', title='Position error by trial')
    ax.grid(axis='y', alpha=.25); ax.legend(fontsize=8, ncol=2); fig.tight_layout(); fig.savefig(FIG/'position_errors.png', dpi=200); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.2, 4.7)); x=np.arange(len(rows)); w=.19
    for off, vals, lab, col in [(-1.5*w,np.abs(odom_dx)*100,'Odometry |x error|','#2584c5'),(-.5*w,np.abs(odom_dy)*100,'Odometry |y error|','#75b7e5'),(.5*w,np.abs(ekf_dx)*100,'EKF |x error|','#e17c35'),(1.5*w,np.abs(ekf_dy)*100,'EKF |y error|','#f3b27e')]:
        ax.bar(x+off, vals, w, label=lab, color=col)
    ax.errorbar(x+.5*w, arr(rows,'ekf_sigma_x_m')*100, yerr=0, fmt='D', ms=4, color='#873e12', label='EKF sigma x')
    ax.errorbar(x+1.5*w, arr(rows,'ekf_sigma_y_m')*100, yerr=0, fmt='D', ms=4, color='#502d1d', label='EKF sigma y')
    ax.set_xticks(x,trials); ax.set(xlabel='Trial',ylabel='Absolute coordinate error / sigma (cm)',title='Coordinate errors compared with EKF one-sigma values')
    ax.grid(axis='y',alpha=.25); ax.legend(fontsize=7,ncol=3); fig.tight_layout(); fig.savefig(FIG/'coordinate_sigma.png',dpi=200); plt.close(fig)

    fig, ax=plt.subplots(figsize=(8.2,4.7));
    ax.axhline(0,color='#555',lw=1)
    ax.scatter(odom_dx*100,odom_dy*100,s=55,label='Odometry',color='#2584c5')
    ax.scatter(ekf_dx*100,ekf_dy*100,s=55,label='EKF',color='#e17c35',marker='s')
    for i,t in enumerate(trials):
        ax.annotate(t,(ekf_dx[i]*100,ekf_dy[i]*100),xytext=(3,2),textcoords='offset points',fontsize=7)
    ax.set(xlabel='x error: estimate - measured (cm)',ylabel='y error: estimate - measured (cm)',title='Signed endpoint residuals')
    ax.grid(alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(FIG/'residuals.png',dpi=200); plt.close(fig)

    fig, ax=plt.subplots(figsize=(7.6,4.6))
    ax.boxplot([odom_e*100,ekf_e*100],tick_labels=['Odometry','EKF'],patch_artist=True,
               boxprops={'facecolor':'#dcecf8'},medianprops={'color':'#192a3a','linewidth':2})
    for j, vals, col in [(1,odom_e*100,'#2584c5'),(2,ekf_e*100,'#e17c35')]:
        ax.scatter(np.full(len(vals),j)+np.linspace(-.07,.07,len(vals)),vals,s=24,color=col,zorder=3)
    ax.set(ylabel='Euclidean position error (cm)',title='Error distribution across eight repeated trials')
    ax.grid(axis='y',alpha=.25); fig.tight_layout(); fig.savefig(FIG/'error_distribution.png',dpi=200); plt.close(fig)

    fig, ax=plt.subplots(figsize=(7.6,4.6))
    means=np.array([np.mean(odom_e),np.mean(ekf_e)])*100
    sds=np.array([np.std(odom_e,ddof=1),np.std(ekf_e,ddof=1)])*100
    ax.bar(['Odometry','EKF'],means,yerr=sds,capsize=6,color=['#2584c5','#e17c35'],alpha=.9)
    for i,v in enumerate(means): ax.text(i,v+.15,f'{v:.2f} cm',ha='center',fontweight='bold')
    ax.set(ylabel='Mean Euclidean position error (cm)',title='Mean error with one sample standard deviation',ylim=(0,max(means+sds)*1.35))
    ax.grid(axis='y',alpha=.25); fig.tight_layout(); fig.savefig(FIG/'mean_error.png',dpi=200); plt.close(fig)

    # A composition chart with a direct interpretation: each method's summed
    # squared endpoint residual split into x and y contributions.
    fig, axs=plt.subplots(1,2,figsize=(8.2,4.2))
    for ax, dx,dy,title,col in [(axs[0],odom_dx,odom_dy,'Odometry squared-error share','#2584c5'),(axs[1],ekf_dx,ekf_dy,'EKF squared-error share','#e17c35')]:
        sx=np.sum(dx**2); sy=np.sum(dy**2)
        ax.pie([sx,sy],labels=[f'x: {sx/(sx+sy):.0%}',f'y: {sy/(sx+sy):.0%}'],startangle=90,
               colors=[col,'#b9c7d3'],wedgeprops={'edgecolor':'white','linewidth':2})
        ax.set_title(title)
    fig.suptitle('Share of total squared position error by coordinate')
    fig.tight_layout(); fig.savefig(FIG/'error_share.png',dpi=200); plt.close(fig)


def report(cfg, rows):
    make_figures(cfg, rows)
    xsig=arr(rows,'ekf_sigma_x_m'); ysig=arr(rows,'ekf_sigma_y_m')
    odom_e=arr(rows,'odom_error_m'); ekf_e=arr(rows,'ekf_error_m')
    odx=arr(rows,'odom_x_m')-arr(rows,'actual_x_m'); ody=arr(rows,'odom_y_m')-arr(rows,'actual_y_m')
    ex=arr(rows,'ekf_x_m')-arr(rows,'actual_x_m'); ey=arr(rows,'ekf_y_m')-arr(rows,'actual_y_m')
    mean_odom,mean_ekf=np.mean(odom_e),np.mean(ekf_e)
    all_x_inside=int(np.sum(np.abs(ex)<=xsig)); all_y_inside=int(np.sum(np.abs(ey)<=ysig))
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleX',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=23,leading=28,textColor=colors.HexColor('#17324d'),alignment=TA_LEFT,spaceAfter=10))
    styles.add(ParagraphStyle(name='Sub',parent=styles['Normal'],fontSize=10,leading=14,textColor=colors.HexColor('#536477'),spaceAfter=14))
    styles.add(ParagraphStyle(name='H1x',parent=styles['Heading1'],fontSize=15,leading=19,textColor=colors.HexColor('#17324d'),spaceBefore=8,spaceAfter=7))
    styles.add(ParagraphStyle(name='H2x',parent=styles['Heading2'],fontSize=11,leading=14,textColor=colors.HexColor('#2373a5'),spaceBefore=6,spaceAfter=4))
    styles.add(ParagraphStyle(name='BodyX',parent=styles['BodyText'],fontSize=9.2,leading=13,spaceAfter=6))
    styles.add(ParagraphStyle(name='SmallX',parent=styles['BodyText'],fontSize=7.4,leading=9))
    styles.add(ParagraphStyle(name='CodeX',parent=styles['BodyText'],fontName='Courier',fontSize=8.4,leading=12,leftIndent=12,backColor=colors.HexColor('#f2f5f8'),borderPadding=6,spaceBefore=3,spaceAfter=8))
    styles.add(ParagraphStyle(name='Callout',parent=styles['BodyText'],fontSize=10,leading=14,backColor=colors.HexColor('#edf5fa'),borderColor=colors.HexColor('#9ac3db'),borderWidth=.6,borderPadding=8,spaceBefore=7,spaceAfter=9))
    story=[]
    story += [Spacer(1,.35*inch),Paragraph('ROBOMASTER EP CORE',styles['Sub']),Paragraph('Phase 4: Bearing-aided EKF localization',styles['TitleX']),Paragraph('Advanced Robotics (SCE 672) | King Fahd University of Petroleum and Minerals | 22 November 2026',styles['Sub']),Paragraph('<b>Prepared by:</b> Shakib Al Sifat &nbsp;&nbsp; <b>Student ID:</b> 202613880',styles['Sub']),Spacer(1,.18*inch)]
    story.append(Paragraph(f'<b>Result at a glance.</b> Eight repeated straight-line trials were completed. Mean endpoint position error was <b>{mean_odom*100:.2f} cm for odometry</b> and <b>{mean_ekf*100:.2f} cm for the EKF</b>. In this experiment, the bearing updates did not improve final position accuracy; the implemented EKF developed a consistent positive-y (left) bias.',styles['Callout']))
    story.append(Paragraph('This report uses the eight fixed-start measured trials 06-13. Trials 01, 03, and 04 were earlier setup attempts without comparable complete ground truth; trial 02 stopped before a run; trial 05 was excluded at the student’s request because its endpoint/setup was uncertain. The pilot was for checking motion direction and is not included.',styles['BodyX']))
    story.append(Paragraph('Contents',styles['H1x']))
    story.append(Paragraph('1. Objective and setup &nbsp;&nbsp; 2. EKF method &nbsp;&nbsp; 3. Noise assumptions &nbsp;&nbsp; 4. Results &nbsp;&nbsp; 5. Discussion & limitations &nbsp;&nbsp; 6. Reproducibility and submission checklist',styles['BodyX']))
    story.append(Image(str(FIG/'endpoints.png'),width=6.9*inch,height=4.2*inch)); story.append(Paragraph('Figure 1. Measured endpoint versus odometry and EKF endpoint estimates. The tag is beside the straight path.',styles['SmallX']))
    story.append(PageBreak())

    story.append(Paragraph('1. Objective and experimental setup',styles['H1x']))
    story.append(Paragraph('The experiment evaluates whether a camera bearing measurement to a fixed landmark can correct position and heading drift accumulated by chassis odometry. The robot drives in a straight line past a stationary tag. The same initial chassis-center mark, heading, tag position, speed, and run duration were used for trials 06-13.',styles['BodyX']))
    setup=[['Item','Value used'],['Robot / connection','RoboMaster EP Core; DJI SDK, AP connection'],['Motion','Straight forward; commanded speed 0.10 m/s; duration 13.5 s'],['Nominal odometry travel','Approximately 1.35 m; actual movement varies by trial'],['Coordinate frame','Origin at chassis center at start; +x forward; +y left; heading 0 along run line'],['Tag','AprilTag 36h11 ID 3; measured black square 0.142 m'],['Tag center entered in config','(1.17 m, 0.40 m) in the floor frame'],['Camera offset / yaw in config','x = -0.03 m; yaw correction = 0.0271 rad'],['Independent endpoint','Tape measurement of chassis center, recorded after each run']]
    story.append(make_table(setup,[1.75*inch,5.05*inch],styles))
    story.append(Paragraph('The student reported the tag was 1.20 m forward and 0.40 m left relative to the camera at the starting pose. With the camera approximately 0.03 m behind the chassis-center origin, the configuration uses tag x = 1.17 m. A stationary camera preflight detected tag ID 3 in 357/357 frames; observed bearing was 17.27 degrees, compared with a configured geometry prediction of 16.88 degrees. The camera bearing standard deviation reported in that short preflight was 0.01 degrees; this is a frame-to-frame repeatability measure, not an independent absolute calibration.',styles['BodyX']))
    story.append(Paragraph('The assignment asks for a defined and recorded path and start conditions. The path was recorded as straight, with initial position (0,0), heading 0, the tag beside the path, and one robot-camera recording for each successful take. Endpoint ground truth is based on the student’s post-run tape measurements.',styles['BodyX']))

    story.append(Paragraph('2. EKF method',styles['H1x']))
    story.append(Paragraph('The state is s = [x, y, theta]^T. Between measurements, the filter predicts with odometry increments expressed in the robot body frame:',styles['BodyX']))
    story.append(Paragraph('x(k+1) = x(k) + cos(theta) d_f - sin(theta) d_l<br/>y(k+1) = y(k) + sin(theta) d_f + cos(theta) d_l<br/>theta(k+1) = wrap(theta(k) + d_theta)',styles['CodeX']))
    story.append(Paragraph('The covariance prediction uses the motion Jacobian F and process-noise covariance Q: P- = F P F^T + Q (13B.3). The predicted bearing to tag (x_t,y_t) is h(s) = atan2(y_t-y, x_t-x) - theta - camera_yaw, with the configured camera translation included in the geometry. The scalar innovation is wrapped to [-pi,pi).',styles['BodyX']))
    story.append(Paragraph('For H = dh/ds, measurement variance R, and innovation covariance S = H P- H^T + R, the Kalman gain is K = P- H^T S^-1 (13A.4). The state update is s = s- + K innovation. Covariance correction uses the Joseph form P = (I-KH)P-(I-KH)^T + K R K^T (13A.5), then symmetrizes P numerically. The implementation uses analytical Jacobians.',styles['BodyX']))
    story.append(Paragraph('Odometry-only results propagate the initial floor-frame position using odometry, without bearing corrections. EKF final estimates are the last state after replaying timestamped odometry and detected tag bearings.',styles['BodyX']))

    story.append(PageBreak())
    story.append(Paragraph('3. Noise assumptions and uncertainty',styles['H1x']))
    Q=[cfg['motion_std_x_m_per_step']**2,cfg['motion_std_y_m_per_step']**2,math.radians(cfg['motion_std_heading_deg_per_step'])**2]
    R=math.radians(cfg['bearing_std_deg'])**2
    nv=[['Term','Configured standard deviation','Covariance value','Status / basis'],['Odometry forward increment','7 mm per sample',f'{Q[0]:.3g} m^2','Provisional engineering setting; not obtained from a dedicated calibration run'],['Odometry lateral increment','7 mm per sample',f'{Q[1]:.3g} m^2','Provisional engineering setting; not obtained from a dedicated calibration run'],['Odometry heading increment','0.5 deg per sample',f'{Q[2]:.3g} rad^2','Provisional engineering setting; not obtained from a dedicated calibration run'],['Camera bearing','3 deg',f'{R:.3g} rad^2','Conservative provisional value; exceeds observed stationary frame scatter to allow for calibration and detection effects']]
    story.append(make_table(nv,[1.35*inch,1.3*inch,1.0*inch,3.15*inch],styles))
    story.append(Paragraph('These Q and R values are declared and used in the implementation, but they were not empirically calibrated from repeated motion-noise and bearing-noise datasets. They must therefore be described as provisional assumptions, not measured sensor specifications. The final reported one-sigma values are sqrt(Pxx) and sqrt(Pyy) from the filter covariance after the last update. They are conditional model uncertainties; the persistent residual bias indicates that the covariance model does not capture all observed error.',styles['Callout']))
    story.append(Paragraph('4. Results',styles['H1x']))
    story.append(Paragraph(f'Across n = {len(rows)} measured runs, mean odometry error was {mean_odom*100:.2f} cm (sample SD {np.std(odom_e,ddof=1)*100:.2f} cm; RMSE {np.sqrt(np.mean(odom_e**2))*100:.2f} cm). Mean EKF error was {mean_ekf*100:.2f} cm (sample SD {np.std(ekf_e,ddof=1)*100:.2f} cm; RMSE {np.sqrt(np.mean(ekf_e**2))*100:.2f} cm). Here position error is Euclidean distance between final estimate and tape-measured final chassis center.',styles['BodyX']))
    story.append(Image(str(FIG/'position_errors.png'),width=6.8*inch,height=3.9*inch)); story.append(Paragraph('Figure 2. Euclidean endpoint error by trial; dashed lines mark the method means.',styles['SmallX']))
    story.append(Image(str(FIG/'mean_error.png'),width=6.2*inch,height=3.7*inch)); story.append(Paragraph('Figure 3. Mean Euclidean error; error bars are one sample standard deviation across trials.',styles['SmallX']))
    comparison=[['Summary measure','Odometry','EKF'],
                ['Mean absolute x error',f'{np.mean(np.abs(odx))*100:.2f} cm',f'{np.mean(np.abs(ex))*100:.2f} cm'],
                ['Mean absolute y error',f'{np.mean(np.abs(ody))*100:.2f} cm',f'{np.mean(np.abs(ey))*100:.2f} cm'],
                ['Mean signed x residual',f'{np.mean(odx)*100:.2f} cm',f'{np.mean(ex)*100:.2f} cm'],
                ['Mean signed y residual',f'{np.mean(ody)*100:.2f} cm',f'{np.mean(ey)*100:.2f} cm'],
                ['Mean Euclidean error',f'{mean_odom*100:.2f} cm',f'{mean_ekf*100:.2f} cm'],
                ['Euclidean RMSE',f'{np.sqrt(np.mean(odom_e**2))*100:.2f} cm',f'{np.sqrt(np.mean(ekf_e**2))*100:.2f} cm'],
                ['Mean final sigma x / y','- ',f'{np.mean(xsig)*100:.2f} / {np.mean(ysig)*100:.2f} cm'],
                ['Coordinate errors within 1 sigma','- ',f'x {all_x_inside}/8; y {all_y_inside}/8']]
    story.append(Spacer(1,8)); story.append(Paragraph('Table 2. Aggregate comparison across the eight runs',styles['H2x']))
    story.append(make_table(comparison,[2.7*inch,1.7*inch,2.4*inch],styles))
    story.append(PageBreak())

    story.append(Paragraph('Table 1. Per-trial final positions, errors, and EKF uncertainty',styles['H2x']))
    header=['Run','Actual x','Actual y','Odom x','Odom y','EKF x','EKF y','Err O','Err E','sigma x','sigma y']
    data=[header]
    for r in rows:
        data.append([r['trial'],*[f'{r[k]:.3f}' for k in ['actual_x_m','actual_y_m','odom_x_m','odom_y_m','ekf_x_m','ekf_y_m','odom_error_m','ekf_error_m','ekf_sigma_x_m','ekf_sigma_y_m']]])
    story.append(make_table(data,[.48*inch]+[.62*inch]*10,styles,small=True))
    story.append(Paragraph('All positions and errors are in meters; sigma values are meters. Err O and Err E are Euclidean errors. x is forward, y is left positive. Negative y values indicate right of the path.',styles['SmallX']))
    story.append(Spacer(1,8))
    story.append(Image(str(FIG/'coordinate_sigma.png'),width=6.9*inch,height=4.0*inch)); story.append(Paragraph('Figure 4. Absolute coordinate residuals and final EKF one-sigma uncertainty values.',styles['SmallX']))
    story.append(PageBreak())

    story.append(Paragraph('5. Residuals, uncertainty, and discussion',styles['H1x']))
    story.append(Image(str(FIG/'residuals.png'),width=6.5*inch,height=3.8*inch)); story.append(Paragraph('Figure 5. Signed endpoint residuals (estimate minus tape measurement).',styles['SmallX']))
    story.append(Image(str(FIG/'error_distribution.png'),width=5.8*inch,height=3.5*inch)); story.append(Paragraph('Figure 6. Distribution of Euclidean errors. With eight trials, treat the box summaries as descriptive only.',styles['SmallX']))
    story.append(Paragraph(f'The mean signed EKF x residual was {np.mean(ex)*100:.2f} cm and mean signed y residual was {np.mean(ey)*100:.2f} cm. Since +y points left, the positive EKF y residual means the filter placed the robot too far left on average. The odometry mean signed residuals were {np.mean(odx)*100:.2f} cm in x and {np.mean(ody)*100:.2f} cm in y. The mean error grew by {(mean_ekf/mean_odom-1)*100:.0f}% when using this EKF configuration compared with odometry alone.',styles['BodyX']))
    story.append(Paragraph(f'Every measured x residual magnitude was within its reported EKF one-sigma x value ({all_x_inside}/{len(rows)}), and every y residual magnitude was within its one-sigma y value ({all_y_inside}/{len(rows)}). This does not establish calibrated coverage: the trial count is small, the assumed Q and R are provisional, and the residuals show a systematic positive-y bias. A centered, calibrated uncertainty model should not routinely hide a directional bias inside a broad sigma.',styles['BodyX']))
    story.append(Image(str(FIG/'error_share.png'),width=6.2*inch,height=3.2*inch)); story.append(Paragraph('Figure 7. Share of summed squared endpoint residual attributable to x and y, separately for each method.',styles['SmallX']))
    story.append(Paragraph('The bearing measurement contains useful geometric information: as the robot moves past the fixed tag, the line of sight changes and the filter can adjust lateral position and heading. The Kalman gain sets the size and direction of each correction from the relative predicted and measured uncertainties. Covariance propagation increases uncertainty during motion; measurement correction reduces uncertainty along the observed direction. Here, the final EKF covariance was roughly 8 cm per coordinate, while observed mean position error was 6 cm. However, the bearing updates also introduced leftward displacement in all eight final estimates, so the current geometry or measurement timing/model bias outweighed the expected benefit.',styles['BodyX']))
    story.append(Paragraph('Likely error sources include camera intrinsic and yaw calibration, uncertainty in tag and camera offsets, the conversion from image center to bearing, camera/odometry timestamp alignment, robot heading reference and yaw drift, floor friction and wheel slip, starting alignment, and tape measurement precision. The endpoint variation also includes run-to-run speed and stop variation. A follow-up calibration should measure camera yaw and tag coordinates in a surveyed floor frame, estimate bearing noise from independent poses rather than repeated identical frames, and estimate odometry Q from repeated stationary and controlled-motion segments. Then compare NIS/innovation behavior and endpoint residuals before retuning Q and R.',styles['BodyX']))

    story.append(PageBreak())
    story.append(Paragraph('6. Reproducibility and submission checklist',styles['H1x']))
    story.append(Paragraph('The eight analyzed runs are 06-13. Raw event logs are stored under raw/, and the robot camera videos are under videos/. The analysis script regenerates the summary table and trajectory plot; this report builder generates the figures and PDF.',styles['BodyX']))
    videos=[['Trial','Camera video'],*[[r['trial'],f"videos/trial_{int(r['trial']):02d}_camera.mp4"] for r in rows]]
    story.append(make_table(videos,[1.2*inch,5.7*inch],styles))
    story.append(Paragraph('Submission files: the project source, report, result figures, raw event logs, and eight robot-camera videos for trials 06-13 are included in the GitHub repository at <link href="https://github.com/ssifat109/robomaster-odometry-phase3/tree/main/phase4" color="#2373a5">github.com/ssifat109/robomaster-odometry-phase3/tree/main/phase4</link>. A separate screen recording of the command panel is not included in this repository.',styles['Callout']))
    story.append(Paragraph('Reproduction commands (Ubuntu 24.04 WSL, from project folder):<br/><font name="Courier">~/.venvs/robomaster4/bin/python scripts/analyze.py</font><br/><font name="Courier">~/.venvs/robomaster4/bin/python scripts/build_report.py</font>',styles['BodyX']))
    story.append(Paragraph('Limitations: eight trials are a modest sample; two trials had slightly different forward endpoints (including 1.49 m), so this represents a repeated setup and commanded motion rather than an exactly identical realized displacement. Trial 05 and earlier attempts were excluded from the main comparison for documented reasons. No result is fabricated to make EKF outperform odometry.',styles['BodyX']))

    pdf_path=OUT/'SCE672_Phase4_EKF_Localization_Report.pdf'
    doc=SimpleDocTemplate(str(pdf_path),pagesize=letter,rightMargin=.65*inch,leftMargin=.65*inch,topMargin=.62*inch,bottomMargin=.58*inch,title='Advanced Robotics (SCE 672) Phase 4 EKF Localization Report',author='Shakib Al Sifat | Student ID 202613880')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    markdown_path=ROOT/'results'/'phase4_final_report.md'
    markdown_path.write_text(make_markdown(cfg,rows),encoding='utf-8')
    print(pdf_path)
    print(markdown_path)


def make_table(data,widths,styles,small=False):
    cell='SmallX' if small else 'BodyX'
    formatted=[]
    for ri,row in enumerate(data):
        formatted.append([Paragraph(str(v),styles['SmallX'] if (small or ri==0) else styles['BodyX']) for v in row])
    t=Table(formatted,colWidths=widths,repeatRows=1 if len(data)>2 else 0,hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17324d')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#d2dbe4')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f7fa')]),
        ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))
    return t


def footer(canvas,doc):
    canvas.saveState(); w,h=letter
    canvas.setStrokeColor(colors.HexColor('#d6e0e8')); canvas.line(.65*inch,.46*inch,w-.65*inch,.46*inch)
    canvas.setFont('Helvetica',7.5); canvas.setFillColor(colors.HexColor('#647487'))
    canvas.drawString(.65*inch,.30*inch,'SCE 672 | Phase 4 | Bearing-aided EKF localization')
    canvas.drawRightString(w-.65*inch,.30*inch,f'{doc.page}')
    canvas.restoreState()


def make_markdown(cfg,rows):
    lines=['# SCE 672 Phase 4: Bearing-aided EKF localization','',
           '## Executive result','',
           f"Eight valid fixed-start trials were analyzed. Mean Euclidean endpoint error was {np.mean(arr(rows,'odom_error_m'))*100:.2f} cm for odometry and {np.mean(arr(rows,'ekf_error_m'))*100:.2f} cm for the EKF. The current EKF configuration performed worse on these data and shows positive-y bias.",'',
           '## Per-trial results','',
           '| Trial | Actual x | Actual y | Odom x | Odom y | EKF x | EKF y | Odom error | EKF error | sigma x | sigma y |','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append('| '+r['trial']+' | '+' | '.join(f"{r[k]:.3f}" for k in ['actual_x_m','actual_y_m','odom_x_m','odom_y_m','ekf_x_m','ekf_y_m','odom_error_m','ekf_error_m','ekf_sigma_x_m','ekf_sigma_y_m'])+' |')
    lines += ['', 'Coordinates and errors are in meters; sigma values are sqrt of final diagonal covariance entries. x is forward, y is left positive.', '',
              '## Figures','', 'See `report_figures/` for endpoint comparison, per-trial error, coordinate error versus sigma, signed residuals, error distribution, mean error with sample standard deviation, and squared-error coordinate share.', '',
              '## Noise assumptions','',
              'The configuration uses provisional Q standard deviations of 7 mm forward and lateral per odometry sample and 0.5 degrees heading per sample; R uses 3 degrees bearing standard deviation. These were not empirically calibrated and should be labeled as assumptions. The Joseph covariance correction and FPF^T+Q propagation are implemented.', '',
              '## Interpretation','',
              'All eight EKF x and y residual magnitudes are within their reported one-sigma values, but this is not evidence of calibrated coverage: Q and R are provisional and EKF y residuals show systematic positive bias. The bearing correction raised the mean error from 3.30 cm to 6.00 cm. Geometry, camera yaw, timestamp alignment, odometry-frame alignment, and wheel slip need calibration before claiming improvement.', '',
              '## Excluded attempts','', 'Trials 01, 03, and 04 lacked comparable complete ground truth; 02 had no valid run; 05 was excluded because the endpoint/setup was uncertain. The eight analyzed trials are 06-13.', '',
              '## Submission','', 'Author: Shakib Al Sifat (Student ID 202613880). Course: Advanced Robotics (SCE 672). Repository: https://github.com/ssifat109/robomaster-odometry-phase3/tree/main/phase4. Eight robot-camera videos for trials 06-13 are included in the repository; the separate command-panel screen recording is not included.']
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    c,r=load_data(); report(c,r)

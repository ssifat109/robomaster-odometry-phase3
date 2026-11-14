"""Build the Phase 3 submission report from measured CSV/JSON evidence."""
import json
from pathlib import Path

import cv2
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                               TableStyle, Image, PageBreak, KeepTogether)

root = Path(__file__).resolve().parents[1]
summary = json.loads((root / "results" / "summary.json").read_text(encoding="utf-8"))
assert summary["trials"] == 9
out_dir = root / "output" / "pdf"
out_dir.mkdir(parents=True, exist_ok=True)
out = out_dir / "phase3_report.pdf"
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"],
                          fontName="Helvetica-Bold", fontSize=19, leading=23,
                          textColor=colors.HexColor("#12324A"), spaceAfter=10))
styles.add(ParagraphStyle(name="Deck", parent=styles["Normal"],
                          fontSize=10, leading=14, alignment=TA_CENTER,
                          textColor=colors.HexColor("#3B5262"), spaceAfter=12))
styles.add(ParagraphStyle(name="BodyCopy", parent=styles["BodyText"],
                          fontSize=9.2, leading=13.5, spaceAfter=7))
styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"],
                          fontName="Helvetica-Bold", fontSize=11.5, leading=15,
                          textColor=colors.HexColor("#12324A"), spaceBefore=12,
                          spaceAfter=6))
styles.add(ParagraphStyle(name="Small", parent=styles["Normal"],
                          fontSize=8, leading=11, textColor=colors.HexColor("#4B5D68")))

doc = SimpleDocTemplate(str(out), pagesize=A4, rightMargin=1.8*cm,
                        leftMargin=1.8*cm, topMargin=1.7*cm, bottomMargin=1.7*cm)
story = []
def p(text, style="BodyCopy"):
    story.append(Paragraph(text, styles[style]))
def section(name):
    p(name, "Section")

p("RoboMaster Odometry - Phase 3", "ReportTitle")
p("SCE-672 Advanced Robotics | Professor Aamer Iqbal Bhatti<br/>"
  "Md. Shakib Al Sifat | 202613880 | 10 and 14 November 2026", "Deck")
section("Objective and setup")
p("The RoboMaster EP Core detected a fixed tag and drove straight toward it from "
  "the same <b>1.50 m</b> starting distance on nine successful trials. The robot "
  "stopped before the tag. Each post-stop estimated distance was compared with "
  "an independently taped distance from the <b>front bumper centre to the tag's "
  "flat front plane</b>.")
p("The target was an upright AprilTag 36h11, ID 3, on a cardboard stand. Its "
  "measured black square was 0.142 m wide; its lower edge was about 0.01 m above "
  "the floor, giving an approximate centre height of 0.081 m. The tag, arm/camera "
  "pose, floor, and starting mark remained fixed. The nominal stop distance was "
  "0.55 m, with a 0.08 m early-stop guard, so the robot stopped near an estimated "
  "0.63 m. Forward speed was limited to 0.10 m/s; lateral and yaw commands were zero.")
section("Camera measurement and calibration")
p("OpenCV located ID 3 in 1280 x 720 frames and used its four corners, calibrated "
  "intrinsics, the measured square size, and IPPE square PnP to estimate camera-axis "
  "depth. The camera read the newest available frame. Two independently taped "
  "stationary placements mapped camera depth to bumper-to-tag distance:")
p("<b>d_camera = 0.97387735 x camera_axis_depth - 0.23056594</b> (metres).")
p("The calibration pairs were 0.57 m tape / 0.8220 m depth and 1.50 m tape / "
  "1.7770 m depth. Independent checks gave 0.3621 m against a 0.40 m tape "
  "reading (-0.0379 m) and 1.4776 m against 1.45 m (+0.0276 m). The conservative "
  "stop keeps the robot away from the closer range where the error grew. The "
  "older Phase 2 body transform failed a physical height check and was not used "
  "to calculate the forward-range correction; it remained in the detector "
  "as compatibility metadata and a forward-facing filter. "
  "Prior ToF readings were zero, so <b>ToF was not used</b> for correction.")
section("Prediction, correction, and stopping")
p("The SDK chassis-position subscription supplied forward odometry at 20 Hz. "
  "For odometry increment delta_x, the prediction was <b>d_pred = d_previous - "
  "delta_x</b>. A fresh camera range z corrected it as <b>d_new = d_pred + "
  "0.35(z - d_pred)</b> if the innovation magnitude was at most 0.15 m. Otherwise "
  "the prediction was retained. Commands stopped on target guard, tag age over "
  "0.50 s, odometry age over 0.30 s, or a 25 s time limit. A short post-stop "
  "sensing interval supplied the final estimate at the stopped pose.")
section("Preflight")
p("Stationary detection succeeded in 86/86 frames at 0.57 m, 113/113 at 1.50 m, "
  "and 111/111 at 0.40 m. A brief attended 0.06 m/s motion command stopped "
  "normally: tape displacement was about 0.05 m, while odometry reported +0.034 m. "
  "The operator reset the bumper to 1.50 m before each successful trial and taped "
  "the final distance before moving the robot again.")
p("Before the additional Trial 10 on 14 November, a stationary preflight detected "
  "the tag in 138/138 frames and estimated 1.477 m at the 1.50 m start mark. "
  "Trial 10 then reached the target stop; the user measured 0.65 m from the "
  "front bumper centre to the tag face.")

story.append(PageBreak())
section("Nine successful trial results")
p("Signed error = estimated final distance - measured final distance. Values "
  "below are rounded to 0.1 cm. The Trial 1 tape reading was reported as "
  "'almost 61 cm'; the calculation uses 61 cm and is approximate.")
data = [["Trial", "Estimated (cm)", "Measured (cm)", "Error (cm)"]]
for row in summary["rows"]:
    trial = row["trial"]
    data.append([str(trial), f'{row["estimated_m"]*100:.1f}',
                 ("~" if trial == 1 else "") + f'{row["measured_m"]*100:.1f}',
                 ("~" if trial == 1 else "") + f'{row["error_m"]*100:+.1f}'])
table = Table(data, colWidths=[2.4*cm, 4.1*cm, 4.1*cm, 4.1*cm], repeatRows=1)
table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#12324A")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#EFF5F8")]),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("LINEBELOW", (0,-1), (-1,-1), 0.8, colors.HexColor("#8FAAB8")),
]))
story.append(table)
story.append(Spacer(1, 8))
p(f'<b>Mean absolute error:</b> {summary["mean_absolute_error_m"]*100:.1f} cm. '
  f'<b>Signed error range:</b> {summary["error_min_m"]*100:+.1f} to '
  f'{summary["error_max_m"]*100:+.1f} cm '
  f'(width {summary["error_range_width_m"]*100:.1f} cm). '
  "Statistics use the unrounded log values; the approximate first tape reading "
  "limits their precision.")

section("Discussion and exception")
p("All nine counted runs reached the target stop before the tag. The taped "
  "final distances ranged from 61.0 to 65.0 cm. Eight signed errors were "
  "negative, suggesting a small tendency to understate the actual stopping "
  "distance in this setup. Calibration/marker pose uncertainty, a slightly "
  "non-flat stand, tape placement, floor traction, odometry drift, frame timing, "
  "and motor stopping latency are plausible sources. The low-speed check "
  "showed 1.6 cm more movement by tape than by odometry. Camera correction "
  "limited prediction drift when fresh tag measurements arrived; prediction "
  "maintained the estimate between frames.")
p("Attempt 7 stopped early at an estimated 0.832 m when a camera-frame pause "
  "exceeded the 0.50 s tag-age limit; the user measured about 0.85 m. It is "
  "retained as an aborted safety-stop attempt and excluded from the nine "
  "target-stop rows. An earlier Trial 2 connection attempt failed before "
  "motion when Windows switched away from RoboMaster Wi-Fi. No ToF "
  "measurement is claimed.")

video = root / "results" / "trial_10_camera.mp4"
if video.exists():
    cap = cv2.VideoCapture(str(video))
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    image_paths = []
    tmp = root / "tmp" / "pdfs"
    tmp.mkdir(parents=True, exist_ok=True)
    for label, index in [("Start", 0), ("Near stop", max(0,count-1))]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = cap.read()
        if ok:
            path = tmp / f"trial10_{index}.jpg"
            cv2.imwrite(str(path), frame)
            image_paths.append((label, path))
    cap.release()
    if len(image_paths) == 2:
        section("Robot-camera evidence")
        p("Trial 10 camera frames show the identified tag at the start and near the "
          "stop. The MP4 contains the full approach with ID 3 and estimated "
          "distance overlays.")
        images = []
        for label, path in image_paths:
            images.append([Paragraph(label, styles["Small"]),
                           Image(str(path), width=6.8*cm, height=3.83*cm)])
        evidence = Table([[images[0][0], images[1][0]],
                          [images[0][1], images[1][1]]],
                         colWidths=[7.8*cm, 7.8*cm])
        evidence.setStyle(TableStyle([("ALIGN", (0,0), (-1,-1), "CENTER")]))
        story.append(evidence)

def report_figure(filename, caption):
    path = root / "figures" / filename
    if not path.exists():
        raise FileNotFoundError(f"Run code/make_report_graphs.py first: {path}")
    story.append(KeepTogether([
        Image(str(path), width=16.5*cm, height=7.9*cm),
        Spacer(1, 0.08*cm),
        Paragraph(caption, styles["Small"]),
        Spacer(1, 0.30*cm),
    ]))

story.append(PageBreak())
section("Motion and distance tracking")
p("The following graphs use Trial 10 raw telemetry. This run stopped "
  "at 0.622 m estimated versus 0.650 m measured. The target threshold is 0.63 m "
  "because it includes the 0.08 m guard added to the 0.55 m nominal stop.")
report_figure("01_distance_tracking.png",
  "Figure 1. Corrected range and camera-derived range versus elapsed time, with "
  "the guarded stop threshold. Source: results/trial_10.csv.")
report_figure("02_odometry_speed.png",
  "Figure 2. Logged chassis x position and commanded forward speed during "
  "Trial 10. The command values were recorded by the controller; actual wheel "
  "speed was not measured.")

story.append(PageBreak())
section("Correction and calibration")
p("The camera measurement is used only when its innovation relative to the "
  "odometry prediction is within 0.15 m. The stationary calibration chart "
  "separates the two fit points from two independent tape checks.")
report_figure("03_innovation.png",
  "Figure 3. Camera minus predicted bumper range for accepted Trial 10 "
  "corrections. Dashed lines show the +/-15 cm acceptance limit. "
  "Source: results/trial_10.csv.")
report_figure("04_calibration.png",
  "Figure 4. Camera-axis depth versus tape-measured bumper range. The 0.57 m "
  "and 1.50 m points define the line; 0.40 m and 1.45 m are held-out checks. "
  "Sources: results/preflight_*.json and config/phase3.yaml.")

story.append(PageBreak())
section("Across-trial comparison")
p("Only nine target-stop runs are included. Trial 7 was an early safety stop "
  "and is discussed on page 2. Trial 1's tape value was reported as almost "
  "61 cm, so its plotted measurement and error are approximate.")
report_figure("05_final_distances.png",
  "Figure 5. Estimated and independently measured final bumper-to-tag distance "
  "for every successful target-stop trial. Source: results/summary.csv.")
report_figure("06_final_errors.png",
  "Figure 6. Signed error is estimate minus tape measurement. Mean absolute "
  f'error (MAE) is {summary["mean_absolute_error_m"]*100:.1f} cm; '
  "the signed range is -3.1 to +2.2 cm. "
  "Source: results/summary.csv.")

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#A8BAC4"))
    canvas.line(1.8*cm, 1.25*cm, A4[0]-1.8*cm, 1.25*cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#526875"))
    canvas.drawString(1.8*cm, 0.95*cm, "SCE-672 | RoboMaster Odometry | Phase 3")
    canvas.drawRightString(A4[0]-1.8*cm, 0.95*cm, str(doc.page))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(1.8*cm, 0.65*cm,
                      "github.com/ssifat109/robomaster-odometry-phase3")
    canvas.restoreState()

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(out)

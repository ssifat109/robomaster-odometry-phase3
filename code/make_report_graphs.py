"""Create source-labeled figures for the measured Phase 3 report."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

root = Path(__file__).resolve().parents[1]
out = root / "figures"
out.mkdir(parents=True, exist_ok=True)

with (root / "results" / "trial_10.csv").open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
with (root / "results" / "summary.csv").open(newline="", encoding="utf-8") as f:
    trials = list(csv.DictReader(f))

def number(value):
    return float(value) if value not in ("", None) else np.nan

t = np.array([number(r["elapsed_s"]) for r in rows])
x = np.array([number(r["odometry_x_m"]) for r in rows])
pred = np.array([number(r["predicted_distance_m"]) for r in rows])
cam = np.array([number(r["tag_forward_distance_m"]) for r in rows])
corr = np.array([number(r["corrected_distance_m"]) for r in rows])
moving = np.array([r["phase"] == "MOVING" for r in rows])
vref = np.array([number(r["commanded_speed_m_s"]) for r in rows])

plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":9,
                     "axes.titlesize":10, "axes.labelsize":9,
                     "axes.spines.top":False, "axes.spines.right":False,
                     "figure.facecolor":"white", "axes.facecolor":"white"})
navy, blue, orange, gray = "#12324A", "#13759A", "#D36A3C", "#657A88"

def finish(fig, name):
    fig.savefig(out / name, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)

# 1. Tracking through one complete approach, including the stop-settle samples.
fig, ax = plt.subplots(figsize=(9.2, 4.4))
ax.plot(t, corr, color=blue, lw=2.2, label="Corrected estimate")
ax.scatter(t[np.isfinite(cam)], cam[np.isfinite(cam)], s=5, color=orange,
           alpha=.45, label="Camera-derived range")
ax.axhline(.63, color=navy, ls="--", lw=1.4, label="Guarded stop threshold (0.63 m)")
ax.set(xlabel="Elapsed time (s)", ylabel="Bumper-to-tag distance (m)",
       title="Trial 10 distance tracking")
ax.grid(axis="y", color="#DCE5E9", lw=.7)
ax.legend(loc="upper right", frameon=False, ncol=1)
finish(fig, "01_distance_tracking.png")

# 2. Logged chassis x and the controller's recorded speed commands.
fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4))
axes[0].plot(t, x, color=blue, lw=2.2)
axes[0].set(xlabel="Elapsed time (s)", ylabel="Chassis x (m)",
            title="Logged forward odometry")
axes[1].plot(t, vref, color=orange, lw=2.2)
axes[1].set(xlabel="Elapsed time (s)", ylabel="Speed reference (m/s)",
            title="Logged forward speed command")
for ax in axes: ax.grid(axis="y", color="#DCE5E9", lw=.7)
fig.tight_layout(w_pad=2.5)
finish(fig, "02_odometry_speed.png")

# 3. Measurement innovation and correction magnitude during Trial 10.
innovation = 100 * (cam - pred)
applied = np.isfinite(innovation) & (np.abs(innovation) <= 15)
fig, ax = plt.subplots(figsize=(9.2, 4.4))
ax.plot(t[applied], innovation[applied], color=blue, lw=1.5,
        label="Accepted camera - prediction")
ax.axhline(0, color=navy, lw=1)
ax.axhline(15, color=orange, ls="--", lw=1, label="Acceptance limit (+/-15 cm)")
ax.axhline(-15, color=orange, ls="--", lw=1)
ax.set(xlabel="Elapsed time (s)", ylabel="Innovation (cm)",
       title="Trial 10 camera correction input")
ax.grid(axis="y", color="#DCE5E9", lw=.7)
finish(fig, "03_innovation.png")

# 4. Calibration observations, separating fit points and held-out checks.
points = [
    (0.8220398, .57, "Fit: 0.57 m"),
    (1.7769855, 1.50, "Fit: 1.50 m"),
    (0.6085616303425083, .40, "Check: 0.40 m"),
    (1.7539369318932987, 1.45, "Check: 1.45 m"),
]
fig, ax = plt.subplots(figsize=(9.2, 4.4))
z = np.linspace(.6, 1.9, 200)
ax.plot(z, .973877350917005*z - .23056594406464548, color=blue, lw=2,
        label="Two-point range map")
for i,(depth,tape,label) in enumerate(points):
    ax.scatter(depth,tape,s=60,color=navy if i<2 else orange,
               marker="o" if i<2 else "D", zorder=3)
    offsets = [(8,-14),(-102,10),(8,7),(-102,-20)]
    ax.annotate(label,(depth,tape),xytext=offsets[i],
                textcoords="offset points",fontsize=8)
ax.set(xlabel="Camera-axis depth (m)",ylabel="Tape bumper-to-tag range (m)",
       title="Stationary camera range calibration and checks")
ax.grid(color="#DCE5E9",lw=.7)
ax.legend(loc="lower right",frameon=False)
finish(fig, "04_calibration.png")

# 5. Both final distances for every successful target-stop trial.
ids = [int(r["trial"]) for r in trials]
estimated = np.array([100*float(r["estimated_m"]) for r in trials])
measured = np.array([100*float(r["measured_m"]) for r in trials])
pos = np.arange(len(ids))
fig, ax = plt.subplots(figsize=(9.2, 4.4))
ax.bar(pos-.19, estimated, .38, color=blue, label="Estimate")
ax.bar(pos+.19, measured, .38, color=orange, label="Tape measurement")
ax.set(xticks=pos,xticklabels=ids,xlabel="Successful trial number",
       ylabel="Final bumper-to-tag distance (cm)",
       title="Estimated and measured final distances")
ax.set_ylim(0,72)
ax.grid(axis="y",color="#DCE5E9",lw=.7)
ax.set_axisbelow(True)
ax.legend(frameon=False,ncol=2)
finish(fig, "05_final_distances.png")

# 6. Signed error with MAE and signed range stated in the caption.
errors = np.array([100*float(r["error_m"]) for r in trials])
mae = np.mean(np.abs(errors))
fig, ax = plt.subplots(figsize=(9.2, 4.4))
ax.bar(pos, errors, .62, color=[orange if e>0 else blue for e in errors])
ax.axhline(0,color=navy,lw=1)
ax.set(xticks=pos,xticklabels=ids,xlabel="Successful trial number",
       ylabel="Estimate - tape (cm)",title="Final signed distance error by trial")
ax.set_ylim(-4,3)
ax.grid(axis="y",color="#DCE5E9",lw=.7)
ax.set_axisbelow(True)
ax.text(.98,.94,f"MAE = {mae:.1f} cm",ha="right",va="top",
        transform=ax.transAxes,fontsize=10,color=navy,weight="bold")
finish(fig, "06_final_errors.png")

print(out)

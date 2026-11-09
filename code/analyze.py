"""Summarize independently measured Phase 3 trials without inventing data."""
import csv
import json
import statistics
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "results" / "measurements.csv"
with path.open(newline="", encoding="utf-8") as stream:
    records = list(csv.DictReader(stream))
if not 8 <= len(records) <= 10:
    raise SystemExit("Enter 8 to 10 measured trials in results/measurements.csv")
rows = []
for record in records:
    trial = int(record["trial"])
    measured = float(record["measured_final_distance_m"])
    logged = json.loads((root / "results" / f"trial_{trial:02d}.json").read_text())
    if logged["stop_reason"] != "TARGET_STOP":
        raise SystemExit(f"Trial {trial} stopped for {logged['stop_reason']}; investigate before reporting")
    estimated = float(logged["estimated_final_distance_m"])
    rows.append((trial, estimated, measured, estimated-measured))
if len({r[0] for r in rows}) != len(rows):
    raise SystemExit("Duplicate trial number")
errors = [r[3] for r in rows]
mae = statistics.mean(abs(e) for e in errors)
summary = {"trials": len(rows), "mean_absolute_error_m": mae,
           "error_min_m": min(errors), "error_max_m": max(errors),
           "error_range_width_m": max(errors)-min(errors),
           "rows": [{"trial": t, "estimated_m": e, "measured_m": m, "error_m": x}
                    for t,e,m,x in rows]}
(root / "results" / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
with (root / "results" / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
    writer = csv.writer(stream)
    writer.writerow(["trial", "estimated_m", "measured_m", "error_m"])
    writer.writerows(rows)
print(json.dumps(summary, indent=2))

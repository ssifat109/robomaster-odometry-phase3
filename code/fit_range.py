"""Fit the camera-axis-to-bumper range map from two stationary tape surveys."""
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parents[1]
samples = []
for path in (root / "results").glob("preflight_*mm.json"):
    sample = json.loads(path.read_text(encoding="utf-8"))
    if sample.get("known_bumper_to_tag_m") is None:
        continue
    if sample.get("detection_fraction", 0) < 0.9:
        continue
    samples.append(sample)
if len(samples) < 2:
    raise SystemExit("Need two stationary surveys with >=90% tag detection")
near = min(samples, key=lambda s: s["known_bumper_to_tag_m"])
far = max(samples, key=lambda s: s["known_bumper_to_tag_m"])
x1, y1 = near["median_camera_forward_m"], near["known_bumper_to_tag_m"]
x2, y2 = far["median_camera_forward_m"], far["known_bumper_to_tag_m"]
if abs(x2-x1) < 0.3:
    raise SystemExit("Camera range separation too small for a stable fit")
scale = (y2-y1)/(x2-x1)
offset = y1-scale*x1
if not math.isfinite(scale) or not 0.7 < scale < 1.3:
    raise SystemExit(f"Implausible range scale {scale:.3f}; check pose and tape measurements")
candidate = {"range_scale": scale, "range_offset_m": offset,
             "near_known_m": y1, "near_camera_m": x1,
             "far_known_m": y2, "far_camera_m": x2,
             "warning": "Validate at an independent third distance before setting calibration_verified true"}
(root / "results" / "range_candidate.json").write_text(json.dumps(candidate, indent=2), encoding="utf-8")
print(json.dumps(candidate, indent=2))

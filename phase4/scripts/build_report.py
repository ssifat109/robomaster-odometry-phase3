"""Compile the Phase 4 report from its LaTeX source using Tectonic."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "SCE672_Phase4_EKF_Localization_Report.tex"
OUT = ROOT / "output" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)

tectonic = shutil.which("tectonic")
if not tectonic:
    sys.exit(
        "Tectonic was not found on PATH. Install Tectonic, then run this script again. "
        "The source is results/SCE672_Phase4_EKF_Localization_Report.tex."
    )

subprocess.run(
    [tectonic, "--outdir", str(OUT), str(SOURCE)],
    cwd=ROOT,
    check=True,
)

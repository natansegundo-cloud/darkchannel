#!/usr/bin/env python3
"""Cria um snapshot, sem sobrescrita, das dependencias e licencas locais."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENTS = {
    "narracao": ROOT / ".tts" / "venv" / "Scripts" / "python.exe",
    "comfyui": ROOT / ".comfyui" / "venv" / "Scripts" / "python.exe",
}
QUERY = r'''
import importlib.metadata as md
import json

rows = []
for dist in md.distributions():
    meta = dist.metadata
    expression = meta.get("License-Expression") or ""
    license_text = expression or meta.get("License") or ""
    if not license_text:
        classifiers = meta.get_all("Classifier") or []
        license_text = "; ".join(x for x in classifiers if x.startswith("License ::"))
    home = meta.get("Home-page") or ""
    if not home:
        for item in meta.get_all("Project-URL") or []:
            if "," in item:
                label, url = item.split(",", 1)
                if label.strip().lower() in {"homepage", "repository", "source"}:
                    home = url.strip()
                    break
    rows.append({
        "package": meta.get("Name") or dist.name,
        "version": dist.version,
        "license": " ".join(license_text.split())[:500],
        "source": home,
    })
print(json.dumps(sorted(rows, key=lambda x: x["package"].lower())))
'''


def main() -> int:
    all_rows: list[dict[str, str]] = []
    for environment, python in ENVIRONMENTS.items():
        if not python.exists():
            continue
        completed = subprocess.run(
            [str(python), "-c", QUERY],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        for row in json.loads(completed.stdout):
            row["environment"] = environment
            all_rows.append(row)

    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    output = ROOT / "docs" / f"inventario_dependencias_{stamp}.csv"
    with output.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["environment", "package", "version", "license", "source"],
        )
        writer.writeheader()
        writer.writerows(all_rows)
    print(output.relative_to(ROOT))
    print(f"{len(all_rows)} registros")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

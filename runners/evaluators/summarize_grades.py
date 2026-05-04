#!/usr/bin/env python3
"""Summarize graded model runs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "results" / "processed" / "nemotron_3_nano_4b_pilot_summary.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    groups = defaultdict(list)
    for path in args.inputs:
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            groups[(row["model"], row["format"])].append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "model",
                "format",
                "examples",
                "success_rate",
                "valid_json_rate",
                "error_rate",
                "mean_latency_seconds",
            ],
        )
        writer.writeheader()
        for (model, fmt), rows in sorted(groups.items()):
            latencies = [row["latency_seconds"] for row in rows if row.get("latency_seconds") is not None]
            writer.writerow(
                {
                    "model": model,
                    "format": fmt,
                    "examples": len(rows),
                    "success_rate": round(sum(1 for row in rows if row["success"]) / len(rows), 4),
                    "valid_json_rate": round(sum(1 for row in rows if row["valid_json"]) / len(rows), 4),
                    "error_rate": round(sum(1 for row in rows if row.get("error")) / len(rows), 4),
                    "mean_latency_seconds": round(mean(latencies), 3) if latencies else "",
                }
            )

    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()

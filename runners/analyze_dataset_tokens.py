#!/usr/bin/env python3
"""Analyze output-format token sizes for Benchmark V1."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

from tokenizers.estimate_tokens import estimate_tokens


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "datasets" / "generated" / "benchmark_v1.jsonl"
DEFAULT_OUTPUT = ROOT / "results" / "processed" / "format_token_summary.csv"
FORMATS = ["raw_cli", "rtk_style", "structured_json", "compact_json", "task_focused_json"]


def as_text(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines()]
    stats: dict[tuple[str, str], list[int]] = defaultdict(list)

    for row in rows:
        for fmt in FORMATS:
            text = as_text(row["tool_outputs"][fmt])
            stats[(row["task_id"], fmt)].append(estimate_tokens(text))
            stats[("ALL", fmt)].append(estimate_tokens(text))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["task_id", "format", "examples", "mean_tokens", "min_tokens", "max_tokens", "reduction_vs_raw_pct"],
        )
        writer.writeheader()
        for task_id in sorted({key[0] for key in stats}):
            raw_mean = mean(stats[(task_id, "raw_cli")])
            for fmt in FORMATS:
                values = stats[(task_id, fmt)]
                fmt_mean = mean(values)
                reduction = 0.0 if raw_mean == 0 else (1 - fmt_mean / raw_mean) * 100
                writer.writerow(
                    {
                        "task_id": task_id,
                        "format": fmt,
                        "examples": len(values),
                        "mean_tokens": round(fmt_mean, 2),
                        "min_tokens": min(values),
                        "max_tokens": max(values),
                        "reduction_vs_raw_pct": round(reduction, 2),
                    }
                )

    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run Benchmark V1 examples through an Ollama model."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "datasets" / "generated" / "benchmark_v1.jsonl"
DEFAULT_OUTPUT = ROOT / "results" / "raw" / "ollama_runs.jsonl"


def as_text(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def build_prompt(example: dict, fmt: str) -> str:
    tool_output = as_text(example["tool_outputs"][fmt])
    return f"""You are evaluating command-line tool output.

Answer the question using only the provided tool output.
Return only valid JSON using this shape:
{{"answer": <task-specific answer>, "confidence": "low|medium|high"}}

Question:
{example["question"]}

Tool output format: {fmt}

Tool output:
{tool_output}
"""


def run_ollama_cli(model: str, prompt: str, timeout: int) -> tuple[str, float]:
    started = time.perf_counter()
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    latency = time.perf_counter() - started
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"ollama exited with {result.returncode}")
    return result.stdout.strip(), latency


def run_ollama_api(model: str, prompt: str, timeout: int) -> tuple[str, float]:
    started = time.perf_counter()
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "keep_alive": "30m",
        "options": {
            "temperature": 0,
        },
    }
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    latency = time.perf_counter() - started
    return body.get("response", "").strip(), latency


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--format",
        required=True,
        choices=["raw_cli", "rtk_style", "structured_json", "compact_json", "task_focused_json"],
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=0, help="0 means all examples")
    parser.add_argument("--task-id", default="", help="Optional single task filter")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--backend", choices=["api", "cli"], default="api")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines()]
    if args.task_id:
        rows = [row for row in rows if row["task_id"] == args.task_id]
    if args.limit:
        rows = rows[: args.limit]

    existing_ids = set()
    if args.skip_existing and args.output.exists() and not args.overwrite:
        with args.output.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    existing_ids.add(json.loads(line)["example_id"])
                except (json.JSONDecodeError, KeyError):
                    pass
        rows = [row for row in rows if row["example_id"] not in existing_ids]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if args.overwrite else "a"
    with args.output.open(mode, encoding="utf-8") as fh:
        for index, row in enumerate(rows, start=1):
            prompt = build_prompt(row, args.format)
            try:
                if args.backend == "api":
                    response, latency = run_ollama_api(args.model, prompt, args.timeout)
                else:
                    response, latency = run_ollama_cli(args.model, prompt, args.timeout)
                error = None
            except Exception as exc:
                response = ""
                latency = None
                error = str(exc)

            record = {
                "model": args.model,
                "format": args.format,
                "example_id": row["example_id"],
                "task_id": row["task_id"],
                "question": row["question"],
                "ground_truth": row["ground_truth"],
                "response": response,
                "latency_seconds": latency,
                "error": error,
            }
            fh.write(json.dumps(record, sort_keys=True) + "\n")
            fh.flush()
            print(f"[{index}/{len(rows)}] {row['example_id']} error={error is not None}")


if __name__ == "__main__":
    main()

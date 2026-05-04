#!/usr/bin/env python3
"""Generate Benchmark V1 for structured tool-output experiments.

The generated dataset is deterministic by default and contains 10 tasks with
30 examples per task. Each example includes raw CLI, RTK-style, structured JSON,
compact JSON, task-focused JSON, a natural-language question, and
machine-gradable ground truth.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"
FIXTURES = DATASETS / "fixtures"
GENERATED = DATASETS / "generated"
SCHEMAS = DATASETS / "schemas"

REFERENCE_DATE = datetime(2026, 5, 4, tzinfo=timezone.utc)
TASK_COUNT = 10

DIRS = ["logs", "reports", "data", "archives", "tmp", "configs"]
LOG_NAMES = ["api", "worker", "scheduler", "gateway", "billing", "auth"]
EXTENSIONS = [".log", ".json", ".txt", ".csv", ".md", ".tar"]
LEVELS = ["INFO", "WARN", "ERROR", "DEBUG", "FAIL"]
MESSAGES = [
    "request completed",
    "timeout while connecting to upstream",
    "cache refresh finished",
    "invalid payload received",
    "retry budget exhausted",
    "database pool resized",
    "background job started",
    "permission denied",
    "health check recovered",
    "rate limit reached",
]


TASKS = {
    "task_01_largest_file": {
        "question": "Which file is the largest?",
        "answer_type": "file_path",
    },
    "task_02_newest_file": {
        "question": "Which file was modified most recently?",
        "answer_type": "file_path",
    },
    "task_03_extension_count": {
        "question": "How many files have the `.log` extension?",
        "answer_type": "integer",
    },
    "task_04_pattern_file_count": {
        "question": "How many files contain the word `ERROR`?",
        "answer_type": "integer",
    },
    "task_05_pattern_occurrence_count": {
        "question": "How many total `ERROR` occurrences are there?",
        "answer_type": "integer",
    },
    "task_06_first_failure": {
        "question": "Which file contains the earliest `FAIL` event?",
        "answer_type": "event",
    },
    "task_07_total_line_count": {
        "question": "What is the total number of lines across all `.log` files?",
        "answer_type": "integer",
    },
    "task_08_average_file_size": {
        "question": "What is the average size in bytes of `.json` files?",
        "answer_type": "number",
    },
    "task_09_largest_log_error_count": {
        "question": "In the largest `.log` file, how many `ERROR` entries are there?",
        "answer_type": "composite",
    },
    "task_10_stale_large_file_detection": {
        "question": "Which files are larger than 1 MB and have not been modified in the last 30 days?",
        "answer_type": "file_path_list",
    },
}

FORMATS = ["raw_cli", "rtk_style", "structured_json", "compact_json", "task_focused_json"]


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def rand_dt(rng: random.Random, max_age_days: int = 75) -> datetime:
    age_days = rng.randint(0, max_age_days)
    seconds = rng.randint(0, 86_399)
    return REFERENCE_DATE - timedelta(days=age_days, seconds=seconds)


def make_path(rng: random.Random, idx: int, ext: str) -> str:
    directory = rng.choice(DIRS)
    if ext == ".log":
        stem = f"{rng.choice(LOG_NAMES)}-{idx:02d}"
    elif ext == ".tar":
        stem = f"archive-{idx:02d}"
        directory = "archives"
    elif ext == ".json":
        stem = f"report-{idx:02d}"
        directory = rng.choice(["reports", "configs", "data"])
    else:
        stem = f"file-{idx:02d}"
    return f"{directory}/{stem}{ext}"


def make_log_lines(rng: random.Random, path: str, count: int, start: datetime) -> list[dict]:
    lines = []
    current = start
    for line_no in range(1, count + 1):
        current += timedelta(seconds=rng.randint(2, 420))
        level = rng.choices(LEVELS, weights=[48, 18, 15, 15, 4], k=1)[0]
        message = rng.choice(MESSAGES)
        lines.append(
            {
                "file": path,
                "line": line_no,
                "timestamp": iso(current),
                "level": level,
                "text": f"{iso(current)} {level} {message}",
            }
        )
    return lines


def generate_fixture(rng: random.Random, fixture_id: str) -> dict:
    file_count = rng.randint(18, 34)
    files = []
    used_paths = set()

    required_exts = [".log", ".log", ".log", ".json", ".json", ".tar"]
    exts = required_exts + [rng.choice(EXTENSIONS) for _ in range(file_count - len(required_exts))]

    for idx, ext in enumerate(exts, start=1):
        path = make_path(rng, idx, ext)
        while path in used_paths:
            path = make_path(rng, idx + rng.randint(10, 99), ext)
        used_paths.add(path)

        mtime = rand_dt(rng)
        if ext == ".tar" and rng.random() < 0.7:
            mtime = REFERENCE_DATE - timedelta(days=rng.randint(31, 90), seconds=rng.randint(0, 86_399))

        size = rng.randint(80, 15_000)
        line_count = None
        log_lines = []
        if ext == ".log":
            line_count = rng.randint(18, 80)
            start = mtime - timedelta(hours=rng.randint(1, 24))
            log_lines = make_log_lines(rng, path, line_count, start)
            size = max(size, sum(len(item["text"]) + 1 for item in log_lines))
        elif ext == ".json":
            size = rng.randint(120, 14_000)
        elif ext == ".tar":
            size = rng.randint(600_000, 4_500_000)

        files.append(
            {
                "path": path,
                "name": path.split("/")[-1],
                "extension": ext,
                "type": "file",
                "size_bytes": size,
                "mtime": iso(mtime),
                "line_count": line_count,
                "log_lines": log_lines,
            }
        )

    ensure_task_coverage(files, rng)
    return {"fixture_id": fixture_id, "reference_date": "2026-05-04", "files": sorted(files, key=lambda f: f["path"])}


def ensure_task_coverage(files: list[dict], rng: random.Random) -> None:
    logs = [f for f in files if f["extension"] == ".log"]
    jsons = [f for f in files if f["extension"] == ".json"]
    archives = [f for f in files if f["extension"] == ".tar"]

    if logs and not any(line["level"] == "ERROR" for f in logs for line in f["log_lines"]):
        line = logs[0]["log_lines"][0]
        line["level"] = "ERROR"
        line["text"] = line["text"].replace("INFO", "ERROR", 1)

    if logs and not any(line["level"] == "FAIL" for f in logs for line in f["log_lines"]):
        line = logs[-1]["log_lines"][0]
        line["level"] = "FAIL"
        line["text"] = line["text"].replace("INFO", "FAIL", 1)

    if jsons:
        jsons[0]["size_bytes"] = max(jsons[0]["size_bytes"], rng.randint(1_000, 20_000))

    if archives:
        archives[0]["size_bytes"] = max(archives[0]["size_bytes"], 1_200_000)
        archives[0]["mtime"] = iso(REFERENCE_DATE - timedelta(days=45, seconds=3600))


def ls_rows(files: list[dict]) -> list[str]:
    rows = []
    for f in sorted(files, key=lambda item: item["path"]):
        dt = datetime.strptime(f["mtime"], "%Y-%m-%dT%H:%M:%SZ")
        rows.append(f"-rw-r--r-- 1 user staff {f['size_bytes']:>8} {dt:%b %d %H:%M} {f['path']}")
    return rows


def grep_rows(matches: list[dict]) -> list[str]:
    return [f"{m['file']}:{m['line']}:{m['text']}" for m in matches]


def wc_rows(files: list[dict]) -> list[str]:
    rows = [f"{f['line_count']:>7} {f['path']}" for f in files]
    rows.append(f"{sum(f['line_count'] for f in files):>7} total")
    return rows


def compact_files(files: list[dict]) -> list[dict]:
    return [{"p": f["path"], "s": f["size_bytes"], "m": f["mtime"], "e": f["extension"]} for f in files]


def public_files(files: list[dict]) -> list[dict]:
    return [
        {
            "path": f["path"],
            "size_bytes": f["size_bytes"],
            "mtime": f["mtime"],
            "extension": f["extension"],
            "type": f["type"],
        }
        for f in files
    ]


def all_matches(files: list[dict], level: str) -> list[dict]:
    matches = []
    for f in files:
        if f["extension"] != ".log":
            continue
        for line in f["log_lines"]:
            if line["level"] == level:
                matches.append({"file": f["path"], "line": line["line"], "timestamp": line["timestamp"], "text": line["text"]})
    return sorted(matches, key=lambda m: (m["file"], m["line"]))


def render_listing(files: list[dict]) -> dict:
    structured = {"files": public_files(files)}
    compact = {"f": compact_files(files)}
    return {
        "raw_cli": "\n".join(ls_rows(files)),
        "rtk_style": "\n".join(f"{f['path']}|{f['size_bytes']}|{f['mtime']}|{f['extension']}" for f in files),
        "structured_json": structured,
        "compact_json": compact,
    }


def render_grep(matches: list[dict], pattern: str) -> dict:
    structured = {"pattern": pattern, "matches": matches, "count": len(matches)}
    compact = {"q": pattern, "n": len(matches), "m": [{"f": m["file"], "l": m["line"], "t": m["timestamp"], "x": m["text"]} for m in matches]}
    return {
        "raw_cli": "\n".join(grep_rows(matches)),
        "rtk_style": "\n".join(f"{m['file']}:{m['line']}:{pattern}" for m in matches),
        "structured_json": structured,
        "compact_json": compact,
    }


def render_wc(logs: list[dict]) -> dict:
    structured = {
        "files": [{"path": f["path"], "lines": f["line_count"]} for f in logs],
        "total_lines": sum(f["line_count"] for f in logs),
    }
    compact = {"f": [{"p": f["path"], "l": f["line_count"]} for f in logs], "t": structured["total_lines"]}
    return {
        "raw_cli": "\n".join(wc_rows(logs)),
        "rtk_style": "\n".join(f"{f['path']}|{f['line_count']}" for f in logs) + f"\nTOTAL|{structured['total_lines']}",
        "structured_json": structured,
        "compact_json": compact,
    }


def focused_file_sizes(files: list[dict]) -> dict:
    return {"files": [{"path": f["path"], "size_bytes": f["size_bytes"]} for f in files]}


def focused_file_times(files: list[dict]) -> dict:
    return {"files": [{"path": f["path"], "mtime": f["mtime"]} for f in files]}


def focused_extension_files(files: list[dict], extension: str) -> dict:
    return {
        "extension": extension,
        "matching_files": [{"path": f["path"]} for f in files if f["extension"] == extension],
    }


def focused_unique_match_files(matches: list[dict], pattern: str) -> dict:
    return {"pattern": pattern, "matching_files": [{"path": path} for path in sorted({m["file"] for m in matches})]}


def focused_match_refs(matches: list[dict], pattern: str) -> dict:
    return {"pattern": pattern, "matches": [{"file": m["file"], "line": m["line"]} for m in matches]}


def focused_failure_events(matches: list[dict], pattern: str) -> dict:
    return {
        "pattern": pattern,
        "events": [{"file": m["file"], "line": m["line"], "timestamp": m["timestamp"]} for m in matches],
    }


def focused_log_line_counts(logs: list[dict]) -> dict:
    return {"files": [{"path": f["path"], "lines": f["line_count"]} for f in logs]}


def focused_ext_sizes(files: list[dict], extension: str) -> dict:
    return {
        "extension": extension,
        "files": [{"path": f["path"], "size_bytes": f["size_bytes"]} for f in files if f["extension"] == extension],
    }


def focused_stale_candidates(files: list[dict], threshold: int) -> dict:
    return {
        "reference_date": "2026-05-04",
        "size_threshold_bytes": threshold,
        "age_threshold_days": 30,
        "files": [
            {"path": f["path"], "size_bytes": f["size_bytes"], "mtime": f["mtime"]}
            for f in files
            if f["size_bytes"] > threshold
        ],
    }


def build_example(task_id: str, fixture: dict) -> dict:
    files = fixture["files"]
    logs = [f for f in files if f["extension"] == ".log"]
    jsons = [f for f in files if f["extension"] == ".json"]

    if task_id == "task_01_largest_file":
        largest = max(files, key=lambda f: (f["size_bytes"], f["path"]))
        outputs = render_listing(files)
        outputs["task_focused_json"] = focused_file_sizes(files)
        ground_truth = {"answer_type": "file_path", "largest_file": largest["path"], "size_bytes": largest["size_bytes"]}

    elif task_id == "task_02_newest_file":
        newest = max(files, key=lambda f: (f["mtime"], f["path"]))
        outputs = render_listing(files)
        outputs["task_focused_json"] = focused_file_times(files)
        ground_truth = {"answer_type": "file_path", "newest_file": newest["path"], "mtime": newest["mtime"]}

    elif task_id == "task_03_extension_count":
        outputs = render_listing(files)
        outputs["task_focused_json"] = focused_extension_files(files, ".log")
        ground_truth = {"answer_type": "integer", "extension": ".log", "count": len(logs)}

    elif task_id == "task_04_pattern_file_count":
        matches = all_matches(files, "ERROR")
        matching_files = sorted({m["file"] for m in matches})
        outputs = render_grep(matches, "ERROR")
        outputs["task_focused_json"] = focused_unique_match_files(matches, "ERROR")
        ground_truth = {"answer_type": "integer", "pattern": "ERROR", "matching_file_count": len(matching_files)}

    elif task_id == "task_05_pattern_occurrence_count":
        matches = all_matches(files, "ERROR")
        outputs = render_grep(matches, "ERROR")
        outputs["task_focused_json"] = focused_match_refs(matches, "ERROR")
        ground_truth = {"answer_type": "integer", "pattern": "ERROR", "total_occurrences": len(matches)}

    elif task_id == "task_06_first_failure":
        matches = sorted(all_matches(files, "FAIL"), key=lambda m: (m["timestamp"], m["file"], m["line"]))
        first = matches[0]
        outputs = render_grep(matches, "FAIL")
        outputs["task_focused_json"] = focused_failure_events(matches, "FAIL")
        ground_truth = {
            "answer_type": "event",
            "pattern": "FAIL",
            "file": first["file"],
            "line": first["line"],
            "timestamp": first["timestamp"],
        }

    elif task_id == "task_07_total_line_count":
        outputs = render_wc(logs)
        outputs["task_focused_json"] = focused_log_line_counts(logs)
        ground_truth = {"answer_type": "integer", "extension": ".log", "total_lines": sum(f["line_count"] for f in logs)}

    elif task_id == "task_08_average_file_size":
        outputs = render_listing(files)
        outputs["task_focused_json"] = focused_ext_sizes(files, ".json")
        avg = sum(f["size_bytes"] for f in jsons) / len(jsons)
        ground_truth = {
            "answer_type": "number",
            "extension": ".json",
            "file_count": len(jsons),
            "average_size_bytes": round(avg, 2),
            "tolerance": 0.01,
        }

    elif task_id == "task_09_largest_log_error_count":
        largest_log = max(logs, key=lambda f: (f["size_bytes"], f["path"]))
        matches = [m for m in all_matches(files, "ERROR") if m["file"] == largest_log["path"]]
        combined = {
            "files": public_files(logs),
            "matches": all_matches(files, "ERROR"),
            "pattern": "ERROR",
        }
        outputs = {
            "raw_cli": "\n".join(ls_rows(logs) + ["", *grep_rows(all_matches(files, "ERROR"))]),
            "rtk_style": "\n".join([f"{f['path']}|{f['size_bytes']}" for f in logs] + ["--"] + [f"{m['file']}:{m['line']}:ERROR" for m in all_matches(files, "ERROR")]),
            "structured_json": combined,
            "compact_json": {
                "f": compact_files(logs),
                "q": "ERROR",
                "m": [{"f": m["file"], "l": m["line"]} for m in all_matches(files, "ERROR")],
            },
            "task_focused_json": {
                "log_files": [{"path": f["path"], "size_bytes": f["size_bytes"]} for f in logs],
                "pattern": "ERROR",
                "matches": [{"file": m["file"], "line": m["line"]} for m in all_matches(files, "ERROR")],
            },
        }
        ground_truth = {
            "answer_type": "composite",
            "largest_log_file": largest_log["path"],
            "size_bytes": largest_log["size_bytes"],
            "pattern": "ERROR",
            "error_count": len(matches),
        }

    elif task_id == "task_10_stale_large_file_detection":
        threshold = 1_048_576
        cutoff = REFERENCE_DATE - timedelta(days=30)
        stale = sorted(
            f["path"]
            for f in files
            if f["size_bytes"] > threshold and datetime.strptime(f["mtime"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) < cutoff
        )
        listing = render_listing(files)
        listing["structured_json"]["reference_date"] = "2026-05-04"
        listing["structured_json"]["size_threshold_bytes"] = threshold
        listing["structured_json"]["age_threshold_days"] = 30
        listing["compact_json"]["r"] = "2026-05-04"
        listing["compact_json"]["smin"] = threshold
        listing["compact_json"]["dmin"] = 30
        listing["task_focused_json"] = focused_stale_candidates(files, threshold)
        outputs = listing
        ground_truth = {
            "answer_type": "file_path_list",
            "reference_date": "2026-05-04",
            "size_threshold_bytes": threshold,
            "age_threshold_days": 30,
            "files": stale,
        }

    else:
        raise ValueError(f"Unknown task: {task_id}")

    task = TASKS[task_id]
    example_id = f"{fixture['fixture_id']}_{task_id}"
    return {
        "example_id": example_id,
        "task_id": task_id,
        "fixture_id": fixture["fixture_id"],
        "question": task["question"],
        "expected_answer_type": task["answer_type"],
        "tool_outputs": outputs,
        "ground_truth": ground_truth,
        "answer_schema": {
            "type": "object",
            "required": ["answer", "confidence"],
            "properties": {
                "answer": {"description": "Task-specific answer value or object."},
                "confidence": {"enum": ["low", "medium", "high"]},
            },
        },
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def write_schemas() -> None:
    example_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Benchmark V1 Example",
        "type": "object",
        "required": ["example_id", "task_id", "fixture_id", "question", "tool_outputs", "ground_truth"],
        "properties": {
            "example_id": {"type": "string"},
            "task_id": {"type": "string"},
            "fixture_id": {"type": "string"},
            "question": {"type": "string"},
            "expected_answer_type": {"type": "string"},
            "tool_outputs": {
                "type": "object",
                "required": FORMATS,
            },
            "ground_truth": {"type": "object"},
        },
    }
    fixture_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Benchmark V1 Fixture",
        "type": "object",
        "required": ["fixture_id", "reference_date", "files"],
    }
    write_json(SCHEMAS / "benchmark_v1_example.schema.json", example_schema)
    write_json(SCHEMAS / "benchmark_v1_fixture.schema.json", fixture_schema)


def generate(instances_per_task: int, seed: int) -> tuple[list[dict], list[dict], dict]:
    examples = []
    fixtures = []
    rng = random.Random(seed)

    for task_id in TASKS:
        for index in range(1, instances_per_task + 1):
            fixture_id = f"{task_id}_fixture_{index:03d}"
            fixture_rng = random.Random(rng.randint(0, 10_000_000))
            fixture = generate_fixture(fixture_rng, fixture_id)
            fixtures.append(fixture)
            examples.append(build_example(task_id, fixture))

    manifest = {
        "name": "llm-cli-structured-output-benchmark-v1",
        "version": "0.1.0",
        "seed": seed,
        "reference_date": "2026-05-04",
        "task_count": TASK_COUNT,
        "instances_per_task": instances_per_task,
        "example_count": len(examples),
        "formats": FORMATS,
        "tasks": TASKS,
        "files": {
            "examples": "datasets/generated/benchmark_v1.jsonl",
            "fixtures": "datasets/fixtures/benchmark_v1_fixtures.jsonl",
            "manifest": "datasets/generated/benchmark_v1_manifest.json",
        },
    }
    return examples, fixtures, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances-per-task", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260504)
    args = parser.parse_args()

    examples, fixtures, manifest = generate(args.instances_per_task, args.seed)
    write_jsonl(GENERATED / "benchmark_v1.jsonl", examples)
    write_jsonl(FIXTURES / "benchmark_v1_fixtures.jsonl", fixtures)
    write_json(GENERATED / "benchmark_v1_manifest.json", manifest)
    write_schemas()

    print(f"Generated {len(examples)} examples")
    print(f"Wrote {GENERATED / 'benchmark_v1.jsonl'}")
    print(f"Wrote {FIXTURES / 'benchmark_v1_fixtures.jsonl'}")
    print(f"Wrote {GENERATED / 'benchmark_v1_manifest.json'}")


if __name__ == "__main__":
    main()

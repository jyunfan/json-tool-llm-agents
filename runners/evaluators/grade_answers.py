#!/usr/bin/env python3
"""Grade model JSON answers against Benchmark V1 ground truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "results" / "raw" / "ollama_runs.jsonl"
DEFAULT_OUTPUT = ROOT / "results" / "processed" / "ollama_grades.jsonl"


def extract_json(text: str) -> tuple[dict | None, str | None]:
    try:
        return json.loads(text), None
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1]), None
        except json.JSONDecodeError as exc:
            return None, str(exc)
    return None, "no_json_object_found"


def normalize_answer(payload: dict | None) -> object:
    if not isinstance(payload, dict):
        return None
    return payload.get("answer")


def grade_answer(answer: object, gt: dict) -> bool:
    answer_type = gt.get("answer_type")

    if answer_type == "file_path":
        expected = gt.get("largest_file") or gt.get("newest_file")
        if isinstance(answer, str):
            return answer == expected
        if isinstance(answer, dict):
            return answer.get("file") == expected or answer.get("path") == expected

    if answer_type == "integer":
        expected = gt.get("count", gt.get("matching_file_count", gt.get("total_occurrences", gt.get("total_lines"))))
        if isinstance(answer, dict):
            answer = answer.get("value", answer.get("count"))
        return isinstance(answer, int) and answer == expected

    if answer_type == "number":
        expected = gt.get("average_size_bytes")
        tolerance = gt.get("tolerance", 0.01)
        if isinstance(answer, dict):
            answer = answer.get("value", answer.get("average_size_bytes"))
        return isinstance(answer, (int, float)) and abs(float(answer) - float(expected)) <= tolerance

    if answer_type == "event":
        if not isinstance(answer, dict):
            return False
        return answer.get("file") == gt.get("file") and answer.get("timestamp") == gt.get("timestamp")

    if answer_type == "composite":
        if not isinstance(answer, dict):
            return False
        file_ok = answer.get("largest_log_file") == gt.get("largest_log_file") or answer.get("file") == gt.get("largest_log_file")
        count_ok = answer.get("error_count") == gt.get("error_count") or answer.get("value") == gt.get("error_count")
        return file_ok and count_ok

    if answer_type == "file_path_list":
        expected = sorted(gt.get("files", []))
        if isinstance(answer, dict):
            answer = answer.get("files")
        return isinstance(answer, list) and sorted(answer) == expected

    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=0, help="0 means all rows")
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines()]
    if args.limit:
        rows = rows[: args.limit]
    graded = []
    for row in rows:
        payload, parse_error = extract_json(row.get("response", ""))
        valid_json = payload is not None
        answer = normalize_answer(payload)
        success = valid_json and grade_answer(answer, row["ground_truth"])
        graded.append({**row, "parsed_response": payload, "valid_json": valid_json, "parse_error": parse_error, "success": success})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for row in graded:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    total = len(graded)
    ok = sum(1 for row in graded if row["success"])
    valid = sum(1 for row in graded if row["valid_json"])
    print(f"Wrote {args.output}")
    print(f"success_rate={ok}/{total} ({ok / total:.2%})")
    print(f"valid_json_rate={valid}/{total} ({valid / total:.2%})")


if __name__ == "__main__":
    main()

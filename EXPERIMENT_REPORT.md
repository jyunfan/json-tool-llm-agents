# Structured Tool Output Pilot Report

## Summary

This pilot evaluates whether task-aligned structured output helps a local small
LLM answer tool-output questions more reliably. The experiment uses
`nemotron-3-nano:4b` on the first 100 Benchmark V1 examples.

The key result is that **task-focused JSON** outperforms raw CLI, RTK-style
output, full structured JSON, and compact JSON.

## Setup

- Model: `nemotron-3-nano:4b`
- Runner: Ollama API with JSON mode and temperature 0
- Dataset: first 100 examples from Benchmark V1
- Tasks covered:
  - Task 1: largest file, 30 examples
  - Task 2: newest file, 30 examples
  - Task 3: `.log` extension count, 30 examples
  - Task 4: files containing `ERROR`, first 10 examples
- Output formats:
  - `raw_cli`
  - `rtk_style`
  - `structured_json`
  - `compact_json`
  - `task_focused_json`

## Format-Level Results

| Format | Success Rate | Valid JSON Rate | Runtime Error Rate | Mean Latency | Mean Tokens | Token Reduction vs Raw |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| raw_cli | 43% | 100% | 0% | 4.451s | 696.34 | 0% |
| rtk_style | 26% | 100% | 0% | 4.533s | 463.24 | 33.47% |
| structured_json | 41% | 98% | 2% | 7.299s | 1664.15 | -138.98% |
| compact_json | 37% | 98% | 2% | 5.977s | 1392.60 | -99.99% |
| task_focused_json | 70% | 100% | 0% | 2.966s | 478.21 | 31.33% |

## Task-Level Results

| Format | Task 1 | Task 2 | Task 3 | Task 4 |
| --- | ---: | ---: | ---: | ---: |
| raw_cli | 25/30 | 6/30 | 12/30 | 0/10 |
| rtk_style | 16/30 | 10/30 | 0/30 | 0/10 |
| structured_json | 26/30 | 7/30 | 8/30 | 0/10 |
| compact_json | 19/30 | 6/30 | 12/30 | 0/10 |
| task_focused_json | 26/30 | 12/30 | 23/30 | 9/10 |

## Interpretation

The initial JSON formats did not validate a simple "JSON always wins" claim.
Full structured JSON increased token usage and latency, while compact JSON
still preserved too much irrelevant information. RTK-style output reduced token
count but had the lowest success rate.

The task-focused JSON result is different. It keeps the output structured while
filtering each task to the fields needed for the question:

- Largest file: `path` and `size_bytes`
- Newest file: `path` and `mtime`
- Extension count: only matching `.log` files
- Pattern file count: unique files containing `ERROR`

This improved success from 43% with raw CLI to 70%, reduced average token usage
by 31.33% relative to raw CLI, and lowered latency to 2.966s.

## Research Claim

The pilot supports a more precise claim:

> Structured tool output helps local small LLMs when the schema is task-aligned
> and suppresses irrelevant command-line noise.

This is stronger than claiming that JSON serialization alone is beneficial.
The benchmark now shows a useful distinction among:

- token reduction without enough semantic support (`rtk_style`)
- structure without task filtering (`structured_json`, `compact_json`)
- task-aligned structured evidence (`task_focused_json`)

## Artifacts

- Dataset generator: `datasets/generate_benchmark_v1.py`
- Dataset: `datasets/generated/benchmark_v1.jsonl`
- Token summary: `results/processed/format_token_summary.csv`
- Five-format summary: `results/processed/nemotron_3_nano_4b_pilot100_with_task_focused_summary.csv`
- Detailed report: `results/processed/nemotron_3_nano_4b_pilot100_with_task_focused_report.md`

## Next Step

Run the same pilot on Phi, Gemma, and Qwen small models. If the pattern holds
across model families, task-focused structured output becomes the central result
for the paper.

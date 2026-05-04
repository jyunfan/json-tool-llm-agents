# Nemotron 3 Nano 4B Pilot 100: Task-Focused JSON Comparison

Model:

- `nemotron-3-nano:4b`

Scope:

- First 100 Benchmark V1 examples
- 5 output formats:
  - raw CLI
  - RTK-style
  - structured JSON
  - compact JSON
  - task-focused JSON

Covered tasks:

- Task 1: largest file, 30 examples
- Task 2: newest file, 30 examples
- Task 3: `.log` extension count, 30 examples
- Task 4: files containing `ERROR`, first 10 examples

## Main Result

| Format | Success Rate | Valid JSON Rate | Runtime Error Rate | Mean Latency | Mean Tokens | Token Reduction vs Raw |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| raw_cli | 43% | 100% | 0% | 4.451s | 696.34 | 0% |
| rtk_style | 26% | 100% | 0% | 4.533s | 463.24 | 33.47% |
| structured_json | 41% | 98% | 2% | 7.299s | 1664.15 | -138.98% |
| compact_json | 37% | 98% | 2% | 5.977s | 1392.60 | -99.99% |
| task_focused_json | 70% | 100% | 0% | 2.966s | 478.21 | 31.33% |

Task-focused JSON produced the best pilot result: highest success rate, no runtime errors, lowest mean latency, and token usage close to RTK-style compression.

## Task-Level Success

| Format | Task 1 | Task 2 | Task 3 | Task 4 |
| --- | ---: | ---: | ---: | ---: |
| raw_cli | 25/30 | 6/30 | 12/30 | 0/10 |
| rtk_style | 16/30 | 10/30 | 0/30 | 0/10 |
| structured_json | 26/30 | 7/30 | 8/30 | 0/10 |
| compact_json | 19/30 | 6/30 | 12/30 | 0/10 |
| task_focused_json | 26/30 | 12/30 | 23/30 | 9/10 |

## Interpretation

The earlier pilot showed that naively converting full raw output into JSON was not enough. Full structured JSON increased token count and latency, and compact JSON still forced the model to process mostly irrelevant records.

Task-focused JSON changed the result. It kept the schema explicit while removing irrelevant fields:

- Task 1 kept only `path` and `size_bytes`.
- Task 2 kept only `path` and `mtime`.
- Task 3 kept only `.log` matching files.
- Task 4 kept only unique files containing `ERROR`.

This supports the stronger research claim:

> Structured output helps small local models when the structure is task-aligned, not when it merely serializes raw tool output.

## Research Takeaways

1. Token reduction alone is insufficient: RTK-style had the lowest token count among the original four formats but the worst success rate.
2. Full JSON is not automatically better: structured JSON and compact JSON were slower and less reliable than task-focused JSON.
3. Task-focused structure is the promising contribution: it improved success from 43% to 70% over raw CLI while also reducing mean tokens by 31.33%.
4. Task 4 became solvable: raw, RTK-style, structured JSON, and compact JSON all scored 0/10, while task-focused JSON scored 9/10.

## Next Step

Run the same pilot on Phi, Gemma, and Qwen small models. If the pattern holds, this becomes the paper's central result: local small models benefit most from structured outputs when schemas expose task-relevant information and suppress irrelevant command-line noise.

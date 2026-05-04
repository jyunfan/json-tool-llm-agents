# Nemotron 3 Nano 4B Pilot 100 Results

Model:

- `nemotron-3-nano:4b`

Scope:

- First 100 Benchmark V1 examples
- 4 output formats: raw CLI, RTK-style, structured JSON, compact JSON
- Covered tasks:
  - Task 1: largest file, 30 examples
  - Task 2: newest file, 30 examples
  - Task 3: `.log` extension count, 30 examples
  - Task 4: files containing `ERROR`, first 10 examples

## Format-Level Summary

| Format | Examples | Success Rate | Valid JSON Rate | Runtime Error Rate | Mean Latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| raw_cli | 100 | 43% | 100% | 0% | 4.451s |
| rtk_style | 100 | 26% | 100% | 0% | 4.533s |
| structured_json | 100 | 41% | 98% | 2% | 7.299s |
| compact_json | 100 | 37% | 98% | 2% | 5.977s |

## Task-Level Success

| Format | Task 1 | Task 2 | Task 3 | Task 4 |
| --- | ---: | ---: | ---: | ---: |
| raw_cli | 25/30 | 6/30 | 12/30 | 0/10 |
| rtk_style | 16/30 | 10/30 | 0/30 | 0/10 |
| structured_json | 26/30 | 7/30 | 8/30 | 0/10 |
| compact_json | 19/30 | 6/30 | 12/30 | 0/10 |

## Early Interpretation

This pilot does not support a simple "JSON always wins" claim. Structured JSON slightly outperformed raw CLI on the largest-file task, but raw CLI had the best overall success rate across the first 100 examples. RTK-style output reduced representation size, but performed worst overall in this pilot.

The weakest task was pattern-file counting. All formats scored 0/10 on Task 4. Structured JSON and compact JSON also triggered two Ollama HTTP 500 errors on the same Task 4 fixtures:

- `task_04_pattern_file_count_fixture_004_task_04_pattern_file_count`
- `task_04_pattern_file_count_fixture_007_task_04_pattern_file_count`

## Research Implications

1. The benchmark is already useful because it exposes non-obvious trade-offs.
2. Structured output needs task-specific filtering; dumping every match into JSON can be slower and less stable.
3. RTK-style compression may remove or obscure cues small models need for counting and sorting.
4. The next iteration should compare full-output JSON against task-specific JSON summaries.

## Next Experiment

Add a fifth output format:

- `task_focused_json`

Instead of serializing all available tool data, this format should expose only fields relevant to the question. For example:

- Largest file: file path and size only
- Newest file: file path and mtime only
- Extension count: extension histogram or file extension list only
- Pattern file count: unique matching files and count, not every matching line

This will test whether structure helps when schema design is aligned with the task, rather than merely converting raw output into JSON.

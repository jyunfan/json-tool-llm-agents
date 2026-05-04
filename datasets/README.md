# Benchmark V1 Dataset

This directory contains the first synthetic dataset for evaluating raw CLI,
RTK-style, structured JSON, compact JSON, and task-focused JSON tool outputs
with local small LLMs.

## Generated Files

- `generated/benchmark_v1.jsonl`: 300 model-evaluation examples.
- `fixtures/benchmark_v1_fixtures.jsonl`: synthetic file-tree and log fixtures used to derive examples.
- `generated/benchmark_v1_manifest.json`: dataset metadata, task list, generation seed, and output format list.
- `schemas/benchmark_v1_example.schema.json`: JSON schema for generated examples.
- `schemas/benchmark_v1_fixture.schema.json`: JSON schema for fixtures.

## Regenerate

```bash
python3 datasets/generate_benchmark_v1.py --instances-per-task 30 --seed 20260504
```

## Scale

The default dataset size is:

```text
10 tasks x 30 instances = 300 examples
```

Increase `--instances-per-task` to create a larger benchmark.

## Example Shape

Each example contains:

- `example_id`
- `task_id`
- `fixture_id`
- `question`
- `expected_answer_type`
- `tool_outputs.raw_cli`
- `tool_outputs.rtk_style`
- `tool_outputs.structured_json`
- `tool_outputs.compact_json`
- `tool_outputs.task_focused_json`
- `ground_truth`
- `answer_schema`

## Tasks

1. Largest file
2. Newest file
3. `.log` extension count
4. Files containing `ERROR`
5. Total `ERROR` occurrences
6. Earliest `FAIL` event
7. Total lines across `.log` files
8. Average `.json` file size
9. `ERROR` count in the largest `.log` file
10. Files larger than 1 MB and older than 30 days

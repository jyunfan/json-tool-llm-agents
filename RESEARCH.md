# Structured Tool Outputs for Local Small LLM Agents

## Working Title

**Structured Tool Outputs Improve Token Efficiency and Reliability for Local Small Language Model Agents**

Subtitle:

**A Benchmark Study with Phi, Gemma, and Qwen Models**

## Research Positioning

This project studies whether structured tool outputs, especially JSON and compact JSON, improve the reliability and token efficiency of local small language model agents. The central argument is that local models such as Phi, Gemma, and Qwen are more sensitive to verbose and ambiguous command-line output than larger hosted models. Structured output may reduce not only input tokens, but also parsing ambiguity, answer-format failures, repair attempts, and total execution cost.

The paper should be framed as a benchmark and empirical study, not merely as a JSON wrapper tool. RTK is treated as an important comparison point, but the benchmark and evaluation protocol are the primary contribution.

## Core Claim

Structured JSON output reduces the reasoning and parsing burden for local small LLMs, improving task reliability under limited model capacity. Even when JSON is not always the shortest serialization, its schema-level regularity can produce better total efficiency by improving success rate and reducing retries.

## Contributions

1. A benchmark for evaluating token efficiency and reliability in LLM command-line tool usage.
2. A standard evaluation protocol comparing raw CLI output, RTK-style token-reduced output, structured JSON, and optionally compact JSON.
3. A systematic comparison across local small model families: Phi, Gemma, and Qwen.
4. Evidence that structured output can improve task success, output validity, and repair rate for small local LLMs.
5. A finding that input token reduction alone is insufficient; total tokens, task success, latency, and repair attempts must be evaluated together.

## Research Questions

**RQ1: Does structured JSON reduce token usage compared with raw CLI output and RTK-style output?**

Metrics:

- Input tokens
- Output tokens
- Total tokens
- Context overflow rate

**RQ2: Does structured JSON improve task success rate for local small language models?**

Metrics:

- Exact-match task success
- Numeric tolerance success for aggregate answers
- Answer format validity

**RQ3: Are smaller local models more dependent on structured tool output than larger local models?**

Metrics:

- Accuracy gain by model size
- Repair attempts by model size
- Failure type distribution by model size

**RQ4: Does RTK-style token reduction reliably translate into lower total cost and higher task success?**

Metrics:

- Input token reduction
- Total token reduction
- Output verbosity
- Retry rate
- Success rate

## Hypotheses

**H1:** Structured JSON reduces input token usage compared with raw CLI output for common file, search, and statistics tasks.

**H2:** Structured JSON improves task success rate for local small models by reducing parsing ambiguity.

**H3:** The benefit of structured output is larger for smaller models than for larger models.

**H4:** RTK-style output reduces input tokens, but does not always improve total token cost or task success.

## Compared Output Formats

### Raw CLI

Unmodified command-line output from tools such as `ls`, `find`, `grep`, and `wc`.

### RTK-Style Reduced Output

Token-reduced text representation inspired by RTK. The benchmark should record whether RTK-style compression preserves task-relevant details and whether reduced input tokens lead to better total efficiency.

### Structured JSON

Human-readable schema-based output with explicit fields.

Example:

```json
{
  "files": [
    {
      "path": "logs/app.log",
      "size_bytes": 5321,
      "mtime": "2026-05-01T10:12:00Z",
      "type": "file"
    }
  ]
}
```

### Compact JSON

Optional fourth condition using shorter field names. This separates the value of structure from the verbosity of descriptive JSON keys.

Example:

```json
{
  "f": [
    {
      "p": "logs/app.log",
      "s": 5321,
      "m": "2026-05-01T10:12:00Z",
      "t": "file"
    }
  ]
}
```

## Model Plan

The MVP should include 6 local models if compute allows:

| Family | Small | Medium |
| --- | --- | --- |
| Phi | 3B/4B class | 7B/14B class |
| Gemma | 2B/4B class | 9B/12B class |
| Qwen | 1.5B/3B class | 7B/14B class |

If compute is limited, use this smaller MVP:

1. One Phi small model
2. One Gemma small model
3. One Qwen small model
4. One Qwen 7B-class model as a stronger local baseline

## Benchmark V1

Benchmark V1 contains 10 tasks across file listing, search, statistics, and multi-step tool reasoning. Each task should have synthetic instances with known ground truth. A reasonable MVP size is:

```text
10 tasks x 30 instances = 300 examples
```

Each example should contain:

- A synthetic workspace fixture
- The tool command or tool-output source
- Raw CLI output
- RTK-style reduced output
- Structured JSON output
- Optional compact JSON output
- A natural-language question
- Ground truth answer
- Expected answer schema

## Benchmark V1 Tasks and Ground Truth

### Task 1: Largest File

Question:

> Which file is the largest?

Tool source:

- `ls -l`
- `find` with file metadata

Required fields:

- File path
- Size in bytes
- File type

Ground truth format:

```json
{
  "answer_type": "file_path",
  "largest_file": "logs/api-2026-05-01.log",
  "size_bytes": 91234
}
```

Success criterion:

- Exact match on `largest_file`
- Optional exact match on `size_bytes`

### Task 2: Newest File

Question:

> Which file was modified most recently?

Tool source:

- `ls -lt`
- `find` with modification time

Required fields:

- File path
- Modification timestamp

Ground truth format:

```json
{
  "answer_type": "file_path",
  "newest_file": "reports/build-summary.json",
  "mtime": "2026-05-01T18:42:00Z"
}
```

Success criterion:

- Exact match on `newest_file`

### Task 3: Extension Count

Question:

> How many files have the `.log` extension?

Tool source:

- `find`
- `ls -R`

Required fields:

- File path
- Extension or file name

Ground truth format:

```json
{
  "answer_type": "integer",
  "extension": ".log",
  "count": 17
}
```

Success criterion:

- Exact integer match on `count`

### Task 4: Pattern File Count

Question:

> How many files contain the word `ERROR`?

Tool source:

- `grep -rl ERROR`

Required fields:

- Matching file path
- Pattern

Ground truth format:

```json
{
  "answer_type": "integer",
  "pattern": "ERROR",
  "matching_file_count": 6
}
```

Success criterion:

- Exact integer match on `matching_file_count`

### Task 5: Pattern Occurrence Count

Question:

> How many total `ERROR` occurrences are there?

Tool source:

- `grep -r ERROR`
- `grep -ro ERROR`

Required fields:

- File path
- Line number
- Match text
- Optional occurrence count per line

Ground truth format:

```json
{
  "answer_type": "integer",
  "pattern": "ERROR",
  "total_occurrences": 42
}
```

Success criterion:

- Exact integer match on `total_occurrences`

### Task 6: First Failure

Question:

> Which file contains the earliest `FAIL` event?

Tool source:

- `grep -r FAIL`

Required fields:

- File path
- Line number
- Event timestamp
- Match text

Ground truth format:

```json
{
  "answer_type": "event",
  "pattern": "FAIL",
  "file": "logs/worker-1.log",
  "line": 84,
  "timestamp": "2026-05-01T09:13:27Z"
}
```

Success criterion:

- Exact match on `file`
- Exact match on `timestamp` if requested

### Task 7: Total Line Count

Question:

> What is the total number of lines across all `.log` files?

Tool source:

- `wc -l *.log`
- recursive `wc`

Required fields:

- File path
- Line count
- Total line count

Ground truth format:

```json
{
  "answer_type": "integer",
  "extension": ".log",
  "total_lines": 12890
}
```

Success criterion:

- Exact integer match on `total_lines`

### Task 8: Average File Size

Question:

> What is the average size in bytes of `.json` files?

Tool source:

- `find`
- `ls -l`

Required fields:

- File path
- Size in bytes
- Extension

Ground truth format:

```json
{
  "answer_type": "number",
  "extension": ".json",
  "file_count": 8,
  "average_size_bytes": 2441.5
}
```

Success criterion:

- Numeric match within configured tolerance, for example `0.01`

### Task 9: Largest Log Error Count

Question:

> In the largest `.log` file, how many `ERROR` entries are there?

Tool source:

- `find` or `ls -l`
- `grep`

Required fields:

- File path
- Size in bytes
- Match count

Ground truth format:

```json
{
  "answer_type": "composite",
  "largest_log_file": "logs/api-2026-05-01.log",
  "size_bytes": 91234,
  "pattern": "ERROR",
  "error_count": 19
}
```

Success criterion:

- Exact match on `largest_log_file`
- Exact integer match on `error_count`

### Task 10: Stale Large File Detection

Question:

> Which files are larger than 1 MB and have not been modified in the last 30 days?

Tool source:

- `find`
- `ls -l`

Required fields:

- File path
- Size in bytes
- Modification timestamp
- Reference date

Ground truth format:

```json
{
  "answer_type": "file_path_list",
  "reference_date": "2026-05-04",
  "size_threshold_bytes": 1048576,
  "age_threshold_days": 30,
  "files": [
    "archives/service-2026-03.tar",
    "archives/legacy-debug.log"
  ]
}
```

Success criterion:

- Set equality on `files`

## Common Answer Schema

All model answers should be requested in JSON to simplify automatic grading:

```json
{
  "answer": null,
  "confidence": "low|medium|high"
}
```

Task-specific schemas should specialize `answer`:

```json
{
  "answer": {
    "file": "logs/api.log",
    "value": 19
  },
  "confidence": "high"
}
```

The evaluator should separately measure:

- Whether the answer is valid JSON
- Whether required fields are present
- Whether the value is correct
- Whether the model added unsupported extra claims

## Evaluation Pipeline

1. Generate synthetic benchmark fixtures.
2. Compute ground truth directly from structured fixture metadata.
3. Render each fixture into output formats: raw CLI, RTK-style reduced text, structured JSON, compact JSON.
4. Prompt each local model with a fixed task instruction and one rendered output.
5. Require the model to return JSON.
6. Parse and grade the model response.
7. Record token counts, latency, success, answer validity, and repair attempts.
8. Aggregate results by task, output format, model family, and model size.

## Metrics

### Token Metrics

- Input tokens
- Output tokens
- Total tokens
- Token reduction relative to raw CLI
- Context overflow rate

### Reliability Metrics

- Task success rate
- Answer JSON validity rate
- Required-field validity rate
- Repair attempts per example
- Unsupported-claim rate

### Runtime Metrics

- Tool rendering time
- Model inference latency
- End-to-end latency

### Cost-Like Local Metrics

For local models, direct API cost may not apply. Use proxy metrics:

- Total tokens
- Wall-clock latency
- Tokens per successful answer
- Retry-adjusted tokens per successful answer

## Expected Figures

1. Token usage by output format.
2. Task success rate by model and output format.
3. Accuracy gain from structured output by model size.
4. Total tokens vs success rate.
5. Repair attempts by model family.
6. RTK-style reduction vs structured JSON trade-off.

## Recommended Repository Structure

```text
datasets/
  fixtures/
  generated/
  schemas/
formatters/
  raw_cli/
  rtk_style/
  structured_json/
  compact_json/
runners/
  prompts/
  evaluators/
  tokenizers/
  local_models/
models/
  configs/
  manifests/
results/
  raw/
  processed/
  figures/
paper/
  outline/
  drafts/
  references/
```

### `datasets/`

Stores benchmark data and dataset definitions.

- `fixtures/`: synthetic file-tree and log fixtures used to generate tool outputs.
- `generated/`: rendered benchmark examples ready for model evaluation.
- `schemas/`: JSON schemas for fixtures, tool outputs, and ground truth.

### `formatters/`

Converts benchmark fixtures into different tool-output representations.

- `raw_cli/`: faithful raw command-line style renderers.
- `rtk_style/`: token-reduced text output inspired by RTK-like formatting.
- `structured_json/`: descriptive JSON schemas.
- `compact_json/`: compact JSON schemas with short keys.

### `runners/`

Runs model evaluation and grading.

- `prompts/`: fixed task prompts and response-format instructions.
- `evaluators/`: parsing, grading, and failure classification.
- `tokenizers/`: token counting utilities per model family.
- `local_models/`: adapters for local inference engines such as Ollama, llama.cpp, vLLM, or LM Studio.

### `models/`

Stores model metadata, not model weights.

- `configs/`: model-specific inference settings.
- `manifests/`: model lists, versions, quantization details, context length, and hardware notes.

### `results/`

Stores experiment outputs.

- `raw/`: per-run JSONL logs.
- `processed/`: aggregated tables.
- `figures/`: generated charts for the paper.

### `paper/`

Stores writing material.

- `outline/`: paper outline, contribution notes, and experiment tables.
- `drafts/`: manuscript drafts.
- `references/`: BibTeX and related-work notes.

## MVP Milestone

The first publishable version should include:

- 10 benchmark tasks
- 300 benchmark examples
- 3 to 4 output formats
- 4 to 6 local models
- Automatic grading
- Token and latency logging
- At least one open-source reproducibility path

## Main Risk

JSON may not always minimize token count. The paper should avoid overclaiming that structured output is always shorter. The stronger and more defensible claim is that structured output improves the trade-off between token usage, parsing reliability, and task success, especially for local small models.

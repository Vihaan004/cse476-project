# CSE 476 Final Project

This is our submission for the CSE 476 final project: a general-purpose
reasoning agent that answers arbitrary problem-solving questions using
inference-time techniques on top of the provided ASU Research Compute (SOL)
LLM API.

The agent is built around the `qwen3-30b-a3b-instruct-2507` model and stays
within the assignment's 20-LLM-calls-per-question budget.

## Folder structure

```
src/
  generate_answers.py      # batch runner, reads input json and writes answers json
  evaluate_answers.py      # offline accuracy script for labeled dev splits
  agent/
    client.py              # http client for the SOL api
    router.py              # decides what kind of question it is
    graph.py               # main agent loop and inference techniques
    tools.py               # calculator tool
    normalize_answer.py    # cleans the model output into the required format
    call_counter.py        # tracks how many calls we've used per question
data/
  input/                   # provided test/dev json files
  output/                  # answers written here
docs/                      # the project pdf and the provided template
```


## Constraints we follow

- Can only call the SOL endpoint at `https://openai.rc.asu.edu/v1` using the
  `qwen3-30b-a3b-instruct-2507` model (set in `client.py` and overridable
  via `.env`). No GPT, Claude, or other external LLMs are used.
- No paid APIs, no search APIs, no internet calls other than the SOL one.
- No full delegation: the calculator only does arithmetic, the model still
  has to decide what arithmetic to do.
- The hard 20-call limit is enforced by `CallCounter`.

## Setup

1. Make a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate          # macOS / Linux
   venv\Scripts\activate             # Windows
   ```

2. Install the package in editable mode:
   ```bash
   python -m pip install -e .
   ```

   This installs the dependencies (`requests`, `python-dotenv`) and registers
   two console scripts: `generate-answers` and `evaluate-answers`.

3. Copy the env template and fill in your SOL API key:
   ```bash
   cp .env.example .env
   ```

   The variables we read are:
   - `OPENAI_API_KEY` (or `LLM_API_KEY`) — required, this is the SOL key
     from the ASU Research Computing dashboard.
   - `API_BASE` — defaults to `https://openai.rc.asu.edu/v1`, only change
     this if you are pointing at a different endpoint.
   - `MODEL_NAME` — defaults to `qwen3-30b-a3b-instruct-2507`. The final
     submission has to work with this model.

## Running it

The input/output paths are set at the top of `src/generate_answers.py`. There
are commented-out blocks for the smoke set, dev set, and the real test set.
uncomment the pair you want and comment the others out. By default it points
at the official test file:

```python
INPUT_PATH  = ROOT / "data" / "input" / "cse_476_final_project_test_data.json"
OUTPUT_PATH = ROOT / "data" / "output" / "cse_476_final_project_answers.json"
```

Then run from the project root:

```bash
generate-answers
```

or equivalently:

```bash
python src/generate_answers.py
```

A few things the runner does that are worth knowing:

- It runs questions in parallel with a `ThreadPoolExecutor` (`MAX_WORKERS = 8`).
- It saves progress every `SAVE_EVERY = 10` finished questions, using a
  temp-file rename so the output file is never half-written if the run
  crashes.
- On startup it loads any existing output file and skips questions that
  already have a non-empty, non-placeholder answer. So you can stop and
  restart the run without redoing work.
- At the end it re-reads the file and runs `validate_results`, which checks
  that every entry has a string `"output"` field and that no answer is
  longer than 5000 characters.

If something goes wrong on a single question it is caught and the answer is
set to `"unknown"` so the run keeps going.

## Running the offline evaluator

`src/evaluate_answers.py` compares a predicted answers file against an
expected answers file (only useful for the labeled dev split, not for the
hidden test set). Edit the paths at the top of the file, then:

```bash
evaluate-answers
```

It prints per-domain accuracy and overall accuracy.

## Reproducing our results

1. Set up the venv and install as above.
2. Put the official test json at `data/input/cse_476_final_project_test_data.json`.
3. Make sure `.env` has a valid SOL key and `MODEL_NAME=qwen3-30b-a3b-instruct-2507`.
4. Run `generate-answers`.
5. The submission file is written to `data/output/cse_476_final_project_answers.json`.

The first-pass calls all use `temperature=0.0`. Only the second
self-consistency sample and the tree-of-thought call use a higher
temperature, so most questions are deterministic given the model.

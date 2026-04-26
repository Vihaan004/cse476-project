#!/usr/bin/env python3
"""
Generate a placeholder answer file that matches the expected auto-grader format.

Replace the placeholder logic inside `build_answers()` with your own agent loop
before submitting so the ``output`` fields contain your real predictions.

Reads the input questions from cse_476_final_project_test_data.json and writes
an answers JSON file where each entry contains a string under the "output" key.
"""

from __future__ import annotations

from importlib.resources import path
import json
from pathlib import Path
from typing import Any, Dict, List
from agent.graph import invoke_agent
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent

# INPUT_PATH = ROOT / "data" / "input" / "smoke.json"                                 # for sanity
# OUTPUT_PATH = ROOT / "data" / "output" / "smoke.json"

# INPUT_PATH = ROOT / "data" / "input" / "cse_476_final_project_dev_data.json"      # for development
# OUTPUT_PATH = ROOT / "data" / "output" / "dev.json"

# INPUT_PATH = ROOT / "data" / "input" / "test.json"      # for development
# OUTPUT_PATH = ROOT / "data" / "output" / "test_output.json"

INPUT_PATH = ROOT / "data" / "input" / "cse_476_final_project_test_data.json"     # for evaluation
OUTPUT_PATH = ROOT / "data" / "output" / "cse_476_final_project_answers.json"


MAX_WORKERS = 8
SAVE_EVERY = 10


def load_questions(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, list):
        raise ValueError("Input file must contain a list of question objects.")
    return data

def load_existing_answers(n: int) -> List[Dict[str, str]]:
    if OUTPUT_PATH.exists():
        try:
            with OUTPUT_PATH.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
            if isinstance(data, list) and len(data) == n:
                return data
        except Exception:
            pass

    return [{"output": ""} for _ in range(n)]


def save_answers(answers: List[Dict[str, str]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = OUTPUT_PATH.with_suffix(".tmp")

    with tmp_path.open("w", encoding="utf-8") as fp:
        json.dump(answers, fp, ensure_ascii=False, indent=2)

    tmp_path.replace(OUTPUT_PATH)


def is_done(answer):
    output = str(answer.get("output", "")).strip()
    return (
        output != "" and
        not output.startswith("Placeholder answer")
    )

def answer_one(idx: int, question: Dict[str, Any]) -> tuple[int, str]:
    print(f"Starting question {idx + 1}", flush=True)

    try:
        real_answer = invoke_agent(question["input"])
        real_answer = str(real_answer).strip()
        if not real_answer:
            real_answer = "unknown"
    except Exception as e:
        print(f"Error on question {idx + 1}: {type(e).__name__}", flush=True)
        real_answer = "unknown"

    print(f"Completed question {idx + 1}: {real_answer[:100]}", flush=True)
    return idx, real_answer


def build_answers(questions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    answers = load_existing_answers(len(questions))
    total = len(questions)

    todo = [
        (i, q)
        for i, q in enumerate(questions)
        if not is_done(answers[i])
    ]

    print(f"Total questions: {total}", flush=True)
    print(f"Already completed: {total - len(todo)}", flush=True)
    print(f"Remaining: {len(todo)}", flush=True)

    completed_since_save = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(answer_one, i, q)
            for i, q in todo
        ]

        for future in as_completed(futures):
            idx, real_answer = future.result()
            answers[idx] = {"output": real_answer}

            completed_since_save += 1

            if completed_since_save >= SAVE_EVERY:
                save_answers(answers)
                done_count = sum(1 for a in answers if is_done(a))
                print(f"Saved progress: {done_count}/{total}", flush=True)
                completed_since_save = 0

    save_answers(answers)
    return answers


def validate_results(
    questions: List[Dict[str, Any]], answers: List[Dict[str, Any]]
) -> None:
    if len(questions) != len(answers):
        raise ValueError(
            f"Mismatched lengths: {len(questions)} questions vs {len(answers)} answers."
        )
    for idx, answer in enumerate(answers):
        if "output" not in answer:
            raise ValueError(f"Missing 'output' field for answer index {idx}.")
        if not isinstance(answer["output"], str):
            raise TypeError(
                f"Answer at index {idx} has non-string output: {type(answer['output'])}"
            )
        if len(answer["output"]) >= 5000:
            raise ValueError(
                f"Answer at index {idx} exceeds 5000 characters "
                f"({len(answer['output'])} chars). Please make sure your answer does not include any intermediate results."
            )


def main() -> None:
    questions = load_questions(INPUT_PATH)
    answers = build_answers(questions)

    save_answers(answers)

    with OUTPUT_PATH.open("r", encoding="utf-8") as fp:
        saved_answers = json.load(fp)

    validate_results(questions, saved_answers)

    print(
        f"Wrote {len(answers)} answers to {OUTPUT_PATH} "
        "and validated format successfully.",
        flush=True,
    )


if __name__ == "__main__":
    main()


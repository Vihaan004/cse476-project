#!/usr/bin/env python3
"""
Generate an answer file matching the expected auto-grader format.

Dev mode uses a stratified sample (5 questions per domain) so we get an honest
per-domain accuracy signal for the same call budget as a flat first-N slice.
The sample is deterministic via SAMPLE_SEED so a teammate re-running the eval
hits the same 25 questions.

For final submission, switch INPUT_PATH/OUTPUT_PATH to the test set and call
``build_answers(load_questions(INPUT_PATH))`` directly (no sampling).
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from agent.graph import invoke_agent

ROOT = Path(__file__).resolve().parent.parent

# INPUT_PATH = ROOT / "data" / "input" / "smoke.json"                                 # for sanity
# OUTPUT_PATH = ROOT / "data" / "output" / "smoke.json"

INPUT_PATH = ROOT / "data" / "input" / "cse_476_final_project_dev_data.json"      # for development
OUTPUT_PATH = ROOT / "data" / "output" / "dev.json"
SAMPLED_QUESTIONS_PATH = ROOT / "data" / "output" / "dev_sampled_questions.json"

# INPUT_PATH = ROOT / "data" / "input" / "cse_476_final_project_test_data.json"     # for evaluation
# OUTPUT_PATH = ROOT / "data" / "output" / "cse_476_final_project_answers.json"

PER_DOMAIN = 5
SAMPLE_SEED = 42


def load_questions(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, list):
        raise ValueError("Input file must contain a list of question objects.")
    return data


def stratified_sample(
    questions: List[Dict[str, Any]],
    per_domain: int = PER_DOMAIN,
    seed: int = SAMPLE_SEED,
) -> List[Dict[str, Any]]:
    """Pick `per_domain` questions from each domain. Deterministic via seed."""
    by_domain: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for q in questions:
        by_domain[q.get("domain", "unknown")].append(q)

    rng = random.Random(seed)
    sample: List[Dict[str, Any]] = []
    for domain in sorted(by_domain):
        items = by_domain[domain]
        sample.extend(rng.sample(items, min(per_domain, len(items))))
    return sample


def build_answers(questions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Run the agent on each question. Saves incrementally and never
    aborts on a single failure — failed questions get an empty output so
    we still have a valid file at the end."""
    answers: List[Dict[str, str]] = []
    total = len(questions)
    for idx, question in enumerate(questions, start=1):
        domain = question.get("domain", "?")
        print(f"  [{idx:2d}/{total}] {domain:18s} ... ", end="", flush=True)
        try:
            real_answer = invoke_agent(question["input"])
            print(f"OK ({len(real_answer)} chars)")
        except Exception as exc:
            print(f"FAILED: {type(exc).__name__}: {exc}")
            real_answer = ""
        answers.append({"output": real_answer})
        # Persist after every call so a crash doesn't lose prior work.
        OUTPUT_PATH.write_text(
            json.dumps(answers, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
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
    all_questions = load_questions(INPUT_PATH)
    questions = stratified_sample(all_questions)

    counts: Dict[str, int] = defaultdict(int)
    for q in questions:
        counts[q.get("domain", "unknown")] += 1
    print("Stratified sample:")
    for domain in sorted(counts):
        print(f"  {domain:20s} {counts[domain]}")
    print(f"  TOTAL                {sum(counts.values())}")
    print()

    # Persist sampled questions up front so the eval script can join even
    # if the agent run crashes partway through.
    SAMPLED_QUESTIONS_PATH.write_text(
        json.dumps(questions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    answers = build_answers(questions)

    with OUTPUT_PATH.open("r", encoding="utf-8") as fp:
        saved_answers = json.load(fp)
    validate_results(questions, saved_answers)
    print(
        f"Wrote {len(answers)} answers to {OUTPUT_PATH}\n"
        f"Wrote sampled questions to {SAMPLED_QUESTIONS_PATH}\n"
        "Validated format successfully."
    )


if __name__ == "__main__":
    main()

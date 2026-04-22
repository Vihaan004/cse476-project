import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

PREDICTED_PATH = ROOT / "data" / "output" / "eval.json"
EXPECTED_PATH = ROOT / "data" / "input" / "eval.json"
RESULT_PATH = ROOT / "data" / "eval" / "results.json"

def load_json(path: Path) -> list[dict]:
    with path.open("r") as fp:
        data = json.load(fp)
    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of objects.")
    return data


def main() -> None:
    predicted = load_json(PREDICTED_PATH)
    expected = load_json(EXPECTED_PATH)

    if len(predicted) != len(expected):
        print("ERROR: Mismatch in number of items in predicted and expected outputs.")
        return

    results = []
    domain_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    overall_correct = 0
    overall_total = 0

    for pred_item, exp_item in zip(predicted, expected):
        pred_output = pred_item.get("output")
        exp_output = exp_item.get("output")
        domain = exp_item.get("domain", "unknown")
        input_text = exp_item.get("input")

        is_correct = pred_output == exp_output

        results.append(
            {
                "input": input_text,
                "predicted": pred_output,
                "expected": exp_output,
                "domain": domain,
            }
        )

        domain_stats[domain]["total"] += 1
        overall_total += 1

        if is_correct:
            domain_stats[domain]["correct"] += 1
            overall_correct += 1

    with RESULT_PATH.open("w") as fp:
        json.dump(results, fp, indent=2)

    print("Per-domain accuracy:")
    for domain in sorted(domain_stats):
        correct = domain_stats[domain]["correct"]
        total = domain_stats[domain]["total"]
        accuracy = (correct / total) if total else 0.0
        print(f"- {domain}: {correct}/{total} ({accuracy:.2%})")

    overall_accuracy = (overall_correct / overall_total) if overall_total else 0.0
    print(f"Overall accuracy: {overall_correct}/{overall_total} ({overall_accuracy:.2%})")


if __name__ == "__main__":
    main()
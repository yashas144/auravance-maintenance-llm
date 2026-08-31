"""
Validates the generated dataset against the schema and selects a random
subset for hand review. Run this after generate_dataset.py and before
committing the final dataset.

Usage:
    python validate_dataset.py --in ../data/raw_dataset.jsonl --review-frac 0.3
"""

import argparse
import json
import random
from pathlib import Path

REQUIRED_INPUT_KEYS = {
    "equipment_id", "equipment_type", "telemetry_summary",
    "predicted_failure_mode", "failure_probability", "time_to_failure_estimate",
}
REQUIRED_TARGET_KEYS = {
    "root_cause_hypothesis", "urgency", "suggested_action", "confidence", "reasoning",
}
VALID_URGENCY = {"low", "medium", "high", "critical"}


def validate_example(ex: dict, idx: int) -> list:
    errors = []
    if set(ex.get("input", {}).keys()) != REQUIRED_INPUT_KEYS:
        errors.append(f"[{idx}] input keys mismatch: {set(ex.get('input', {}).keys())}")
    if set(ex.get("target", {}).keys()) != REQUIRED_TARGET_KEYS:
        errors.append(f"[{idx}] target keys mismatch: {set(ex.get('target', {}).keys())}")
    target = ex.get("target", {})
    if target.get("urgency") not in VALID_URGENCY:
        errors.append(f"[{idx}] invalid urgency: {target.get('urgency')}")
    conf = target.get("confidence")
    if not isinstance(conf, (int, float)) or not (0 <= conf <= 1):
        errors.append(f"[{idx}] confidence out of range: {conf}")
    prob = ex.get("input", {}).get("failure_probability")
    if not isinstance(prob, (int, float)) or not (0 <= prob <= 1):
        errors.append(f"[{idx}] failure_probability out of range: {prob}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="infile", type=str, default="../data/raw_dataset.jsonl")
    parser.add_argument("--review-frac", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    examples = [json.loads(l) for l in Path(args.infile).read_text().splitlines() if l.strip()]

    all_errors = []
    for i, ex in enumerate(examples):
        all_errors.extend(validate_example(ex, i))

    print(f"Loaded {len(examples)} examples")
    if all_errors:
        print(f"FOUND {len(all_errors)} SCHEMA ERRORS:")
        for e in all_errors[:20]:
            print(f"  {e}")
        if len(all_errors) > 20:
            print(f"  ... and {len(all_errors) - 20} more")
    else:
        print("Schema validation: PASSED (all examples conform)")

    # Flag a random subset for human review
    random.seed(args.seed)
    review_n = int(len(examples) * args.review_frac)
    review_idx = set(random.sample(range(len(examples)), review_n))

    review_path = Path(args.infile).parent / "review_queue.jsonl"
    with open(review_path, "w") as f:
        for i in sorted(review_idx):
            f.write(json.dumps(examples[i]) + "\n")

    print(f"\nFlagged {review_n} examples ({args.review_frac:.0%}) for human review -> {review_path}")
    print("Review each one: does the target genuinely follow from the input? "
          "Fix or discard bad ones, then merge back into the final dataset.")


if __name__ == "__main__":
    main()

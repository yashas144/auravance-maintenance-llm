"""
Generates synthetic training examples for the maintenance-advisory fine-tune.

Each example pairs a telemetry summary + failure prediction (the kind of
output Auravance's XGBoost/LSTM models already produce) with a structured
maintenance recommendation (the target the LLM should learn to generate).

Usage:
    python generate_dataset.py --n 300 --seed 42 --out ../data/raw_dataset.jsonl

Design notes:
- Telemetry values are sampled from failure-mode-specific anomalous ranges
  (see domain_knowledge.py) so summaries stay physically plausible.
- failure_probability and urgency are derived from how far sensor readings
  deviate from normal, not assigned randomly, so the dataset has real
  internal structure for the model to learn.
- ~15% of examples deliberately fall in a "borderline" probability band
  (0.35-0.55) to teach the model to express medium confidence and
  medium urgency rather than only ever predicting extremes.
"""

import argparse
import json
import random
from pathlib import Path

from domain_knowledge import EQUIPMENT_PROFILES, SENSOR_DISPLAY, sample_value


def deviation_score(sensor: str, value: float, normal_range: tuple) -> float:
    lo, hi = normal_range
    mid = (lo + hi) / 2
    span = (hi - lo) / 2
    return min(abs(value - mid) / span, 3.0)  # cap extreme outliers


def urgency_from_probability(p: float) -> str:
    if p >= 0.80:
        return "critical"
    if p >= 0.60:
        return "high"
    if p >= 0.35:
        return "medium"
    return "low"


def time_to_failure(urgency: str) -> str:
    return {
        "critical": random.choice(["12-24 hours", "1-2 days"]),
        "high": random.choice(["3-5 days", "5-7 days"]),
        "medium": random.choice(["1-2 weeks", "2-3 weeks"]),
        "low": random.choice(["3-4 weeks", "1-2 months"]),
    }[urgency]


def generate_example(borderline: bool = False) -> dict:
    equipment_type = random.choice(list(EQUIPMENT_PROFILES.keys()))
    profile = EQUIPMENT_PROFILES[equipment_type]
    failure_mode = random.choice(list(profile["failure_modes"].keys()))
    fm = profile["failure_modes"][failure_mode]

    # Sample all sensors for this equipment; anomalous ones use the failure
    # mode's signature range, others stay in normal operating range.
    readings = {}
    deviations = []
    for sensor in profile["sensors"]:
        if sensor in fm["signature"]:
            lo, hi = fm["signature"][sensor]
            if borderline:
                # pull toward the low end of the anomalous range to create
                # a genuinely ambiguous, medium-confidence case
                hi = lo + (hi - lo) * 0.35
            val = sample_value(sensor, (lo, hi))
            deviations.append(deviation_score(sensor, val, (lo, hi)))
        else:
            val = sample_value(sensor)
        readings[sensor] = val

    avg_deviation = sum(deviations) / len(deviations) if deviations else 0.3
    failure_probability = round(min(0.15 + avg_deviation * 0.75, 0.97), 2)
    urgency = urgency_from_probability(failure_probability)
    tt_failure = time_to_failure(urgency)

    equipment_id = f"{equipment_type.upper()[:4]}-{random.randint(1000, 9999)}"
    readings_str = "; ".join(f"{SENSOR_DISPLAY[k]}: {v}" for k, v in readings.items())
    telemetry_summary = (
        f"Unit {equipment_id} ({equipment_type.replace('_', ' ')}) readings over "
        f"the past 6 hours — {readings_str}."
    )

    confidence = round(min(0.55 + avg_deviation * 0.15, 0.95), 2)

    anomalous_readings = ", ".join(
        f"{SENSOR_DISPLAY[k]} at {v}" for k, v in readings.items() if k in fm["signature"]
    )
    reasoning = (
        f"Sensor deviations consistent with {failure_mode.replace('_', ' ')}: "
        f"{anomalous_readings} fall outside normal operating range, matching the "
        f"known signature for this failure mode."
    )

    return {
        "input": {
            "equipment_id": equipment_id,
            "equipment_type": equipment_type,
            "telemetry_summary": telemetry_summary,
            "predicted_failure_mode": failure_mode.replace("_", " "),
            "failure_probability": failure_probability,
            "time_to_failure_estimate": tt_failure,
        },
        "target": {
            "root_cause_hypothesis": fm["root_cause"],
            "urgency": urgency,
            "suggested_action": fm["action"],
            "confidence": confidence,
            "reasoning": reasoning,
        },
        "human_reviewed": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="../data/raw_dataset.jsonl")
    parser.add_argument("--borderline-frac", type=float, default=0.15)
    args = parser.parse_args()

    random.seed(args.seed)
    n_borderline = int(args.n * args.borderline_frac)

    examples = []
    for i in range(args.n):
        examples.append(generate_example(borderline=(i < n_borderline)))
    random.shuffle(examples)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

    urgency_counts = {}
    for ex in examples:
        u = ex["target"]["urgency"]
        urgency_counts[u] = urgency_counts.get(u, 0) + 1

    print(f"Generated {len(examples)} examples -> {out_path}")
    print(f"Urgency distribution: {urgency_counts}")


if __name__ == "__main__":
    main()

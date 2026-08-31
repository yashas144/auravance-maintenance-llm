# Training Data Schema

This document defines the input/output structure for the maintenance-advisory
fine-tuning dataset. Every training example must conform to this schema.

## Input

| Field | Type | Description |
|---|---|---|
| `equipment_id` | string | Unique identifier, e.g. `"PUMP-1042"` |
| `equipment_type` | string | e.g. `"centrifugal_pump"`, `"conveyor_motor"`, `"compressor"`, `"bearing_assembly"` |
| `telemetry_summary` | string | Natural-language summary of recent sensor readings (vibration, temperature, pressure, RPM trends) |
| `predicted_failure_mode` | string | Output from the Auravance XGBoost/LSTM model, e.g. `"bearing_wear"`, `"misalignment"`, `"cavitation"` |
| `failure_probability` | float | 0.0–1.0, model confidence in the failure prediction |
| `time_to_failure_estimate` | string | e.g. `"3-7 days"`, `"< 24 hours"`, `"2-4 weeks"` |

### Example input

```json
{
  "equipment_id": "PUMP-1042",
  "equipment_type": "centrifugal_pump",
  "telemetry_summary": "Vibration amplitude increased 40% over 72 hours (2.1mm/s -> 2.9mm/s). Bearing temperature trending up, now 68C vs 55C baseline. No change in flow rate or discharge pressure.",
  "predicted_failure_mode": "bearing_wear",
  "failure_probability": 0.82,
  "time_to_failure_estimate": "3-7 days"
}
```

## Output (target JSON)

| Field | Type | Description |
|---|---|---|
| `root_cause_hypothesis` | string | Best-guess mechanical explanation, grounded in the telemetry |
| `urgency` | enum | `"low"` \| `"medium"` \| `"high"` \| `"critical"` |
| `suggested_action` | string | Concrete next step (inspect, lubricate, schedule replacement, shut down, etc.) |
| `confidence` | float | 0.0–1.0, model's confidence in this recommendation |
| `reasoning` | string | 1-2 sentences tying the recommendation back to specific telemetry values |

### Example output

```json
{
  "root_cause_hypothesis": "Progressive bearing wear, likely lubrication degradation or early-stage race damage",
  "urgency": "high",
  "suggested_action": "Schedule bearing inspection within 48 hours; check lubrication levels and quality before next run cycle",
  "confidence": 0.78,
  "reasoning": "The combined rise in vibration amplitude and bearing temperature without a corresponding change in flow or pressure is a classic bearing degradation signature rather than a process-side issue."
}
```

## Dataset composition targets

- 150-400 examples total for the first fine-tuning pass
- Cover at least 5 distinct `equipment_type` values
- Cover at least 6 distinct `predicted_failure_mode` values
- Urgency distribution should NOT default to "high" every time — target a
  realistic spread, roughly: low 15%, medium 35%, high 35%, critical 15%
- Include a handful (5-10%) of "edge case" examples: ambiguous telemetry,
  conflicting signals, low failure_probability but still worth flagging —
  these make the fine-tune more robust than a dataset of only clean-cut cases

# Synthetic Data Generation Prompt

Use this prompt with Claude/GPT-4 to generate candidate training examples.
Every output must be hand-reviewed before inclusion in the final dataset.

---
You are an industrial reliability engineer. Given the following equipment
telemetry summary and failure prediction, generate a structured maintenance
recommendation.

Equipment type: {equipment_type}
Telemetry summary: {telemetry_summary}
Predicted failure mode: {predicted_failure_mode}
Failure probability: {failure_probability}
Time to failure estimate: {time_to_failure_estimate}

Return ONLY valid JSON matching this schema:
{schema}

Be specific and realistic. Vary urgency levels and failure modes across the dataset — don't default to "high" urgency every time.
---
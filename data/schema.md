# Training Data Schema

## Input
- equipment_id: string
- equipment_type: string (e.g. "centrifugal_pump", "conveyor_motor")
- telemetry_summary: string (natural language summary of sensor readings)
- predicted_failure_mode: string (from Auravance XGBoost/LSTM output)
- failure_probability: float (0-1)
- time_to_failure_estimate: string (e.g. "3-7 days")

## Output (target JSON)
{
  "root_cause_hypothesis": "string",
  "urgency": "low | medium | high | critical",
  "suggested_action": "string",
  "confidence": "float (0-1)",
  "reasoning": "string (brief explanation tying prediction to telemetry)"
}
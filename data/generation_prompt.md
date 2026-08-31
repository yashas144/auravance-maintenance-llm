# Synthetic Data Generation Prompt

Use this prompt with an LLM (Claude, GPT-4, etc.) to generate candidate
training examples in bulk. **Every generated example must be hand-reviewed
before inclusion in the final dataset** — target at least 30% manual
correction/rewriting to avoid inheriting the generator model's blind spots
and to ensure the recommendations are mechanically sound.

---

## Prompt template

```
You are an industrial reliability engineer with 20 years of experience
in predictive maintenance for rotating equipment. Given the following
equipment telemetry summary and failure prediction, generate a structured
maintenance recommendation.

Equipment type: {equipment_type}
Telemetry summary: {telemetry_summary}
Predicted failure mode: {predicted_failure_mode}
Failure probability: {failure_probability}
Time to failure estimate: {time_to_failure_estimate}

Return ONLY valid JSON matching this schema (no markdown, no commentary):

{
  "root_cause_hypothesis": "string",
  "urgency": "low | medium | high | critical",
  "suggested_action": "string",
  "confidence": float between 0 and 1,
  "reasoning": "string, 1-2 sentences tying the recommendation to specific
                telemetry values mentioned in the input"
}

Guidelines:
- Ground the reasoning in the SPECIFIC numbers given in the telemetry
  summary, not generic advice.
- Vary urgency realistically — do not default to "high" for every case.
  A high failure_probability with a long time_to_failure_estimate might
  still be "medium" urgency if the action can be scheduled rather than
  immediate.
- confidence should reflect genuine uncertainty when the telemetry is
  ambiguous — don't always output 0.8-0.9.
- suggested_action should be concrete and actionable (a technician should
  be able to act on it directly), not vague ("monitor closely").
```

## Scenario generation (to vary inputs before running the prompt above)

To avoid a repetitive dataset, first generate diverse INPUT scenarios,
then run each through the prompt above. Vary along these axes:

- **equipment_type**: centrifugal_pump, conveyor_motor, compressor,
  bearing_assembly, gearbox, cooling_fan, hydraulic_press
- **failure_mode**: bearing_wear, misalignment, cavitation, imbalance,
  lubrication_failure, thermal_overload, belt_slippage, seal_degradation
- **signal pattern**: single-signal drift (only vibration OR only temp),
  multi-signal correlation (vibration + temp together), sudden spike vs.
  gradual trend, intermittent/noisy signal, signal that plateaus after
  initial rise
- **severity**: early-stage (small deviation from baseline), mid-stage
  (clear deviation, no imminent risk), late-stage (large deviation, short
  time_to_failure_estimate)

Combining these axes when writing telemetry_summary inputs is what
produces a dataset the model can actually generalize from, rather than
one where it just memorizes a handful of templates.

## Review checklist (apply to every generated example before inclusion)

- [ ] Does the reasoning cite the actual numbers from telemetry_summary?
- [ ] Is the suggested_action something a real technician could execute?
- [ ] Is the urgency level defensible given failure_probability AND
      time_to_failure_estimate together (not just one of them)?
- [ ] Is confidence varied and not clustered at 0.8-0.9 for everything?
- [ ] Does this example duplicate the failure_mode + equipment_type
      combination of an existing example? (cap duplicates to keep variety)

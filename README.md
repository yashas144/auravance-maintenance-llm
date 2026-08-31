# Auravance Maintenance-Advisory LLM

Fine-tuning a small open-source LLM to generate structured maintenance
recommendations from equipment telemetry and failure predictions — extending
the [Auravance](https://github.com/yashas144/Auravance) predictive
maintenance platform with natural-language diagnostic reasoning.

## Status: In progress

- [x] Define dataset schema and generation methodology
- [x] Generate 300 synthetic training examples, validated against schema
- [ ] Hand-review the flagged 30% review queue and merge corrections
- [ ] Fine-tune base model (LoRA) with tracked experiments
- [ ] Build evaluation suite (base vs. fine-tuned comparison)
- [ ] Quantize and deploy behind a FastAPI endpoint
- [ ] Wire into Auravance dashboard

## Dataset generation approach

Rather than generating examples purely freeform from an LLM prompt, the
dataset is built from a **structured domain knowledge base**
(`scripts/domain_knowledge.py`) encoding realistic equipment types, failure
modes, root causes, and their telemetry signatures (e.g. bearing wear on a
centrifugal pump produces elevated vibration + bearing temperature within
specific ranges). `failure_probability`, `urgency`, and `confidence` are
*derived* from how far sampled sensor values deviate from the failure
mode's known signature — not assigned randomly — so the dataset has real
internal structure for the model to learn, and the urgency distribution
comes out naturally varied (not defaulted to one class).

This keeps the synthetic data physically plausible and reviewable, and
makes it straightforward to extend with real Auravance sensor data later.

## Project structure

```
data/
  schema.md              # Input/output data schema for training examples
  generation_prompt.md   # LLM-based generation approach (alternative/supplementary to domain-rule generation)
  raw_dataset.jsonl       # 300 generated (input, target) training pairs
  review_queue.jsonl      # 30% random sample flagged for hand review
scripts/
  domain_knowledge.py     # Equipment/failure-mode/telemetry-signature knowledge base
  generate_dataset.py      # Generates the dataset from domain knowledge
  validate_dataset.py      # Schema validation + review queue selection
```

## Running it

```bash
cd scripts
pip install -r requirements.txt   # stdlib only for this stage
python generate_dataset.py --n 300 --seed 42 --out ../data/raw_dataset.jsonl
python validate_dataset.py --in ../data/raw_dataset.jsonl --review-frac 0.3
```

## Why this exists

Auravance's existing models (XGBoost/LSTM) predict *that* a failure is
likely and *when*. This project adds the *why* and *what to do about it* —
a fine-tuned model that turns a raw prediction into an actionable,
explainable maintenance recommendation a technician can act on.

More detail on methodology, training results, and evaluation metrics will
be added as each stage is completed.

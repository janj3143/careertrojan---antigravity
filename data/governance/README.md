# Governance Outcome Labels

Date: 2026-02-24

## Purpose

This folder provides seed artifacts for role-outcome ground-truth tracking used by governance/eval gates.

## Files

- `outcome_labels.jsonl`: canonical event records (JSONL, one object per line).

## JSONL Record Contract

Required fields:

- `label_id`: unique ID.
- `role`: `admin|user|mentor|cross_role`.
- `journey`: logical flow name.
- `outcome`: canonical result label.
- `ground_truth`: boolean.
- `source`: data source (`manual_review|harness|telemetry`).
- `evidence_refs`: array of file paths, endpoint names, or trace IDs.
- `created_at`: ISO 8601 UTC timestamp.

Optional fields:

- `severity`: `P0|P1|P2|P3` for negative outcomes.
- `notes`: free-text context.

## Canonical Outcome Labels

- Positive: `success`, `state_transition_valid`, `schema_valid`, `authorization_enforced`
- Negative: `contract_mismatch`, `state_transition_invalid`, `schema_invalid`, `authorization_failure`, `latency_slo_breach`

# Signal Lifecycle Report

Repository root: J:\Codec - runtime version\Antigravity\careertrojan

## Summary

- Signals extracted: 33
- Signals with consumer evidence: 9
- Signals with execution/visibility evidence: 9

## Lifecycle Audit

1. Signal extraction: variable and feature-like assignments discovered in Python functions
2. Signal response: signal usage in predict/classify/rank/infer/evaluate/score contexts
3. Signal execution: signal references in return payloads and frontend visual/output files
4. Noise filtering: excludes tools/tests/scripts/docs/discovery outputs from analysis

## Sample Signals

- action_confidence: consumers=0, executions=0
- allowed_features: consumers=0, executions=0
- avg_confidence: consumers=2, executions=0
- base_features: consumers=0, executions=0
- candidate_features: consumers=1, executions=0
- confidence: consumers=4, executions=8
- confidence_modifier: consumers=1, executions=0
- confidence_score: consumers=0, executions=1
- confidence_scores: consumers=1, executions=0
- confidence_trend: consumers=0, executions=0
- confidence_values: consumers=0, executions=0
- confidences: consumers=1, executions=0
- feature_dict: consumers=0, executions=0
- feature_name: consumers=0, executions=1
- feature_names: consumers=2, executions=0
- feature_summary: consumers=0, executions=0
- features: consumers=5, executions=1
- high_impact: consumers=0, executions=0
- impact: consumers=0, executions=2
- job_features: consumers=0, executions=0
- market_signals: consumers=0, executions=1
- model_features: consumers=0, executions=0
- nlp_confidence: consumers=1, executions=0
- overlap: consumers=0, executions=1
- overlap_skills: consumers=0, executions=1
- portal_features: consumers=0, executions=0
- progression: consumers=0, executions=1
- progressions: consumers=0, executions=0
- tech_indicators: consumers=0, executions=0
- top_features_path: consumers=0, executions=0
- total_impact: consumers=0, executions=0
- vague_indicators: consumers=0, executions=0
- weighted_confidence: consumers=0, executions=0

## Output Files

- discovery_output/signal_inventory.json
- discovery_output/signal_consumers.json
- discovery_output/signal_execution_map.json
- discovery_output/signal_lifecycle_report.md
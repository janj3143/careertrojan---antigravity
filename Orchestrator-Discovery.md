# CareerTrojan AI Orchestrator Discovery

## Discovery-First Rule
Before implementation, refactoring, or orchestration upgrades, CareerTrojan must run a structured discovery pass. Architecture decisions should be based on repository evidence, not memory.

Sequence:
1. Discover the current system as it exists.
2. Document findings in machine- and human-readable outputs.
3. Map gaps, duplicates, dead paths, and active paths.
4. Define target architecture against discovered reality.
5. Implement only after discovery is complete.

## Purpose
This document is the discovery blueprint for the CareerTrojan hybrid AI core.

Primary objective:
- Ensure mathematical and analytical engines perform decision work.
- Ensure the LLM explains decisions in plain, career-focused language.

Core rule:
- The maths decides.
- The LLM explains.

## Why Discovery Must Come First
CareerTrojan now has enough surface area that memory-only understanding is unreliable. Risks include:
- Existing models that are not routed into production.
- Duplicate endpoints with different names.
- Services imported but never called.
- LLM routes doing decision work that should be inference work.
- Charts bound to placeholders instead of live model output.
- Tests that verify syntax but not orchestration integrity.
- Duplicate utilities causing behavior drift.

## Discovery Objectives
Discovery must answer, with evidence:
- What code exists.
- What code is active in runtime paths.
- What code is duplicated.
- What code is dormant or dead.
- What code is partially wired.
- What models are present and where.
- What data each model consumes.
- Which endpoints expose live analytical behavior.
- Which charts are backed by live outputs.
- What observability exists.
- What is missing for a production hybrid AI orchestrator.

## Required Discovery Outputs
Produce the following artifacts during discovery:
- `system_inventory.md`
- `endpoint_inventory.md`
- `service_dependency_map.md`
- `ai_model_registry.md`
- `feature_input_matrix.md`
- `routing_trace_report.md`
- `duplicate_and_dead_code_report.md`
- `visualisation_data_binding_report.md`
- `test_coverage_gap_report.md`
- `implementation_readiness_report.md`

## Discovery Methodology (VS Code)

### Step 1: Structural Inventory
Capture all major folders and files for:
- Apps and portals.
- Backend services.
- Routers.
- Model directories.
- Scoring utilities.
- Visualization modules.
- Tests.
- Scripts.
- Deployment files.
- Environment configs.
- Name/function duplicates.

### Step 2: Runtime Entrypoints
Identify true entrypoints:
- FastAPI app entrypoints.
- Worker entrypoints.
- React bootstraps.
- Scheduled jobs.
- Webhook receivers.
- Queue consumers.

### Step 3: Dependency Tracing
Trace import and call relationships to find:
- True execution paths.
- Unused modules.
- Circular paths.
- Shadow implementations.

### Step 4: Endpoint Mapping
For every API route, record:
- Path.
- Request model.
- Response model.
- Service called.
- Live logic status.
- Model inference status.
- User-visible output status.
- Test coverage status.

### Step 5: AI Logic Discovery
For each analytical component, record:
- File location.
- Class/function names.
- Input features.
- Output schema.
- Invocation path (direct/indirect).
- Downstream endpoint/workflow usage.
- Impact on final score.
- Impact on charts and explanation text.

### Step 6: Dataflow Trace
Trace end-to-end runtime flow:
`upload -> parser -> feature generation -> model inference -> aggregation -> explanation -> visualization`

Annotate each handoff as:
- Implemented.
- Partial.
- Mocked.
- Duplicated.
- Broken.
- Untested.

### Step 7: Visual Binding Verification
For each spider chart, heatmap, covey lens, trend chart, or score card, verify:
- Data source.
- Static vs live source.
- Calculating service.
- Mapping to real model outputs.
- Presence of fallback/placeholder values.

### Step 8: Test and Observability Audit
Capture:
- Unit tests.
- Integration tests.
- Route tests.
- Model tests.
- Orchestration tests.
- Logging hooks.
- Metrics.
- Exception capture paths.
- Runtime diagnostics.

### Step 9: Gap Classification
Classify each component as:
- Live and working.
- Live but fragile.
- Partially wired.
- Dormant.
- Duplicated.
- Legacy.
- Missing.

### Step 10: Readiness Summary
Produce a short implementation-readiness summary:
- What can be kept.
- What must be rewired.
- What must be merged.
- What must be retired.
- What must be built before production orchestration.

## Practical Tooling
Recommended tooling inside VS Code:
- Workspace-wide search.
- Symbol search.
- References and call hierarchy.
- Python import analysis.
- TypeScript route analysis.
- Dependency graph generation.
- Endpoint scanners.
- Test discovery commands.
- Structured markdown output scripts.

Guiding principle:
- Do not rely on recollection when the repository can reveal the truth.

## Target Hybrid Architecture (Post-Discovery)

```
User Input
  -> Ingestion Layer
  -> Parsing and Extraction Layer
  -> Feature Engineering Layer
  -> AI Orchestrator
  -> Model Ensemble
      - Bayesian Engine
      - Regression Engine
      - Neural or Similarity Engine
      - Expert Rules Engine
      - NLP and Semantic Engine
      - Confidence Engine
  -> Inference Aggregator
  -> Decision Object
  -> LLM Explanation Layer
  -> Visualization Layer
```

## Design Contracts

### Layer Separation
Analytical layer responsibilities:
- Probability.
- Regression.
- Similarity.
- Rules.
- Confidence.

Interpretive layer responsibilities:
- Human-readable explanation.
- Recommendation framing.
- Priority ordering.
- Confidence-aware communication.

### Orchestrator Responsibilities
The orchestrator must:
- Receive normalized feature bundles.
- Decide which models run by context.
- Dispatch and collect model outputs.
- Validate output quality and confidence.
- Resolve conflicts and apply aggregation weights.
- Emit a unified decision object.
- Forward payloads to explanation and visualization.
- Log model contributions for observability.

### Decision Object Contract
All analysis routes should emit a standard decision object with:
- Analysis identifiers.
- Dimension scores.
- Model output blocks.
- Key findings and risks.
- Recommendations.
- Explanation payload.
- Visualization payload.

## What To Upload After Discovery
Return a grounded markdown pack that includes:
- Active entrypoints.
- FastAPI route inventory.
- Services actually called.
- Model inventory and inputs.
- Feature and scoring modules.
- Visualization modules and bindings.
- Duplicates and dead code.
- Current test coverage status.
- Known broken or uncertain paths.
- Notes on live vs theoretical behavior.

## Working Rule for Next Phase
Implementation decisions are not final until discovery evidence exists. This document should be used in two modes:
1. Current mode: discovery-first strategic guide.
2. Next mode: implementation blueprint grounded by discovery outputs.

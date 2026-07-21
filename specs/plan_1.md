# DOE Python Core — Minimal Plan

## Goal
Build and verify the minimum workflow needed to:
1. parse factor input from CSV,
2. create a valid `Experiment`,
3. persist a minimal JSON `WorkflowState`.

This first milestone deliberately stops before design generation, results import, analysis, and report generation.

## Scope for this milestone
- Python CLI project scaffolding.
- Domain models required for input handling:
  - `Factor`
  - `Response`
  - `Experiment`
  - `WorkflowState`
- CSV import for factor definitions.
- Validation of parsed input.
- Creation of an `Experiment` from validated input.
- Serialization of a minimal `WorkflowState` to JSON.

## Assumptions
- The initial analysis model is not implemented yet.
- The statistical model is fixed later; for now, no model selection is exposed in the CLI.
- JSON is the internal workflow state format.
- CSV is only an input format, not a persistence format.

## Step 0 — Project scaffolding
Create the minimal Python package structure and test layout.

### Deliverables
- `doe/`
- `doe/models/`
- `doe/imports/`
- `tests/`
- `doe/main.py`

### Acceptance criteria
- The project starts.
- Tests can be executed.
- The package imports correctly.

## Step 1 — Domain models
Implement the minimum domain models for the first milestone.

### Models
- `Factor`
- `Response`
- `Experiment`
- `WorkflowState`

### Requirements
- Each model has `schema_version`.
- Each model supports `validate()`.
- Each model supports `to_dict()` and `from_dict()`.
- Serialization uses JSON-compatible types only.
- Validation raises domain-specific exceptions.

### Acceptance criteria
- Valid objects can be created.
- Invalid objects raise the expected errors.
- Round-trip serialization works for each model.

## Step 2 — CSV import for factors
Implement a dedicated CSV import module for factor definitions.

### Requirements
- CSV parsing must be outside the domain layer.
- CSV rows are parsed into raw values first.
- Raw rows are mapped into `Factor` objects.
- Invalid rows produce row-level errors with:
  - row number,
  - field name,
  - invalid value.

### Acceptance criteria
- A valid factors CSV is parsed successfully.
- Invalid rows are reported clearly.
- Parsed factors are ready for domain validation.

## Step 3 — Create `Experiment`
Implement the function that creates an `Experiment` from validated input.

### Input
- experiment name
- description
- parsed factors
- responses
- `design_type`

### Requirements
- `Experiment` must be internally coherent.
- Factor names must be unique.
- Response names must be unique.
- The experiment must not contain runs, results, or analysis.

### Acceptance criteria
- A valid `Experiment` can be created from imported factors.
- Invalid combinations are rejected.
- The created experiment passes validation.

## Step 4 — Minimal `WorkflowState`
Implement persistence of the first workflow step.

### Requirements
- `WorkflowState` is JSON-serializable.
- It stores the current `step`.
- It stores the created `Experiment`.
- `design`, `results`, and `analysis` remain `null` for this milestone.

### Acceptance criteria
- A minimal workflow state can be saved to JSON.
- The saved state can be loaded back.
- The restored state matches the original one.

## Step 5 — First end-to-end test
Verify the complete input pipeline.

### Scenario
1. Load a factors CSV.
2. Parse and validate factors.
3. Create an `Experiment`.
4. Save a minimal `WorkflowState` to JSON.

### Acceptance criteria
- The pipeline succeeds end to end.
- The parsed factors are correct.
- The `Experiment` is coherent.
- The `WorkflowState` is valid and serializable.

## Out of scope for this milestone
- Design generation.
- Results import.
- Statistical analysis.
- Reporting.
- Model selection.
- Database support.

## Completion rule
Do not start the next milestone until all tests in this milestone pass.
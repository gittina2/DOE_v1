# DOE Python Core — Design Generation Plan

## Goal
Extend the workflow to generate and validate a full factorial experimental design from an existing `Experiment`, and persist the updated `WorkflowState`.

This milestone deliberately stops before result entry, statistical analysis, and report generation.

## Scope for this milestone
- Domain models required for design generation:
  - `Run`
  - `Block`
  - `Design`
- Full factorial design generator.
- Workflow orchestration for design generation.
- Validation of generated designs.
- Persistence of the updated `WorkflowState`.
- End-to-end verification from `Experiment` to `Design`.

## Assumptions
- A valid `Experiment` already exists.
- The workflow starts from `step = experiment_created`.
- Only the `full_factorial` design type is implemented in this milestone.
- Fractional factorial and other DOE algorithms are implemented later.
- JSON remains the workflow state format.
- Randomization support is implemented as defined by the domain model but advanced randomization strategies are out of scope.

---

# Step 1 — Design domain models

Implement the domain models required for experimental design generation.

## Models

- `Run`
- `Block`
- `Design`

`Run` and `Block` are implemented as nested domain types inside the `Design` module.

## Requirements

- Each model has `schema_version` where required by the specification.
- Each model supports `validate()`.
- Each model supports `to_dict()` and `from_dict()`.
- Serialization uses JSON-compatible types only.
- Validation raises domain-specific exceptions.
- Referential integrity is validated.
- Model invariants defined in the technical specification are enforced.

## Acceptance criteria

- Valid objects can be created.
- Invalid objects raise the expected exceptions.
- Round-trip serialization works.
- Referential integrity is verified during validation.

---

# Step 2 — Full factorial design generator

Implement the first DOE algorithm.

## Requirements

- Create a dedicated generator inside:

  `doe/designs/full_factorial.py`

- The generator receives a validated `Experiment`.
- The generator creates every required factor combination.
- Every generated run receives a system-generated `run_id`.
- Generated factor values satisfy the corresponding factor constraints.
- The number of generated runs matches the expected full factorial size.
- The generated design passes domain validation.

## Acceptance criteria

- A correct design is generated for continuous and categorical factors supported by the MVP.
- Every run contains all required factors.
- No duplicate run identifiers exist.
- Invalid experiments are rejected before generation.

---

# Step 3 — Generate `Design`

Implement the workflow function that creates a `Design` from an `Experiment`.

## Function

`generate_design()`

## Input

- `WorkflowState`
- optional generation parameters supported by the MVP

## Requirements

- The workflow state contains a valid `Experiment`.
- The experiment design type is supported.
- The appropriate design generator is selected.
- The generated `Design` is validated.
- The workflow state is updated.
- The workflow step becomes `design_generated`.

## Acceptance criteria

- A valid design is generated.
- Unsupported design types produce the expected error.
- Invalid workflow states are rejected.
- The updated workflow state passes validation.

---

# Step 4 — Persist updated `WorkflowState`

Extend persistence to include the generated design.

## Requirements

- The updated `WorkflowState` remains JSON serializable.
- The generated `Design` is included.
- `results` remains `null`.
- `analysis` remains `null`.
- References remain internally consistent after serialization.

## Acceptance criteria

- The updated workflow state can be saved.
- The saved workflow state can be restored.
- The restored design is identical to the original.
- Referential integrity is preserved.

---

# Step 5 — First end-to-end design workflow

Verify the complete workflow up to design generation.

## Scenario

1. Load an existing `WorkflowState`.
2. Validate the contained `Experiment`.
3. Generate a full factorial design.
4. Validate the generated design.
5. Save the updated `WorkflowState`.
6. Reload the saved workflow state.

## Acceptance criteria

- The complete workflow succeeds.
- The generated design is correct.
- All generated runs are valid.
- The workflow state is internally consistent.
- JSON round-trip succeeds without data loss.

---

# Out of scope for this milestone

- Result entry.
- CSV import for experimental results.
- `Results` and `ResultEntry`.
- Statistical analysis.
- Linear model estimation.
- Report generation.
- Fractional factorial generation.
- Blocking strategies beyond the domain model.
- Advanced randomization algorithms.
- Replication management.

---

# Completion rule

Do not start the next milestone until:

- all unit tests pass;
- all contract tests pass;
- JSON round-trip tests pass;
- end-to-end workflow tests pass;
- full factorial generation is validated for representative experiments.
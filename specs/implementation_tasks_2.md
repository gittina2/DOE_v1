# DOE Python Core — Implementation Task List (Design Generation Milestone)

This document outlines the ordered implementation tasks for the second milestone of the DOE Python Core project, based on the requirements and steps defined in `specs/plan2.md`.

---

## Task List Diagram
```mermaid
graph TD
    T01[Task 0.1: Extend Project Structure] --> T11[Task 1.1: Design Domain Exceptions]
    T11 --> T12[Task 1.2: Run Model]
    T11 --> T13[Task 1.3: Block Model]
    T11 --> T14[Task 1.4: Design Model]

    T14 --> T21[Task 2.1: Full Factorial Generator Interface]
    T21 --> T22[Task 2.2: Full Factorial Matrix Generation]
    T12 --> T23[Task 2.3: Convert Matrix to Run Objects]
    T14 --> T23
    T23 --> T24[Task 2.4: Assemble Validated Design]

    T14 --> T31[Task 3.1: Implement generate_design()]
    T24 --> T31
    T31 --> T32[Task 3.2: Workflow Transition Validation]

    T14 --> T41[Task 4.1: Extend WorkflowState Serialization]
    T31 --> T41

    T24 --> T51[Task 5.1: Design Generation Integration Test]
    T41 --> T51
```

---

## Step 0 — Project Structure Extension
### Task 0.1: Extend Package Layout for Design Modules

**Description:** Extend the existing package structure to support design generation:

- `doe/designs/`
- `doe/models/design.py`

    Nested domain types (`Run`, `Block`) are implemented inside the design domain module as defined by the technical specification.

**Dependencies:** None

**Acceptance Criteria:**
- Required directories and modules exist.
- Existing package imports continue to work.
- New modules can be imported without errors.

---

## Step 1 — Design Domain Models
### Task 1.1: Implement Design Domain Exception Classes

**Description:** Define domain-specific exceptions required for design generation and validation.

Expected exceptions include:

- `UnsupportedDesignTypeError`
- `RunCountMismatchError`
- `InvalidDesignMatrixError`
- `DuplicateRunIdError`
- `IncompatibleFactorDefinitionError`
- `InvalidWorkflowTransitionError`
- `InconsistentReferenceError`

**Dependencies:** Task 0.1

**Acceptance Criteria:**
- All exception classes are importable.
- All exceptions inherit from the common DOE domain exception base.
- Exceptions can be raised by validation and workflow layers.

---

### Task 1.2: Implement Run Domain Model

**Description:** Create the `Run` domain object representing a single experimental execution.

    Implement inside the design model module.

**Dependencies:** Task 1.1

**Acceptance Criteria:**
- Supports fields: `run_id`, `factor_values`, `metadata`
- `run_id` is system-generated and unique within a design.
- `validate()` verifies:
  - run identifier presence;
  - required factor values are present;
  - values respect factor constraints.
- Implements:
  - `to_dict()`
  - `from_dict()`

### Task 1.3: Implement Block Domain Model

**Description:** Create the optional block representation for grouped experimental runs.

**Dependencies:** Task 1.1

**Acceptance Criteria:**
- Supports fields: `block_id`, `run_ids`, `metadata`
- `validate()` verifies:
  - block identifier presence;
  - referenced run identifiers are valid.
- Implements:
  - `to_dict()`
  - `from_dict()`

Note:
- Validation rules involving relationships between multiple blocks
(e.g. a run belonging to multiple blocks) are enforced by the Design
aggregate validation layer.

---

### Task 1.4: Implement Design Domain Model

**Description:** Create the experimental design aggregate.

**Dependencies:** Task 1.2, Task 1.3

**Acceptance Criteria:**
- Supports fields: `schema_version`, `design_id`, `design_type`, `experiment_ref`, `runs`, `randomization`, `order`, `blocks`, `replications`, `metadata`
- Implements `validate()` enforcing:
  - at least one run exists;
  - run identifiers are unique;
  - all runs contain required experiment factors;
  - design type is consistent with the referenced experiment;
  - generated run count is valid;
  - order, if present, is a permutation of run IDs.
  - no run belongs to multiple blocks;
  - blocks are internally valid.
- Implements:
  - `to_dict()`
  - `from_dict()`

---  

## Step 2 — Full Factorial Design Generator
### Task 2.1: Define Design Generator Interface
**Description:** Create the abstraction boundary between workflow orchestration and DOE algorithms.
**Dependencies:** Task 1.4

**Acceptance Criteria:**
- Generator interface accepts a validated `Experiment`.
- Generator returns a validated `Design`.
- Workflow code does not depend on the internal algorithm implementation.

---

### Task 2.2: Implement Full Factorial Combination Generation
**Description:** Implement the full factorial algorithm in:
- `doe/designs/full_factorial.py`

**Dependencies:** Task 2.1

**Acceptance Criteria:**
- Generates all possible combinations of factor levels.
- Supports categorical factors.
- Supports continuous factors according to the MVP representation.
- Generated combinations match the expected factorial size.
- Invalid factor definitions are rejected.

---

### Task 2.3: Convert Factorial Matrix into Run Objects
**Description:** Convert generated factor combinations into validated `Run` domain objects.

**Dependencies:** Task 1.2, Task 2.2

**Acceptance Criteria:**
- Each generated run receives a unique system-generated `run_id`.
- Every run contains all experiment factors.
- Every generated run passes validation.
- Duplicate run identifiers are impossible.

---

### Task 2.4: Assemble Full Factorial Design
**Description:** Create a complete `Design` object from generated runs.

**Dependencies:** Task 1.4, Task 2.3

**Acceptance Criteria:**
- Generated design contains:
  - valid `design_id`;
  - correct `design_type`;
  - reference to the source experiment;
  - validated runs.
- Design validation succeeds.
- Run count matches expected full factorial size.

---

## Step 3 — Design Generation Workflow
### Task 3.1: Implement generate_design() Function
**Description:** Implement workflow orchestration for design generation.

**Location:**
- `doe/design_generation.py`

**Dependencies:** Task 1.4, Task 2.4

**Acceptance Criteria:**
- Accepts a valid `WorkflowState`.
- Requires an existing valid `Experiment`.
- Selects the correct generator.
- Adds the generated `Design` to the workflow state.
- Updates workflow step to: `design_generated`.
- Rejects invalid workflow states.

### Task 3.2: Implement Workflow Transition Validation

**Description:** Extend workflow validation to support the transition:

- `experiment_created -> design_generated`

**Dependencies:** Task 3.1

**Acceptance Criteria:**
- Transition is explicitly validated.
- Backward or invalid transitions raise workflow errors.
- Workflow state consistency is preserved.

## Step 4 — Workflow Persistence Extension
### Task 4.1: Extend WorkflowState JSON Serialization for Design
**Description:** Update workflow serialization to persist generated designs.

**Dependencies:** Task 1.4, Task 3.1

**Acceptance Criteria:**
- `WorkflowState` serializes nested `Design` objects.
- JSON contains:
  - experiment;
  - design;
  - no results;
  - no analysis.
- Saved workflow state can be restored.
- Restored state matches the original state.

---

## Step 5 — Design Generation End-to-End Test
### Task 5.1: Create Design Generation Integration Test

**Description:** Implement an end-to-end test covering the workflow from an existing experiment to a persisted design.

**Dependencies:** Task 2.4, Task 3.1, Task 4.1

**Acceptance Criteria:**
- Test starts from a valid `WorkflowState` containing an `Experiment`.
- Generates a full factorial design.
- Validates generated runs.
- Saves workflow state to JSON.
- Reloads workflow state.
- Confirms design integrity after serialization.
- All tests pass.

---

## Out of Scope for this milestone

- Result entry.
- `ResultEntry` and `Results` models.
- CSV import for experimental results.
- Statistical analysis.
- Linear model estimation.
- ANOVA computation.
- Report generation.
- Fractional factorial generation.
- Advanced blocking strategies.
- Advanced randomization algorithms.
- Database persistence.

---

## Completion Rule

Do not start the next milestone until:

- all unit tests pass;
- all design model contract tests pass;
- full factorial generator tests pass;
- JSON round-trip tests pass;
- workflow transition tests pass;
- end-to-end design generation tests pass.
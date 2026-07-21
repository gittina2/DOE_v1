We want to temporarily extract the Results Input part from the future CLI implementation step and implement it now.

The original plan contains:

Step 4 — Complete CLI Interface & Commands

Task 4.1: Implement CLI Commands for Results, Analysis, and Reporting

However, at this stage we only want to implement and validate the Results workflow.

Your task is to implement the "insert-results" functionality end-to-end, while leaving analysis and reporting untouched.

Before coding:

1. Review the current repository state.
2. Identify what is already implemented related to:
   - WorkflowState;
   - Design generation;
   - Design runs;
   - Result models;
   - CSV import utilities;
   - validation logic.
3. Determine what components are missing to support inserting experimental results.

Do not implement analysis, reporting, or unrelated CLI commands.

---

## Goal

Enable the following workflow:


WorkflowState
(step = design_generated)

    |
    v

Import experimental results from CSV

    |
    v

insert_results()

    |
    v

WorkflowState
(step = results_in_progress or results_complete)

    |
    v

Persist updated JSON state


---

## Functional requirements

Implement the Results workflow so that:

### Core logic

- A valid WorkflowState containing a generated Design can receive experimental results.
- Results are imported from a CSV file.
- Imported results are associated with the correct Design runs.
- Invalid inputs are rejected with meaningful domain errors.
- WorkflowState validation rules are respected.

### Persistence

- Results must be serializable through WorkflowState.
- WorkflowState JSON save/load must preserve results information.

### CLI

Add only the required command:


insert-results


Arguments:


--state <path>
--csv <path>
--output <path> (optional, defaults to overwriting state)


The command must:

1. Load WorkflowState.
2. Import results from CSV.
3. Execute insert_results().
4. Save updated WorkflowState.
5. Return:
   - exit code 0 on success;
   - non-zero exit code on domain/workflow errors.

---

## Testing requirements

Add tests covering:

### Core workflow
- inserting results into a valid design-generated workflow;
- invalid workflow states;
- invalid CSV inputs;
- missing runs or mismatched results.

### Persistence
- WorkflowState round-trip serialization including results.

### CLI integration
Create or extend:


tests/test_cli_results.py


to verify:

- insert-results command execution;
- generated output JSON;
- correct exit codes;
- error handling.

---

## Implementation constraints

- Keep domain logic independent from CLI.
- Do not move business logic into `main.py`.
- Reuse existing WorkflowState patterns.
- Follow the existing architecture used for:
  - create_experiment();
  - generate_design().
- Avoid introducing unnecessary dependencies.

---

At the end provide:

## Implementation summary

Include:
- files changed;
- new classes/functions added;
- tests created;
- any architectural decisions.

Do not implement analysis or reporting.
Do not modify unrelated workflow steps.
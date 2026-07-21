from typing import List, Optional, Dict, Any
from doe.models.workflow_state import WorkflowState
from doe.models.results import ResultEntry, Results
from doe.models.exceptions import (
    WorkflowStateMismatchError,
    UnknownRunIdError,
    InvalidResponseValueError,
    DuplicateResultForRunError,
    InvalidWorkflowTransitionError,
)


def insert_results(
    state: WorkflowState,
    result_entries: List[ResultEntry],
    audit_info: Optional[Dict[str, Any]] = None,
) -> WorkflowState:
    """Inserts or updates experimental results in the workflow state.

    Args:
        state: The current WorkflowState (must be in 'design_generated' or 'results_in_progress' or 'results_complete').
        result_entries: List of ResultEntry objects to insert or update.
        audit_info: Optional audit metadata dictionary.

    Returns:
        Updated WorkflowState with step set to 'results_in_progress' or 'results_complete'.

    Raises:
        InvalidWorkflowTransitionError / WorkflowStateMismatchError: If state is not in a valid step.
        UnknownRunIdError: If a result references a run ID not present in the design.
        InvalidResponseValueError: If response names/values are invalid.
        DuplicateResultForRunError: If duplicate run references are present in input list.
    """
    state.validate()

    valid_starting_steps = ("design_generated", "results_in_progress", "results_complete")
    if state.step not in valid_starting_steps:
        raise InvalidWorkflowTransitionError(
            f"Cannot insert results when workflow state is in step '{state.step}'."
        )

    if state.design is None or state.experiment is None:
        raise WorkflowStateMismatchError("WorkflowState must contain valid experiment and design.")

    design_run_ids = {run.run_id for run in state.design.runs}
    experiment_response_names = {r.name for r in state.experiment.responses}

    # Validate input entries
    input_run_refs = set()
    for entry in result_entries:
        if not isinstance(entry, ResultEntry):
            raise InvalidResponseValueError("All entries must be ResultEntry instances.")
        entry.validate()

        if entry.run_ref not in design_run_ids:
            raise UnknownRunIdError(
                f"Run reference '{entry.run_ref}' does not exist in the design."
            )

        if entry.run_ref in input_run_refs:
            raise DuplicateResultForRunError(
                f"Duplicate result entry for run '{entry.run_ref}' in input list."
            )
        input_run_refs.add(entry.run_ref)

        for resp_name, val in entry.values.items():
            if resp_name not in experiment_response_names:
                raise InvalidResponseValueError(
                    f"Response '{resp_name}' is not defined in the experiment."
                )
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise InvalidResponseValueError(
                    f"Response value for '{resp_name}' must be numeric (got '{val}')."
                )

    # Merge with existing results if present
    existing_entries_map: Dict[str, ResultEntry] = {}
    if state.results is not None and hasattr(state.results, "entries"):
        for e in state.results.entries:
            existing_entries_map[e.run_ref] = e

    for entry in result_entries:
        existing_entries_map[entry.run_ref] = entry

    all_entries = list(existing_entries_map.values())

    # Check completeness
    # Complete if all runs in design have complete entries with all expected responses
    is_complete = True
    if len(all_entries) < len(state.design.runs):
        is_complete = False
    else:
        for run in state.design.runs:
            entry = existing_entries_map.get(run.run_id)
            if entry is None or entry.status != "complete":
                is_complete = False
                break
            if not all(resp_name in entry.values for resp_name in experiment_response_names):
                is_complete = False
                break

    completeness = "complete" if is_complete else "partial"
    target_step = "results_complete" if is_complete else "results_in_progress"

    results_obj = Results(
        design_ref=state.design.design_id,
        entries=all_entries,
        completeness=completeness,
        results_id=state.results.results_id if state.results is not None and hasattr(state.results, "results_id") else undefined,
    ) if state.results is not None and hasattr(state.results, "results_id") else Results(
        design_ref=state.design.design_id,
        entries=all_entries,
        completeness=completeness,
    )

    results_obj.validate()

    audit_payload = {
        **(audit_info or {}),
        "inserted_results_count": len(result_entries),
        "total_results_count": len(all_entries),
    }

    new_state = state.transition_to(
        new_step=target_step,
        results=results_obj,
        audit=audit_payload,
    )

    return new_state

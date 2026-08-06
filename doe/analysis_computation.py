from typing import Any, Dict, List, Optional
from doe.models.analysis import Analysis
from doe.models.design import Design
from doe.models.experiment import Experiment
from doe.models.results import Results
from doe.models.workflow_state import WorkflowState
from doe.models.exceptions import (
    InconsistentReferenceError,
    InvalidAnalysisInputError,
    WorkflowStateMismatchError,
)
from doe.statistics import (
    fit_linear_model,
    fit_interaction_model,
    fit_quadratic_model,
)

_MODEL_FIBERS = {
    "linear": fit_linear_model,
    "interaction": fit_interaction_model,
    "quadratic": fit_quadratic_model,
}


def analyze_experiment(
    state: WorkflowState,
    model_type: str = "linear",
) -> WorkflowState:
    state.validate()

    if state.step != "results_complete":
        raise WorkflowStateMismatchError(
            f"Cannot run analysis from step '{state.step}'. Step must be 'results_complete'."
        )

    if state.experiment is None or state.design is None or state.results is None:
        raise WorkflowStateMismatchError(
            "For analysis computation, experiment, design, and results must all be defined."
        )

    if state.design.experiment_ref != state.experiment.experiment_id:
        raise InconsistentReferenceError(
            f"Design experiment_ref '{state.design.experiment_ref}' does not match Experiment id '{state.experiment.experiment_id}'."
        )

    if state.results.design_ref != state.design.design_id:
        raise InconsistentReferenceError(
            f"Results design_ref '{state.results.design_ref}' does not match Design id '{state.design.design_id}'."
        )

    model_func = _MODEL_FIBERS.get(model_type)
    if model_func is None:
        raise InvalidAnalysisInputError(
            f"Unsupported model_type: '{model_type}'. Supported: {list(_MODEL_FIBERS.keys())}"
        )

    analysis_obj = model_func(state.experiment, state.design, state.results)

    new_state = state.transition_to(
        "analysis_created",
        analysis=analysis_obj,
        audit={
            "analysis_id": analysis_obj.analysis_id,
            "model_type": model_type,
        },
    )

    return new_state


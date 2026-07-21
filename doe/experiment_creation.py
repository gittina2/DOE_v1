from typing import Any, List, Optional, Dict
from doe.models import (
    Factor,
    Response,
    Experiment,
    DesignType,
    WorkflowState,
    DomainValidationError,
)

def create_experiment(
    name: str,
    factors: List[Factor],
    responses: List[Response],
    design_type: DesignType,
    description: Optional[str] = None,
    planned_runs: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> WorkflowState:
    # 4.1 create_experiment Preconditions check
    if not factors:
        raise DomainValidationError("At least one factor is required.")
    if not responses:
        raise DomainValidationError("At least one response is required.")

    # Create and validate the Experiment model
    experiment = Experiment(
        name=name,
        factors=factors,
        responses=responses,
        design_type=design_type,
        description=description,
        planned_runs=planned_runs,
        metadata=metadata,
    )
    # This will check model consistency (unique names, valid design type, etc.)
    experiment.validate()

    # Create the WorkflowState as of postconditions:
    # step = experiment_created
    # no design, results, or analysis are present (all None)
    state = WorkflowState(
        step="experiment_created",
        experiment=experiment,
        audit={
            "action": "create_experiment",
            "experiment_id": experiment.experiment_id,
            "experiment_name": experiment.name,
        },
    )
    # Validate the state consistency
    state.validate()

    return state

from typing import Any, List, Optional, Dict
from doe.models import (
    Factor,
    Response,
    Experiment,
    WorkflowState,
    DomainValidationError,
)

def create_experiment(
    name: str,
    factors: List[Factor],
    responses: List[Response],
    description: Optional[str] = None,
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
        description=description,
        metadata=metadata,
    )
    # This will check model consistency (unique names, etc.)
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

from typing import Type, Dict

from doe.models.workflow_state import WorkflowState
from doe.designs.generator_interface import DesignGenerator
from doe.designs.full_factorial import FullFactorialGenerator
from doe.designs.fractional_factorial import FractionalFactorialGenerator

from doe.models.exceptions import (UnsupportedDesignTypeError, WorkflowStateMismatchError)

_DESIGN_GENERATORS: Dict[str, Type[DesignGenerator]] = {
    "full_factorial": FullFactorialGenerator,
    "fractional_factorial": FractionalFactorialGenerator,
}

def get_design_generator(design_type: str) -> DesignGenerator:
    """
    Select the appropriate design generator.

    Parameters
    ----------
    design_type:
        Type of DOE design requested.

    Returns
    -------
    DesignGenerator
        Concrete generator implementation.

    Raises
    ------
    UnsupportedDesignTypeError
        If no generator exists for the requested design type.
    """

    generator_class = _DESIGN_GENERATORS.get(design_type)
    if generator_class is None:
        raise UnsupportedDesignTypeError(
            f"No generator available for design type: {design_type}"
        )

    return generator_class()    
  

def generate_design(
    state: WorkflowState,
    design_type: str = "full_factorial",
) -> WorkflowState:
    
    """
    Generate a DOE design from an experiment stored in a workflow state.

    Parameters
    ----------
    state: WorkflowState
        Current workflow state.
    design_type: str
        DOE design strategy (e.g. 'full_factorial', 'fractional_factorial').

    Preconditions
    -------------
    - WorkflowState must be valid.
    - Workflow step must be 'experiment_created'.
    - A valid Experiment must exist.

    Postconditions
    --------------
    - Returns a new WorkflowState.
    - Step becomes 'design_generated'.
    - Generated Design is attached.
    """
    
    state.validate()  # Validate the current state before proceeding
    
    if state.step != "experiment_created":
        raise WorkflowStateMismatchError(
            f"Cannot generate design from step '{state.step}'. Expected 'experiment_created'."
        )
    
    experiment = state.experiment
    if experiment is None:
        raise WorkflowStateMismatchError("Experiment must be defined for design generation.")

    generator = get_design_generator(design_type)

    design = generator.generate(experiment)

    new_state = WorkflowState(
        step="design_generated",
        experiment=experiment,
        design=design,
        audit={
            "action": "generate_design",    
            "experiment_id": experiment.experiment_id,
            "experiment_name": experiment.name,      
            "design_id": design.design_id,
            "design_type": design.design_type,
        }
    )

    new_state.validate()  # Validate the new state after generation   

    return new_state
import pytest

from doe.design_generation import generate_design
from doe.models.exceptions import (
    WorkflowStateMismatchError,
    UnsupportedDesignTypeError,
)

from doe.models.workflow_state import WorkflowState


def test_generate_design_from_valid_state(sample_workflow_state):

    new_state = generate_design(sample_workflow_state)

    assert new_state.step == "design_generated"

    assert new_state.experiment is not None
    assert new_state.design is not None

    assert new_state.design.design_type == "full_factorial"

    assert (
        new_state.design.experiment_ref
        == new_state.experiment.experiment_id
    )

    assert new_state.audit["action"] == "generate_design"

def test_generated_design_contains_expected_runs(sample_workflow_state):

    new_state = generate_design(sample_workflow_state)

    assert len(new_state.design.runs) == 4

def test_generate_design_rejects_empty_state():    

    state = WorkflowState(
        step="empty"
    )

    with pytest.raises(
        WorkflowStateMismatchError
    ):
        generate_design(state)

def test_generate_design_rejects_existing_design(sample_design_state):

    with pytest.raises(
        WorkflowStateMismatchError
    ):
        generate_design(sample_design_state)

def test_generate_design_rejects_unknown_generator(sample_workflow_state):

    sample_workflow_state.experiment.design_type = (
        "fractional_factorial"
    )

    with pytest.raises(
        UnsupportedDesignTypeError
    ):
        generate_design(sample_workflow_state)        

    
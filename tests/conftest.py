from doe.models.design import Run
import pytest

from doe.models import (
    Experiment,
    Factor,
    Response,
    WorkflowState
)


@pytest.fixture
def sample_experiment():
    temperature = Factor(
        name="temperature",
        type="continuous",
        lower_bound=0.0,
        upper_bound=100.0,
        unit="C",
    )

    catalyst = Factor(
        name="catalyst",
        type="categorical",
        levels=["A", "B"],
    )

    response = Response(
        name="yield",
        type="continuous",
    )

    return Experiment(
        name="Test Experiment",
        factors=[
            temperature,
            catalyst,
        ],
        responses=[
            response
        ],
    )


@pytest.fixture
def sample_runs():
    return [
        Run(
            factor_values={
                "temperature": 0.0,
                "catalyst": "A",
            }
        ),
        Run(
            factor_values={
                "temperature": 100.0,
                "catalyst": "A",
            }
        ),
        Run(
            factor_values={
                "temperature": 0.0,
                "catalyst": "B",
            }
        ),
        Run(
            factor_values={
                "temperature": 100.0,
                "catalyst": "B",
            }
        ),
    ]

from doe.models import Design


@pytest.fixture
def sample_design(sample_experiment, sample_runs):
    return Design(
        experiment_ref=sample_experiment.experiment_id,
        design_type="full_factorial",
        runs=sample_runs,
    )

@pytest.fixture
def sample_workflow_state(sample_experiment):
    return WorkflowState(
        step="experiment_created",
        experiment=sample_experiment,
        audit={
            "action": "create_experiment"
        }
    )

@pytest.fixture
def sample_design_state(sample_workflow_state, sample_design):

    return WorkflowState(
        step="design_generated",
        experiment=sample_workflow_state.experiment,
        design=sample_design,
        audit={
            "action": "generate_design"
        }
    )
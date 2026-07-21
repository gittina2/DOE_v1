import pytest
from doe import create_experiment
from doe.models import (
    Factor,
    Response,
    WorkflowState,
    DomainValidationError,
    InvalidDesignTypeError,
    DuplicateFactorNameError,
)

def test_create_experiment_success():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    
    ws = create_experiment(
        name="Opt Yield",
        factors=[f],
        responses=[r],
        design_type="full_factorial",
        planned_runs=8,
        description="test description",
        metadata={"key": "val"}
    )
    
    assert isinstance(ws, WorkflowState)
    assert ws.step == "experiment_created"
    assert ws.experiment is not None
    assert ws.experiment.name == "Opt Yield"
    assert ws.experiment.factors == [f]
    assert ws.experiment.responses == [r]
    assert ws.experiment.design_type == "full_factorial"
    assert ws.experiment.planned_runs == 8
    assert ws.experiment.description == "test description"
    assert ws.experiment.metadata == {"key": "val"}
    assert ws.design is None
    assert ws.results is None
    assert ws.analysis is None
    assert ws.audit["action"] == "create_experiment"
    assert ws.audit["experiment_name"] == "Opt Yield"

def test_create_experiment_missing_factors():
    r = Response(name="yield", type="continuous")
    with pytest.raises(DomainValidationError, match="At least one factor"):
        create_experiment(
            name="Opt Yield",
            factors=[],
            responses=[r],
            design_type="full_factorial"
        )

def test_create_experiment_missing_responses():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    with pytest.raises(DomainValidationError, match="At least one response"):
        create_experiment(
            name="Opt Yield",
            factors=[f],
            responses=[],
            design_type="full_factorial"
        )

def test_create_experiment_validation_propagation():
    # Invalid factor (missing bounds)
    f = Factor(name="temp", type="continuous")
    r = Response(name="yield", type="continuous")
    with pytest.raises(DomainValidationError, match="must have lower_bound and upper_bound"):
        create_experiment(
            name="Opt Yield",
            factors=[f],
            responses=[r],
            design_type="full_factorial"
        )

    # Duplicate factor names
    f1 = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    f2 = Factor(name="temp", type="continuous", lower_bound=50.0, upper_bound=150.0)
    with pytest.raises(DuplicateFactorNameError, match="Duplicate factor name"):
        create_experiment(
            name="Opt Yield",
            factors=[f1, f2],
            responses=[r],
            design_type="full_factorial"
        )

    # Invalid design type
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    with pytest.raises(InvalidDesignTypeError, match="Unsupported design type"):
        create_experiment(
            name="Opt Yield",
            factors=[f],
            responses=[r],
            design_type="invalid_design" # type: ignore
        )

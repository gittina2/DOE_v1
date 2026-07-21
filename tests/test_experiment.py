import pytest
from doe.models import (
    Experiment,
    Factor,
    Response,
    DomainValidationError,
    DuplicateFactorNameError,
    InvalidDesignTypeError,
    InvalidPlannedRunsError,
)

def test_valid_experiment():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    exp = Experiment(
        name="Chemical yield optimization",
        factors=[f],
        responses=[r],
        design_type="full_factorial",
        planned_runs=8,
        description="Optimize temperature and concentration",
        metadata={"priority": "high"}
    )
    exp.validate()
    assert exp.name == "Chemical yield optimization"
    assert len(exp.factors) == 1
    assert len(exp.responses) == 1
    assert exp.design_type == "full_factorial"
    assert exp.planned_runs == 8
    assert exp.description == "Optimize temperature and concentration"
    assert exp.metadata == {"priority": "high"}
    assert isinstance(exp.experiment_id, str) and len(exp.experiment_id) > 0

def test_missing_name():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="  ", factors=[f], responses=[r], design_type="full_factorial")
    with pytest.raises(DomainValidationError, match="Experiment name is required"):
        exp.validate()

def test_empty_factors():
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Test Exp", factors=[], responses=[r], design_type="full_factorial")
    with pytest.raises(DomainValidationError, match="At least one factor is required"):
        exp.validate()

def test_empty_responses():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    exp = Experiment(name="Test Exp", factors=[f], responses=[], design_type="full_factorial")
    with pytest.raises(DomainValidationError, match="At least one response is required"):
        exp.validate()

def test_duplicate_factor_names():
    f1 = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    f2 = Factor(name="temp", type="continuous", lower_bound=50.0, upper_bound=150.0)
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Test Exp", factors=[f1, f2], responses=[r], design_type="full_factorial")
    with pytest.raises(DuplicateFactorNameError, match="Duplicate factor name detected"):
        exp.validate()

def test_duplicate_response_names():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r1 = Response(name="yield", type="continuous")
    r2 = Response(name="yield", type="continuous")
    exp = Experiment(name="Test Exp", factors=[f], responses=[r1, r2], design_type="full_factorial")
    with pytest.raises(DomainValidationError, match="Duplicate response name detected"):
        exp.validate()

def test_invalid_individual_factor():
    f = Factor(name="temp", type="continuous") # Missing bounds
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Test Exp", factors=[f], responses=[r], design_type="full_factorial")
    # Should propagate the lower_bound/upper_bound validation error
    with pytest.raises(DomainValidationError):
        exp.validate()

def test_invalid_design_type():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Test Exp", factors=[f], responses=[r], design_type="custom_design") # type: ignore
    with pytest.raises(InvalidDesignTypeError, match="Unsupported design type"):
        exp.validate()

def test_invalid_planned_runs():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    
    exp1 = Experiment(name="Test Exp", factors=[f], responses=[r], design_type="full_factorial", planned_runs=0)
    with pytest.raises(InvalidPlannedRunsError, match="must be a positive integer"):
        exp1.validate()

    exp2 = Experiment(name="Test Exp", factors=[f], responses=[r], design_type="full_factorial", planned_runs=-5)
    with pytest.raises(InvalidPlannedRunsError, match="must be a positive integer"):
        exp2.validate()

    exp3 = Experiment(name="Test Exp", factors=[f], responses=[r], design_type="full_factorial", planned_runs="many") # type: ignore
    with pytest.raises(InvalidPlannedRunsError, match="must be a positive integer"):
        exp3.validate()

def test_serialization_round_trip():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    exp1 = Experiment(
        name="Chemical yield optimization",
        factors=[f],
        responses=[r],
        design_type="full_factorial",
        planned_runs=8,
        description="Optimize temperature and concentration",
        metadata={"priority": "high"}
    )
    d = exp1.to_dict()
    assert d["name"] == "Chemical yield optimization"
    assert len(d["factors"]) == 1
    assert d["factors"][0]["name"] == "temp"
    assert len(d["responses"]) == 1
    assert d["responses"][0]["name"] == "yield"
    assert d["design_type"] == "full_factorial"
    assert d["planned_runs"] == 8
    assert d["description"] == "Optimize temperature and concentration"
    assert d["metadata"] == {"priority": "high"}
    assert d["schema_version"] == "1.0"
    
    exp2 = Experiment.from_dict(d)
    assert exp1 == exp2

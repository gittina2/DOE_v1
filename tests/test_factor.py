import pytest
from doe.models import (
    Factor,
    DomainValidationError,
    InvalidFactorTypeError,
    InvalidFactorBoundsError,
    MissingFactorLevelsError,
    DuplicateFactorLevelsError,
)

def test_valid_continuous_factor():
    f = Factor(name="temperature", type="continuous", lower_bound=0.0, upper_bound=100.0, unit="C")
    f.validate()
    assert f.name == "temperature"
    assert f.type == "continuous"
    assert f.lower_bound == 0.0
    assert f.upper_bound == 100.0
    assert f.unit == "C"
    assert f.levels is None

def test_valid_categorical_factor():
    f = Factor(name="catalyst", type="categorical", levels=["A", "B", "C"])
    f.validate()
    assert f.name == "catalyst"
    assert f.type == "categorical"
    assert f.levels == ["A", "B", "C"]
    assert f.lower_bound is None
    assert f.upper_bound is None

def test_invalid_name():
    f = Factor(name="  ", type="continuous", lower_bound=0.0, upper_bound=10.0)
    with pytest.raises(DomainValidationError, match="name is required"):
        f.validate()

def test_invalid_type():
    f = Factor(name="temp", type="discrete", lower_bound=0.0, upper_bound=10.0) # type: ignore
    with pytest.raises(InvalidFactorTypeError, match="Unsupported factor type"):
        f.validate()

def test_continuous_bounds_validation():
    # Missing lower bound
    f = Factor(name="temp", type="continuous", upper_bound=10.0)
    with pytest.raises(InvalidFactorBoundsError, match="must have lower_bound and upper_bound"):
        f.validate()

    # Inverted bounds
    f = Factor(name="temp", type="continuous", lower_bound=10.0, upper_bound=5.0)
    with pytest.raises(InvalidFactorBoundsError, match="must be less than upper_bound"):
        f.validate()

    # Equal bounds
    f = Factor(name="temp", type="continuous", lower_bound=5.0, upper_bound=5.0)
    with pytest.raises(InvalidFactorBoundsError, match="must be less than upper_bound"):
        f.validate()

def test_continuous_with_levels_error():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=10.0, levels=["A", "B"])
    with pytest.raises(DomainValidationError, match="cannot have levels defined"):
        f.validate()

def test_categorical_with_bounds_error():
    f = Factor(name="catalyst", type="categorical", levels=["A", "B"], lower_bound=0.0)
    with pytest.raises(DomainValidationError, match="cannot have lower_bound or upper_bound"):
        f.validate()

def test_categorical_levels_validation():
    # Missing levels
    f = Factor(name="catalyst", type="categorical")
    with pytest.raises(MissingFactorLevelsError, match="must have levels defined"):
        f.validate()

    # Insufficient levels
    f = Factor(name="catalyst", type="categorical", levels=["A"])
    with pytest.raises(DuplicateFactorLevelsError, match="must contain at least 2 values"):
        f.validate()

    # Duplicate levels
    f = Factor(name="catalyst", type="categorical", levels=["A", "B", "A"])
    with pytest.raises(DuplicateFactorLevelsError, match="must not contain duplicate values"):
        f.validate()

    # Invalid level types
    f = Factor(name="catalyst", type="categorical", levels=["A", {}])
    with pytest.raises(DomainValidationError, match="Invalid level type"):
        f.validate()

def test_serialization_round_trip():
    f1 = Factor(
        name="temperature",
        type="continuous",
        lower_bound=20.0,
        upper_bound=50.0,
        unit="C",
        metadata={"precision": 0.1}
    )
    d = f1.to_dict()
    assert d["name"] == "temperature"
    assert d["type"] == "continuous"
    assert d["lower_bound"] == 20.0
    assert d["upper_bound"] == 50.0
    assert d["unit"] == "C"
    assert d["metadata"] == {"precision": 0.1}
    assert d["schema_version"] == "1.1"

    f2 = Factor.from_dict(d)
    assert f1 == f2

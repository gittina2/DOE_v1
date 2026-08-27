import pytest
from doe.models import (
    Response,
    MissingResponseError,
    InvalidResponseTypeError,
    DomainValidationError,
)

def test_valid_response():
    r = Response(name="yield", type="continuous", unit="g", metadata={"target": "maximize"})
    r.validate()
    assert r.name == "yield"
    assert r.type == "continuous"
    assert r.unit == "g"
    assert r.metadata == {"target": "maximize"}

def test_missing_name():
    r = Response(name="   ", type="continuous")
    with pytest.raises(MissingResponseError, match="Response name is required"):
        r.validate()

def test_invalid_type():
    r = Response(name="yield", type="categorical") # type: ignore
    with pytest.raises(InvalidResponseTypeError, match="Unsupported response type"):
        r.validate()

def test_invalid_unit():
    r = Response(name="yield", type="continuous", unit="  ")
    with pytest.raises(DomainValidationError, match="must be non-empty"):
        r.validate()

def test_serialization_round_trip():
    r1 = Response(name="yield", type="continuous", unit="kg", metadata={"target": 100})
    d = r1.to_dict()
    assert d["name"] == "yield"
    assert d["type"] == "continuous"
    assert d["unit"] == "kg"
    assert d["metadata"] == {"target": 100}
    assert d["schema_version"] == "1.1"

    r2 = Response.from_dict(d)
    assert r1 == r2

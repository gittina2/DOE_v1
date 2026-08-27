from _pytest import monkeypatch
from doe.models import (Run, DomainValidationError)
import pytest

def test_valid_run(sample_experiment):
    run = Run(
        factor_values={
            "temperature": 50,
            "catalyst": "A"
        }
    )

    run.validate(sample_experiment)

    assert run.run_id
    assert run.factor_values["temperature"] == 50
    assert run.factor_values["catalyst"] == "A"

def test_run_ids_are_unique():

    run1 = Run()
    run2 = Run()

    assert run1.run_id != run2.run_id

def test_run_missing_id(sample_experiment):

    run = Run(
        run_id="",
        factor_values={
            "temperature":50,
            "catalyst":"A"
        }
    )

    with pytest.raises(DomainValidationError,
        match="Run identifier must be non‑empty"):
        run.validate(sample_experiment)


def test_run_missing_factor(sample_experiment):

    run = Run(
        factor_values={
            "temperature":50
        }
    )

    with pytest.raises(DomainValidationError,
        match="Run missing required factors"):
        run.validate(sample_experiment)

def test_run_extra_factor(sample_experiment):

    run = Run(
        factor_values={
            "temperature":50,
            "catalyst":"A",
            "extra":"extra"
        }
    )

    with pytest.raises(DomainValidationError,
        match="Run contains unknown factors"):
        run.validate(sample_experiment)

def test_run_value_out_of_bounds(sample_experiment):

    run = Run(
        factor_values={
            "temperature":150,
            "catalyst":"A"
        }
    )

    with pytest.raises(DomainValidationError):        
        run.validate(sample_experiment)

def test_run_continuous_requires_numeric_value(sample_experiment):

    run = Run(
        factor_values={
            "temperature":"hot",
            "catalyst":"A",
        }
    )

    with pytest.raises(DomainValidationError, 
    match="requires a numeric value"):
        run.validate(sample_experiment)

def test_run_invalid_categorical_value(sample_experiment):

    run = Run(
        factor_values={
            "temperature":50,
            "catalyst":"C",
        }
    )

    with pytest.raises(DomainValidationError, 
        match="not in allowed levels"):
        run.validate(sample_experiment)

def test_run_serialization_round_trip():

    run1 = Run(
        factor_values={
            "temperature":50,
            "catalyst":"A",
        },
        metadata={
            "replicate":1
        }
    )

    data = run1.to_dict()

    assert data["schema_version"] == "1.1"
    assert data["factor_values"]["temperature"] == 50

    run2 = Run.from_dict(data)

    assert run1 == run2


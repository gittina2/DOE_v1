import pytest

from doe.models import (Run, 
                        Block, 
                        Design,  
                        DomainValidationError, 
                        DuplicateRunIdError, 
                        IncompatibleFactorDefinitionError,
                        InconsistentReferenceError,
                        RunCountMismatchError)
from tests.conftest import sample_design, sample_experiment


def test_valid_design(sample_design, sample_experiment):
    sample_design.validate(sample_experiment)

    assert sample_design.experiment_ref == sample_experiment.experiment_id
    assert sample_design.design_type == "full_factorial"
    assert len(sample_design.runs) == 4

def test_design_without_runs(sample_experiment):

    design = Design(
        experiment_ref=sample_experiment.experiment_id,
        runs=[]
    )

    with pytest.raises(
        DomainValidationError,
        match="Design must contain at least one run"
    ):
        design.validate(sample_experiment)

def test_design_duplicate_run_ids(sample_experiment):

    run1 = Run(
        run_id="run-1",
        factor_values={
            "temperature": 0.0,
            "catalyst": "A"
        }
    )

    run2 = Run(
        run_id="run-1",  # Duplicate ID
        factor_values={
            "temperature": 100.0,
            "catalyst": "A"
        }
    )

    design = Design(
        experiment_ref=sample_experiment.experiment_id,
        runs=[run1, run2]
    )

    with pytest.raises(DuplicateRunIdError):
        design.validate(sample_experiment)

def test_design_invalid_run(sample_experiment):

    run = Run(
        run_id="run-1",
        factor_values={
            "temperature": 0.0,
            # Missing catalyst factor
        }
    )

    design = Design(
        experiment_ref=sample_experiment.experiment_id,
        runs=[run]
    )

    with pytest.raises(DomainValidationError):
        design.validate(sample_experiment)


def test_design_wrong_experiment_reference(sample_runs, sample_experiment):

    design = Design(
        experiment_ref="wrong-id",
        runs=sample_runs
    )

    with pytest.raises(InconsistentReferenceError):
        design.validate(sample_experiment)

def test_design_wrong_run_count(sample_experiment):

    runs = [
        Run(
            factor_values={
                "temperature":0.0,
                "catalyst":"A"
            }
        )
    ]

    design = Design(
        experiment_ref=sample_experiment.experiment_id,
        runs=runs
    )

    with pytest.raises(RunCountMismatchError):
        design.validate(sample_experiment)
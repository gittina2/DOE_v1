import pytest

from doe.models import (
    Block,
    Run,
    Design,
    DomainValidationError,
    InconsistentReferenceError,
)


def create_test_design():
    """
    Create minimal design containing valid runs.
    Used only for block validation tests.
    """

    run1 = Run(
        run_id="run-1",
        factor_values={}
    )

    run2 = Run(
        run_id="run-2",
        factor_values={}
    )

    return Design(
        experiment_ref="experiment-1",
        runs=[
            run1,
            run2
        ]
    )


def test_valid_block():

    block = Block(
        run_ids=[
            "run-1",
            "run-2"
        ],
        metadata={
            "temperature": "high"
        }
    )

    design = create_test_design()

    block.validate(design)

    assert block.block_id
    assert block.run_ids == [
        "run-1",
        "run-2"
    ]
    assert block.metadata == {
        "temperature": "high"
    }


def test_empty_block_id():

    block = Block(
        block_id="",
        run_ids=["run-1"]
    )

    design = create_test_design()

    with pytest.raises(DomainValidationError, match="Block identifier"):
        block.validate(design)


def test_block_without_runs():

    block = Block(
        run_ids=[]
    )

    design = create_test_design()

    with pytest.raises(
        DomainValidationError,
        match="Block must contain at least one run"
    ):
        block.validate(design)


def test_block_with_unknown_run_reference():

    block = Block(
        run_ids=[
            "unknown-run"
        ]
    )

    design = create_test_design()

    with pytest.raises(
        InconsistentReferenceError,
        match="unknown run IDs"
    ):
        block.validate(design)


def test_block_with_duplicate_run_ids():

    block = Block(
        run_ids=[
            "run-1",
            "run-1"
        ]
    )

    design = create_test_design()

    with pytest.raises(
        DomainValidationError,
        match="duplicate run IDs"
    ):
        block.validate(design)


def test_block_serialization_round_trip():

    block1 = Block(
        run_ids=[
            "run-1",
            "run-2"
        ],
        metadata={
            "group": "batch-A"
        }
    )

    data = block1.to_dict()

    assert data["run_ids"] == [
        "run-1",
        "run-2"
    ]

    assert data["metadata"] == {
        "group": "batch-A"
    }

    assert data["schema_version"] == "1.1"


    block2 = Block.from_dict(data)

    assert block1 == block2

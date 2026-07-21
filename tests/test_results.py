import pytest
from doe.models.results import ResultEntry, Results
from doe.models.exceptions import (
    DomainValidationError,
    DuplicateResultForRunError,
    InvalidResponseValueError,
)


def test_result_entry_valid():
    entry = ResultEntry(
        run_ref="run_001",
        values={"yield": 95.5, "purity": 0.99},
        status="complete",
        metadata={"note": "smooth run"},
    )
    entry.validate()
    assert entry.run_ref == "run_001"
    assert entry.values["yield"] == 95.5
    assert entry.status == "complete"


def test_result_entry_invalid_run_ref():
    entry = ResultEntry(run_ref="", values={"yield": 90.0})
    with pytest.raises(DomainValidationError, match="run_ref must be a non-empty string"):
        entry.validate()


def test_result_entry_invalid_values():
    entry = ResultEntry(run_ref="run_001", values={})
    with pytest.raises(InvalidResponseValueError, match="values must be a non-empty dictionary"):
        entry.validate()


def test_result_entry_invalid_status():
    entry = ResultEntry(run_ref="run_001", values={"yield": 90.0}, status="invalid_status")
    with pytest.raises(DomainValidationError, match="Invalid result status"):
        entry.validate()


def test_result_entry_to_dict_from_dict():
    entry = ResultEntry(
        run_ref="run_001",
        values={"yield": 95.5},
        status="partial",
        metadata={"temp": 25},
    )
    d = entry.to_dict()
    restored = ResultEntry.from_dict(d)
    restored.validate()
    assert restored.run_ref == entry.run_ref
    assert restored.values == entry.values
    assert restored.status == entry.status
    assert restored.metadata == entry.metadata


def test_results_aggregate_valid():
    e1 = ResultEntry(run_ref="run_001", values={"yield": 90.0})
    e2 = ResultEntry(run_ref="run_002", values={"yield": 92.0})
    results = Results(
        design_ref="des_001",
        entries=[e1, e2],
        completeness="complete",
    )
    results.validate()
    assert results.design_ref == "des_001"
    assert len(results.entries) == 2
    assert results.results_id.startswith("res_")


def test_results_duplicate_run_ref():
    e1 = ResultEntry(run_ref="run_001", values={"yield": 90.0})
    e2 = ResultEntry(run_ref="run_001", values={"yield": 92.0})
    results = Results(design_ref="des_001", entries=[e1, e2])
    with pytest.raises(DuplicateResultForRunError, match="Duplicate result entry detected"):
        results.validate()


def test_results_invalid_design_ref():
    results = Results(design_ref="", entries=[])
    with pytest.raises(DomainValidationError, match="design_ref must be a non-empty string"):
        results.validate()


def test_results_to_dict_from_dict():
    e1 = ResultEntry(run_ref="run_001", values={"yield": 90.0})
    results = Results(
        design_ref="des_001",
        entries=[e1],
        completeness="partial",
        results_id="res_test_123",
    )
    d = results.to_dict()
    restored = Results.from_dict(d)
    restored.validate()
    assert restored.results_id == "res_test_123"
    assert restored.design_ref == "des_001"
    assert len(restored.entries) == 1
    assert restored.entries[0].run_ref == "run_001"
    assert restored.completeness == "partial"

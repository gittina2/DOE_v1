import io
import pytest
from doe.imports.csv_result_importer import import_results_from_csv
from doe.models.design import Design, Run
from doe.models.exceptions import CsvHeaderError, CsvRowImportError
from doe.models.response import Response


def test_import_results_csv_valid():
    csv_content = """run_id,yield,purity
run_001,95.5,0.99
run_002,92.0,0.98
"""
    stream = io.StringIO(csv_content)
    entries = import_results_from_csv(stream)
    assert len(entries) == 2
    assert entries[0].run_ref == "run_001"
    assert entries[0].values == {"yield": 95.5, "purity": 0.99}
    assert entries[1].run_ref == "run_002"

    assert entries[1].values == {"yield": 92.0, "purity": 0.98}


def test_import_results_csv_with_design_and_responses():
    design = Design(
        design_id="des_001",
        design_type="full_factorial",
        experiment_ref="exp_001",
        runs=[
            Run(run_id="run_001", factor_values={"temp": 100}),
            Run(run_id="run_002", factor_values={"temp": 200}),
        ],
    )
    responses = [Response(name="yield", type="continuous")]

    csv_content = """run_id,yield
run_001,88.5
run_002,91.0
"""
    stream = io.StringIO(csv_content)
    entries = import_results_from_csv(stream, design=design, responses=responses)
    assert len(entries) == 2
    assert entries[0].values == {"yield": 88.5}


def test_import_results_csv_missing_header():
    stream = io.StringIO("")
    with pytest.raises(CsvHeaderError, match="CSV file is empty"):
        import_results_from_csv(stream)


def test_import_results_csv_missing_run_ref_column():
    csv_content = """yield,purity
95.5,0.99
"""
    stream = io.StringIO(csv_content)
    with pytest.raises(CsvHeaderError, match="must contain a run reference column"):
        import_results_from_csv(stream)


def test_import_results_csv_unknown_run_ref():
    design = Design(
        design_id="des_001",
        design_type="full_factorial",
        experiment_ref="exp_001",
        runs=[Run(run_id="run_001", factor_values={"temp": 100})],
    )
    csv_content = """run_id,yield
run_999,95.5
"""
    stream = io.StringIO(csv_content)
    with pytest.raises(CsvRowImportError) as exc_info:
        import_results_from_csv(stream, design=design)
    assert exc_info.value.row_number == 2
    assert exc_info.value.field_name == "run_id"
    assert exc_info.value.invalid_value == "run_999"


def test_import_results_csv_invalid_numeric_cell():
    csv_content = """run_id,yield
run_001,not_a_number
"""
    stream = io.StringIO(csv_content)
    with pytest.raises(CsvRowImportError) as exc_info:
        import_results_from_csv(stream)
    assert exc_info.value.row_number == 2
    assert exc_info.value.field_name == "yield"
    assert exc_info.value.invalid_value == "not_a_number"

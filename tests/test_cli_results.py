import pytest
import sys
from doe.main import main
from doe.models import WorkflowState
from doe.experiment_creation import create_experiment
from doe.design_generation import generate_design
from doe.models.factor import Factor
from doe.models.response import Response


@pytest.fixture
def design_generated_state_file(tmp_path):
    exp = create_experiment(
        name="CLI Results Test Exp",
        factors=[Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)],
        responses=[Response(name="yield", type="continuous")],
        design_type="full_factorial",
    )
    state = generate_design(exp)
    state_file = tmp_path / "workflow_design.json"
    state.save_to_json(str(state_file))
    return state_file, state.design.runs


def test_cli_insert_results_success(tmp_path, design_generated_state_file, capsys):
    state_file, runs = design_generated_state_file
    results_csv = tmp_path / "results.csv"
    results_csv.write_text(
        f"run_id,yield\n{runs[0].run_id},95.5\n{runs[1].run_id},92.0\n",
        encoding="utf-8",
    )

    output_file = tmp_path / "workflow_results.json"

    args = [
        "insert-results",
        "--state", str(state_file),
        "--csv", str(results_csv),
        "--output", str(output_file),
    ]

    with pytest.raises(SystemExit) as exc_info:
        main(args)

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Results successfully inserted" in captured.out

    assert output_file.exists()
    loaded_state = WorkflowState.load_from_json(str(output_file))
    assert loaded_state.step == "results_complete"
    assert loaded_state.results is not None
    assert loaded_state.results.completeness == "complete"
    assert len(loaded_state.results.entries) == 2


def test_cli_insert_results_default_overwrite_state(tmp_path, design_generated_state_file, capsys):
    state_file, runs = design_generated_state_file
    results_csv = tmp_path / "results.csv"
    results_csv.write_text(
        f"run_id,yield\n{runs[0].run_id},95.5\n",
        encoding="utf-8",
    )

    args = [
        "insert-results",
        "--state", str(state_file),
        "--csv", str(results_csv),
    ]

    with pytest.raises(SystemExit) as exc_info:
        main(args)

    assert exc_info.value.code == 0

    loaded_state = WorkflowState.load_from_json(str(state_file))
    assert loaded_state.step == "results_in_progress"
    assert loaded_state.results is not None
    assert loaded_state.results.completeness == "partial"
    assert len(loaded_state.results.entries) == 1


def test_cli_insert_results_invalid_workflow_state(tmp_path, capsys):
    state = WorkflowState(step="empty")
    state_file = tmp_path / "empty_workflow.json"
    state.save_to_json(str(state_file))

    results_csv = tmp_path / "results.csv"
    results_csv.write_text("run_id,yield\nrun_001,95.5\n", encoding="utf-8")

    args = [
        "insert-results",
        "--state", str(state_file),
        "--csv", str(results_csv),
    ]

    with pytest.raises(SystemExit) as exc_info:
        main(args)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Workflow Error" in captured.err


def test_cli_insert_results_invalid_csv_header(tmp_path, design_generated_state_file, capsys):
    state_file, _ = design_generated_state_file
    bad_csv = tmp_path / "bad_results.csv"
    bad_csv.write_text("wrong_col1,wrong_col2\n1,2\n", encoding="utf-8")

    args = [
        "insert-results",
        "--state", str(state_file),
        "--csv", str(bad_csv),
    ]

    with pytest.raises(SystemExit) as exc_info:
        main(args)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Workflow Error" in captured.err or "CSV" in captured.err


def test_cli_insert_results_unknown_run_id(tmp_path, design_generated_state_file, capsys):
    state_file, _ = design_generated_state_file
    bad_csv = tmp_path / "unknown_run.csv"
    bad_csv.write_text("run_id,yield\nrun_nonexistent_999,95.5\n", encoding="utf-8")

    args = [
        "insert-results",
        "--state", str(state_file),
        "--csv", str(bad_csv),
    ]

    with pytest.raises(SystemExit) as exc_info:
        main(args)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Workflow Error" in captured.err

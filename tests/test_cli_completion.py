import pytest
from doe.main import main
from doe.models import WorkflowState
from doe.experiment_creation import create_experiment
from doe.design_generation import generate_design
from doe.result_input import insert_results
from doe.models.factor import Factor
from doe.models.response import Response
from doe.models.results import ResultEntry


@pytest.fixture
def results_complete_state_file(tmp_path):
    f_temp = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    f_press = Factor(name="pressure", type="continuous", lower_bound=1.0, upper_bound=2.0)
    r_yield = Response(name="yield", type="continuous")
    state0 = create_experiment(
        name="CLI Test Exp",
        factors=[f_temp, f_press],
        responses=[r_yield],
    )
    state1 = generate_design(state0, design_type="full_factorial")

    runs = state1.design.runs
    entries = [
        ResultEntry(run_ref=runs[0].run_id, values={"yield": 50.15}),
        ResultEntry(run_ref=runs[1].run_id, values={"yield": 49.85}),
        ResultEntry(run_ref=runs[2].run_id, values={"yield": 70.30}),
        ResultEntry(run_ref=runs[3].run_id, values={"yield": 69.70}),
    ]
    state2 = insert_results(state1, entries)

    state_file = tmp_path / "workflow_results.json"
    state2.save_to_json(str(state_file))
    return state_file, state2


def test_cli_analyze_success(tmp_path, results_complete_state_file, capsys):
    state_file, _ = results_complete_state_file
    output_file = tmp_path / "workflow_analysis.json"

    args = [
        "analyze",
        "--state", str(state_file),
        "--output", str(output_file),
    ]

    with pytest.raises(SystemExit) as exc_info:
        main(args)

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Analysis successfully computed" in captured.out

    assert output_file.exists()
    loaded = WorkflowState.load_from_json(str(output_file))
    assert loaded.step == "analysis_created"
    assert loaded.analysis is not None
    assert "Intercept" in loaded.analysis.coefficients


def test_cli_analyze_default_overwrite(tmp_path, results_complete_state_file, capsys):
    state_file, _ = results_complete_state_file

    args = [
        "analyze",
        "--state", str(state_file),
    ]

    with pytest.raises(SystemExit) as exc_info:
        main(args)

    assert exc_info.value.code == 0

    loaded = WorkflowState.load_from_json(str(state_file))
    assert loaded.step == "analysis_created"
    assert loaded.analysis is not None


def test_cli_analyze_error(tmp_path, capsys):
    f_temp = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    r_yield = Response(name="yield", type="continuous")
    state0 = create_experiment(
        name="Empty Exp",
        factors=[f_temp],
        responses=[r_yield],
    )
    state_file = tmp_path / "exp_created.json"
    state0.save_to_json(str(state_file))

    args = [
        "analyze",
        "--state", str(state_file),
    ]

    with pytest.raises(SystemExit) as exc_info:
        main(args)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Workflow Error" in captured.err


def test_cli_report_success(tmp_path, results_complete_state_file, capsys):
    state_file, _ = results_complete_state_file
    report_file = tmp_path / "experiment_report.md"

    args = [
        "report",
        "--state", str(state_file),
        "--output", str(report_file),
    ]

    with pytest.raises(SystemExit) as exc_info:
        main(args)

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Report successfully generated" in captured.out

    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "# Experiment Report: CLI Test Exp" in content
    assert "## Experimental Results" in content


def test_cli_status_success(results_complete_state_file, capsys):
    state_file, _ = results_complete_state_file

    args = [
        "status",
        "--state", str(state_file),
    ]

    with pytest.raises(SystemExit) as exc_info:
        main(args)

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Workflow Status Summary" in captured.out
    assert "Step: results_complete" in captured.out
    assert "Experiment: CLI Test Exp" in captured.out

"""Full lifecycle end-to-end integration test for the DOE Python Core engine.

This test validates the complete workflow sequentially:
  1. Parse factor definitions from a sample CSV file.
  2. Create an Experiment (create_experiment()).
  3. Generate a FullFactorial design (generate_design()).
  4. Save WorkflowState to JSON.
  5. Import response measurements from a result CSV file and insert results (insert_results()).
  6. Compute linear model statistical analysis (analyze_experiment()).
  7. Confirm ANOVA table, coefficients, and R² are computed accurately.
  8. Save final WorkflowState to JSON and reload it.
  9. Generate Markdown report (generate_report()) and confirm report file content.
  10. Confirm all intermediate and final workflow state JSON files pass validation
      and round-trip equality checks.
"""

import pytest

from doe.imports import parse_factors_csv, map_rows_to_factors, import_results_from_csv
from doe.experiment_creation import create_experiment
from doe.design_generation import generate_design
from doe.result_input import insert_results
from doe.analysis_computation import analyze_experiment
from doe.report_generation import generate_report
from doe.models.response import Response
from doe.models.workflow_state import WorkflowState
from doe.models.analysis import Analysis
from doe.main import main


# ---------------------------------------------------------------------------
# Programmatic API lifecycle test
# ---------------------------------------------------------------------------

def test_full_lifecycle_programmatic_api(tmp_path):
    # ── Step 1: Write sample factor CSV and parse it ──────────────────────
    factors_csv = tmp_path / "factors.csv"
    factors_csv.write_text(
        "name,type,lower_bound,upper_bound\n"
        "temp,continuous,100.0,200.0\n"
        "pressure,continuous,1.0,2.0\n",
        encoding="utf-8",
    )

    parsed_rows = parse_factors_csv(str(factors_csv))
    factors = map_rows_to_factors(parsed_rows)
    assert len(factors) == 2
    assert factors[0].name == "temp"
    assert factors[1].name == "pressure"

    # ── Step 2: Create Experiment ─────────────────────────────────────────
    responses = [Response(name="yield", type="continuous", unit="%")]
    state = create_experiment(
        name="E2E Yield Optimization",
        description="Full lifecycle test experiment",
        factors=factors,
        responses=responses,
    )
    assert state.step == "experiment_created"
    assert state.experiment is not None
    assert state.experiment.name == "E2E Yield Optimization"
    state.validate()

    # Save & reload – round-trip check 1
    json_path_1 = tmp_path / "state_01_experiment.json"
    state.save_to_json(str(json_path_1))
    state_reloaded = WorkflowState.load_from_json(str(json_path_1))
    assert state_reloaded == state

    # ── Step 3: Generate Design ───────────────────────────────────────────
    state = generate_design(state)
    assert state.step == "design_generated"
    assert state.design is not None
    assert len(state.design.runs) == 4  # 2 factors × 2 levels each
    state.validate()

    # Save & reload – round-trip check 2
    json_path_2 = tmp_path / "state_02_design.json"
    state.save_to_json(str(json_path_2))
    state_reloaded = WorkflowState.load_from_json(str(json_path_2))
    assert state_reloaded == state

    # ── Step 4–5: Write result CSV & insert results ───────────────────────
    runs = state.design.runs
    results_csv = tmp_path / "results.csv"
    # Simulate true model: yield ≈ 30 + 0.2*temp + 5*pressure + noise
    result_lines = "run_id,yield\n"
    result_data = {
        runs[0].run_id: 35.5,   # temp=100, pressure=1 → ~35
        runs[1].run_id: 40.3,   # temp=100, pressure=2 → ~40
        runs[2].run_id: 55.8,   # temp=200, pressure=1 → ~55
        runs[3].run_id: 60.4,   # temp=200, pressure=2 → ~60
    }
    for run_id, val in result_data.items():
        result_lines += f"{run_id},{val}\n"
    results_csv.write_text(result_lines, encoding="utf-8")

    result_entries = import_results_from_csv(
        str(results_csv),
        design=state.design,
        responses=state.experiment.responses,
    )
    assert len(result_entries) == 4

    state = insert_results(state, result_entries)
    assert state.step == "results_complete"
    assert state.results is not None
    assert state.results.completeness == "complete"
    assert len(state.results.entries) == 4
    state.validate()

    # Save & reload – round-trip check 3
    json_path_3 = tmp_path / "state_03_results.json"
    state.save_to_json(str(json_path_3))
    state_reloaded = WorkflowState.load_from_json(str(json_path_3))
    assert state_reloaded == state

    # ── Step 6–7: Compute analysis & verify statistics ────────────────────
    state = analyze_experiment(state)
    assert state.step == "analysis_created"
    assert state.analysis is not None
    assert isinstance(state.analysis, Analysis)
    state.validate()

    # Coefficients present
    coeffs = state.analysis.coefficients
    assert "Intercept" in coeffs
    assert "temp" in coeffs
    assert "pressure" in coeffs

    # R² should be high for this near-linear data
    assert state.analysis.r_squared is not None
    assert state.analysis.r_squared > 0.95

    # ANOVA table structure
    anova = state.analysis.anova_table
    assert anova is not None
    assert len(anova) == 3
    sources = [row["source"] for row in anova]
    assert "Model" in sources
    assert "Residuals" in sources
    assert "Total" in sources

    # Residuals present
    assert state.analysis.residuals is not None
    assert len(state.analysis.residuals) == 4

    # p-values present
    assert state.analysis.p_values is not None
    assert "Intercept" in state.analysis.p_values

    # Save & reload – round-trip check 4
    json_path_4 = tmp_path / "state_04_analysis.json"
    state.save_to_json(str(json_path_4))
    state_reloaded = WorkflowState.load_from_json(str(json_path_4))
    assert state_reloaded == state

    # ── Step 8–9: Generate Markdown report ────────────────────────────────
    report_path = tmp_path / "report.md"
    state = generate_report(state, output_path=str(report_path), format="markdown")
    assert state.step == "report_generated"
    state.validate()

    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")

    # Verify report content sections
    assert "# Experiment Report: E2E Yield Optimization" in content
    assert "## Experiment Overview" in content
    assert "## Factors & Responses" in content
    assert "## Experimental Design" in content
    assert "## Experimental Results" in content
    assert "## Statistical Analysis" in content
    assert "### Coefficients" in content
    assert "### ANOVA Table" in content

    # ── Step 10: Final round-trip equality check ──────────────────────────
    json_path_5 = tmp_path / "state_05_report.json"
    state.save_to_json(str(json_path_5))
    state_final = WorkflowState.load_from_json(str(json_path_5))
    assert state_final == state


# ---------------------------------------------------------------------------
# CLI invocation lifecycle test
# ---------------------------------------------------------------------------

def test_full_lifecycle_cli_invocation(tmp_path, capsys):
    # ── Prepare CSV inputs ────────────────────────────────────────────────
    factors_csv = tmp_path / "factors.csv"
    factors_csv.write_text(
        "name,type,lower_bound,upper_bound\n"
        "temp,continuous,100.0,200.0\n"
        "pressure,continuous,1.0,2.0\n",
        encoding="utf-8",
    )

    state_file_1 = tmp_path / "cli_state_01.json"
    state_file_2 = tmp_path / "cli_state_02.json"
    state_file_3 = tmp_path / "cli_state_03.json"
    state_file_4 = tmp_path / "cli_state_04.json"
    report_file = tmp_path / "cli_report.md"

    # ── 1. init-experiment ────────────────────────────────────────────────
    with pytest.raises(SystemExit) as exc_info:
        main([
            "init-experiment",
            "--name", "CLI E2E Exp",
            "--factors-csv", str(factors_csv),
            "--response", "yield:continuous",
            "--output", str(state_file_1),
        ])
    assert exc_info.value.code == 0
    assert state_file_1.exists()

    loaded = WorkflowState.load_from_json(str(state_file_1))
    assert loaded.step == "experiment_created"

    # ── 2. generate-design ────────────────────────────────────────────────
    with pytest.raises(SystemExit) as exc_info:
        main([
            "generate-design",
            "--input", str(state_file_1),
            "--output", str(state_file_2),
        ])
    assert exc_info.value.code == 0
    assert state_file_2.exists()

    loaded = WorkflowState.load_from_json(str(state_file_2))
    assert loaded.step == "design_generated"
    assert len(loaded.design.runs) == 4

    # ── 3. insert-results ─────────────────────────────────────────────────
    runs = loaded.design.runs
    results_csv = tmp_path / "results.csv"
    result_lines = "run_id,yield\n"
    values = [35.5, 40.3, 55.8, 60.4]
    for run, val in zip(runs, values):
        result_lines += f"{run.run_id},{val}\n"
    results_csv.write_text(result_lines, encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main([
            "insert-results",
            "--state", str(state_file_2),
            "--csv", str(results_csv),
            "--output", str(state_file_3),
        ])
    assert exc_info.value.code == 0
    assert state_file_3.exists()

    loaded = WorkflowState.load_from_json(str(state_file_3))
    assert loaded.step == "results_complete"

    # ── 4. analyze ────────────────────────────────────────────────────────
    with pytest.raises(SystemExit) as exc_info:
        main([
            "analyze",
            "--state", str(state_file_3),
            "--output", str(state_file_4),
        ])
    assert exc_info.value.code == 0
    assert state_file_4.exists()

    loaded = WorkflowState.load_from_json(str(state_file_4))
    assert loaded.step == "analysis_created"
    assert loaded.analysis is not None
    assert "Intercept" in loaded.analysis.coefficients

    # ── 5. report ─────────────────────────────────────────────────────────
    with pytest.raises(SystemExit) as exc_info:
        main([
            "report",
            "--state", str(state_file_4),
            "--output", str(report_file),
        ])
    assert exc_info.value.code == 0
    assert report_file.exists()

    content = report_file.read_text(encoding="utf-8")
    assert "# Experiment Report: CLI E2E Exp" in content
    assert "## Statistical Analysis" in content

    # ── 6. status ─────────────────────────────────────────────────────────
    capsys.readouterr()  # clear any previous output
    with pytest.raises(SystemExit) as exc_info:
        main([
            "status",
            "--state", str(state_file_4),
        ])
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "Workflow Status Summary" in captured.out
    assert "Step: analysis_created" in captured.out
    assert "Experiment: CLI E2E Exp" in captured.out
    assert "Analysis Status: Created" in captured.out

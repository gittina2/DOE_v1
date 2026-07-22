import pytest
from doe.models.experiment import Experiment
from doe.models.factor import Factor
from doe.models.response import Response
from doe.models.design import Design, Run
from doe.models.results import Results, ResultEntry
from doe.models.analysis import Analysis
from doe.models.workflow_state import WorkflowState
from doe.report_generation import format_markdown_report
from doe.models.exceptions import WorkflowStateMismatchError


def create_sample_experiment():
    f_temp = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0, unit="C")
    r_yield = Response(name="yield", type="continuous", unit="%")
    exp = Experiment(
        name="Yield Optimization",
        description="Testing temperature effects on yield",
        factors=[f_temp],
        responses=[r_yield],
        design_type="full_factorial",
        experiment_id="exp_rep_001",
    )
    exp.validate()
    return exp


def test_format_markdown_report_experiment_only():
    exp = create_sample_experiment()
    state = WorkflowState(step="experiment_created", experiment=exp)

    report = format_markdown_report(state)

    assert "# Experiment Report: Yield Optimization" in report
    assert "## Experiment Overview" in report
    assert "## Factors & Responses" in report
    assert "| temp | continuous | C | [100.0, 200.0] |" in report
    assert "| yield | continuous | % |" in report

    assert "## Experimental Design" not in report
    assert "## Experimental Results" not in report
    assert "## Statistical Analysis" not in report


def test_format_markdown_report_with_design():
    exp = create_sample_experiment()
    runs = [
        Run(run_id="run_001", factor_values={"temp": 100.0}, run_number=1),
        Run(run_id="run_002", factor_values={"temp": 200.0}, run_number=2),
    ]
    design = Design(
        experiment_ref=exp.experiment_id,
        design_type="full_factorial",
        runs=runs,
        design_id="des_rep_001",
    )

    state = WorkflowState(step="design_generated", experiment=exp, design=design)

    report = format_markdown_report(state)

    assert "# Experiment Report: Yield Optimization" in report
    assert "## Experimental Design" in report
    assert "- **Design ID**: des_rep_001" in report
    assert "| Run ID | Run Number | temp |" in report
    assert "| run_001 | 1 | 100.0 |" in report
    assert "| run_002 | 2 | 200.0 |" in report

    assert "## Experimental Results" not in report
    assert "## Statistical Analysis" not in report


def test_format_markdown_report_with_results():
    exp = create_sample_experiment()
    runs = [
        Run(run_id="run_001", factor_values={"temp": 100.0}, run_number=1),
        Run(run_id="run_002", factor_values={"temp": 200.0}, run_number=2),
    ]
    design = Design(
        experiment_ref=exp.experiment_id,
        design_type="full_factorial",
        runs=runs,
        design_id="des_rep_001",
    )
    entries = [
        ResultEntry(run_ref="run_001", values={"yield": 85.5}, status="complete"),
        ResultEntry(run_ref="run_002", values={"yield": 95.0}, status="complete"),
    ]
    results = Results(design_ref=design.design_id, entries=entries, completeness="complete", results_id="res_rep_001")

    state = WorkflowState(
        step="results_complete",
        experiment=exp,
        design=design,
        results=results,
    )

    report = format_markdown_report(state)

    assert "## Experimental Results" in report
    assert "- **Results ID**: res_rep_001" in report
    assert "| Run Reference | yield | Status |" in report
    assert "| run_001 | 85.5 | complete |" in report
    assert "| run_002 | 95.0 | complete |" in report

    assert "## Statistical Analysis" not in report


def test_format_markdown_report_full_analysis():
    exp = create_sample_experiment()
    runs = [
        Run(run_id="run_001", factor_values={"temp": 100.0}, run_number=1),
        Run(run_id="run_002", factor_values={"temp": 200.0}, run_number=2),
    ]
    design = Design(
        experiment_ref=exp.experiment_id,
        design_type="full_factorial",
        runs=runs,
        design_id="des_rep_001",
    )
    entries = [
        ResultEntry(run_ref="run_001", values={"yield": 85.5}, status="complete"),
        ResultEntry(run_ref="run_002", values={"yield": 95.0}, status="complete"),
    ]
    results = Results(design_ref=design.design_id, entries=entries, completeness="complete", results_id="res_rep_001")

    analysis = Analysis(
        experiment_ref=exp.experiment_id,
        design_ref=design.design_id,
        results_ref=results.results_id,
        model_type="linear",
        coefficients={"Intercept": 76.0, "temp": 0.095},
        anova_table=[
            {"source": "Model", "ss": 45.125, "df": 1, "ms": 45.125, "f_value": 120.0, "p_value": 0.001},
            {"source": "Residuals", "ss": 0.375, "df": 1, "ms": 0.375, "f_value": None, "p_value": None},
            {"source": "Total", "ss": 45.5, "df": 2, "ms": None, "f_value": None, "p_value": None},
        ],
        p_values={"Intercept": 0.001, "temp": 0.001},
        r_squared=0.9918,
        adjusted_r_squared=0.9835,
        analysis_id="ana_rep_001",
    )

    state = WorkflowState(
        step="analysis_created",
        experiment=exp,
        design=design,
        results=results,
        analysis=analysis,
    )

    report = format_markdown_report(state)

    assert "## Statistical Analysis" in report
    assert "- **R²**: 0.9918" in report
    assert "- **Adjusted R²**: 0.9835" in report
    assert "### Coefficients" in report
    assert "| Intercept | 76.0 | 0.001 |" in report
    assert "### ANOVA Table" in report
    assert "| Model | 45.125 | 1 | 45.125 | 120.0 | 0.001 |" in report


def test_format_markdown_report_missing_experiment():
    state = WorkflowState(step="empty")
    with pytest.raises(WorkflowStateMismatchError, match="Cannot generate report without an experiment defined"):
        format_markdown_report(state)

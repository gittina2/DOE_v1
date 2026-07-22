import os
import pytest
from doe.models.experiment import Experiment
from doe.models.factor import Factor
from doe.models.response import Response
from doe.models.workflow_state import WorkflowState
from doe.report_generation import generate_report
from doe.models.exceptions import DomainValidationError


def create_sample_workflow_state():
    f_temp = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    r_yield = Response(name="yield", type="continuous")
    exp = Experiment(
        name="Yield Optimization",
        factors=[f_temp],
        responses=[r_yield],
        design_type="full_factorial",
        experiment_id="exp_wf_rep_001",
    )
    state = WorkflowState(step="experiment_created", experiment=exp)
    state.validate()
    return state


def test_generate_report_workflow_success(tmp_path):
    state = create_sample_workflow_state()
    report_file = tmp_path / "report.md"

    new_state = generate_report(state, output_path=str(report_file), format="markdown")

    assert new_state.step == "report_generated"
    assert report_file.exists()

    content = report_file.read_text(encoding="utf-8")
    assert "# Experiment Report: Yield Optimization" in content
    assert new_state.audit.get("report_format") == "markdown"
    assert new_state.audit.get("output_path") == str(report_file)


def test_generate_report_unsupported_format():
    state = create_sample_workflow_state()
    with pytest.raises(DomainValidationError, match="Unsupported report format: 'pdf'"):
        generate_report(state, format="pdf")

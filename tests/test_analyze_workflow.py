import pytest
from doe.models.experiment import Experiment
from doe.models.factor import Factor
from doe.models.response import Response
from doe.models.design import Design, Run
from doe.models.results import Results, ResultEntry
from doe.models.workflow_state import WorkflowState
from doe.analysis_computation import analyze_experiment
from doe.models.exceptions import (
    WorkflowStateMismatchError,
    InconsistentReferenceError,
)


def create_results_complete_workflow_state():
    f_temp = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    f_press = Factor(name="pressure", type="continuous", lower_bound=1.0, upper_bound=2.0)
    r_yield = Response(name="yield", type="continuous")
    exp = Experiment(
        name="Yield Exp",
        factors=[f_temp, f_press],
        responses=[r_yield],
        design_type="full_factorial",
        experiment_id="exp_wf_001",
    )
    runs = [
        Run(run_id="run_1", factor_values={"temp": 100.0, "pressure": 1.0}, run_number=1),
        Run(run_id="run_2", factor_values={"temp": 100.0, "pressure": 2.0}, run_number=2),
        Run(run_id="run_3", factor_values={"temp": 200.0, "pressure": 1.0}, run_number=3),
        Run(run_id="run_4", factor_values={"temp": 200.0, "pressure": 2.0}, run_number=4),
    ]
    design = Design(
        experiment_ref=exp.experiment_id,
        design_type="full_factorial",
        runs=runs,
        design_id="des_wf_001",
    )
    entries = [
        ResultEntry(run_ref="run_1", values={"yield": 50.1}),
        ResultEntry(run_ref="run_2", values={"yield": 49.9}),
        ResultEntry(run_ref="run_3", values={"yield": 70.1}),
        ResultEntry(run_ref="run_4", values={"yield": 69.9}),
    ]
    results = Results(
        design_ref=design.design_id,
        entries=entries,
        completeness="complete",
        results_id="res_wf_001",
    )

    state = WorkflowState(
        step="results_complete",
        experiment=exp,
        design=design,
        results=results,
    )
    state.validate()
    return state


def test_analyze_experiment_success():
    state = create_results_complete_workflow_state()
    new_state = analyze_experiment(state)

    assert new_state.step == "analysis_created"
    assert new_state.analysis is not None
    assert new_state.analysis.experiment_ref == state.experiment.experiment_id
    assert new_state.analysis.design_ref == state.design.design_id
    assert new_state.analysis.results_ref == state.results.results_id
    assert "Intercept" in new_state.analysis.coefficients
    assert "temp" in new_state.analysis.coefficients


def test_analyze_experiment_invalid_step():
    state = create_results_complete_workflow_state()
    state.step = "design_generated"
    state.results = None

    with pytest.raises(WorkflowStateMismatchError, match="Step must be 'results_complete'"):
        analyze_experiment(state)


def test_analyze_experiment_mismatched_experiment_ref():
    state = create_results_complete_workflow_state()
    state.design.experiment_ref = "exp_wrong_id"

    with pytest.raises(InconsistentReferenceError, match="Design reference does not match experiment"):
        analyze_experiment(state)


def test_analyze_experiment_mismatched_design_ref():
    state = create_results_complete_workflow_state()
    state.results.design_ref = "des_wrong_id"

    with pytest.raises(InconsistentReferenceError, match="Results design_ref"):
        analyze_experiment(state)

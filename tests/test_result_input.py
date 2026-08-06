import pytest
from doe.models.experiment import Experiment
from doe.models.factor import Factor
from doe.models.response import Response
from doe.models.design import Design, Run
from doe.models.results import ResultEntry, Results
from doe.models.workflow_state import WorkflowState
from doe.result_input import insert_results
from doe.models.exceptions import (
    InvalidWorkflowTransitionError,
    UnknownRunIdError,
    InvalidResponseValueError,
    DuplicateResultForRunError,
)


@pytest.fixture
def sample_state():
    exp = Experiment(
        experiment_id="exp_001",
        name="Test Experiment",
        factors=[Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)],
        responses=[Response(name="yield", type="continuous")],
    )
    design = Design(
        design_id="des_001",
        design_type="full_factorial",
        experiment_ref="exp_001",
        runs=[
            Run(run_id="run_001", factor_values={"temp": 100.0}),
            Run(run_id="run_002", factor_values={"temp": 200.0}),
        ],
    )
    return WorkflowState(step="design_generated", experiment=exp, design=design)


def test_insert_results_partial(sample_state):
    entries = [ResultEntry(run_ref="run_001", values={"yield": 95.0})]
    new_state = insert_results(sample_state, entries)
    assert new_state.step == "results_in_progress"
    assert new_state.results is not None
    assert new_state.results.completeness == "partial"
    assert len(new_state.results.entries) == 1
    assert new_state.results.entries[0].run_ref == "run_001"


def test_insert_results_complete(sample_state):
    entries = [
        ResultEntry(run_ref="run_001", values={"yield": 95.0}),
        ResultEntry(run_ref="run_002", values={"yield": 92.0}),
    ]
    new_state = insert_results(sample_state, entries)
    assert new_state.step == "results_complete"
    assert new_state.results is not None
    assert new_state.results.completeness == "complete"
    assert len(new_state.results.entries) == 2


def test_insert_results_incremental_update(sample_state):
    # First insert partial result
    e1 = [ResultEntry(run_ref="run_001", values={"yield": 95.0})]
    state1 = insert_results(sample_state, e1)
    assert state1.step == "results_in_progress"

    # Insert remaining result
    e2 = [ResultEntry(run_ref="run_002", values={"yield": 92.0})]
    state2 = insert_results(state1, e2)
    assert state2.step == "results_complete"
    assert len(state2.results.entries) == 2


def test_insert_results_invalid_workflow_step():
    state = WorkflowState(step="empty")
    entries = [ResultEntry(run_ref="run_001", values={"yield": 95.0})]
    with pytest.raises(InvalidWorkflowTransitionError):
        insert_results(state, entries)


def test_insert_results_unknown_run_id(sample_state):
    entries = [ResultEntry(run_ref="run_999", values={"yield": 95.0})]
    with pytest.raises(UnknownRunIdError, match="Run reference 'run_999' does not exist"):
        insert_results(sample_state, entries)


def test_insert_results_invalid_response_name(sample_state):
    entries = [ResultEntry(run_ref="run_001", values={"unknown_response": 95.0})]
    with pytest.raises(InvalidResponseValueError, match="Response 'unknown_response' is not defined"):
        insert_results(sample_state, entries)


def test_insert_results_non_numeric_response(sample_state):
    entries = [ResultEntry(run_ref="run_001", values={"yield": "high"})]
    with pytest.raises(InvalidResponseValueError, match="Response value for 'yield' must be numeric"):
        insert_results(sample_state, entries)


def test_insert_results_duplicate_in_input(sample_state):
    entries = [
        ResultEntry(run_ref="run_001", values={"yield": 95.0}),
        ResultEntry(run_ref="run_001", values={"yield": 90.0}),
    ]
    with pytest.raises(DuplicateResultForRunError, match="Duplicate result entry for run 'run_001'"):
        insert_results(sample_state, entries)

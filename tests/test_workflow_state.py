from doe.design_generation import generate_design
from doe.models.design import Run
import pytest
from doe.models import (
    WorkflowState,
    Experiment,
    Design,
    Factor,
    Response,
    WorkflowStateMismatchError,
    DomainValidationError,
)

def test_valid_empty_state():
    ws = WorkflowState(step="empty")
    ws.validate()
    assert ws.step == "empty"
    assert ws.experiment is None
    assert ws.design is None
    assert ws.results is None
    assert ws.analysis is None
    assert ws.audit == {}

def test_valid_experiment_created_state():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Yield Optimization", factors=[f], responses=[r], design_type="full_factorial")
    
    ws = WorkflowState(step="experiment_created", experiment=exp, audit={"user": "martin"})
    ws.validate()
    assert ws.step == "experiment_created"
    assert ws.experiment == exp
    assert ws.audit == {"user": "martin"}

def test_empty_state_with_entities_error():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Yield Optimization", factors=[f], responses=[r], design_type="full_factorial")
    
    ws = WorkflowState(step="empty", experiment=exp)
    with pytest.raises(WorkflowStateMismatchError, match="no entities can be defined"):
        ws.validate()

def test_experiment_created_missing_experiment_error():
    ws = WorkflowState(step="experiment_created")
    with pytest.raises(WorkflowStateMismatchError, match="experiment must be defined"):
        ws.validate()

def test_experiment_created_with_other_entities_error():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Yield Optimization", factors=[f], responses=[r], design_type="full_factorial")
    
    ws = WorkflowState(step="experiment_created", experiment=exp, design={}) # design is defined but shouldn't be
    with pytest.raises(WorkflowStateMismatchError, match="design, results, and analysis must be None"):
        ws.validate()

def test_invalid_step_error():
    ws = WorkflowState(step="invalid_step") # type: ignore
    with pytest.raises(WorkflowStateMismatchError, match="Unsupported workflow step"):
        ws.validate()

def test_invalid_audit_error():
    ws1 = WorkflowState(step="empty", audit="not_a_dict") # type: ignore
    with pytest.raises(WorkflowStateMismatchError, match="Audit field must be a dictionary"):
        ws1.validate()

    ws2 = WorkflowState(step="empty", audit={123: "val"}) # type: ignore
    with pytest.raises(WorkflowStateMismatchError, match="keys must be strings"):
        ws2.validate()

def test_propagation_of_entity_validation():
    f = Factor(name="temp", type="continuous") # invalid: missing bounds
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Yield Optimization", factors=[f], responses=[r], design_type="full_factorial")
    
    ws = WorkflowState(step="experiment_created", experiment=exp)
    # validate should propagate Factor's validation exception
    with pytest.raises(DomainValidationError):
        ws.validate()

def test_serialization_round_trip():
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Yield Optimization", factors=[f], responses=[r], design_type="full_factorial")
    
    ws1 = WorkflowState(step="experiment_created", experiment=exp, audit={"action": "created"})
    d = ws1.to_dict()
    assert d["step"] == "experiment_created"
    assert d["audit"] == {"action": "created"}
    assert d["experiment"]["name"] == "Yield Optimization"
    assert d["design"] is None
    assert d["schema_version"] == "1.0"

    ws2 = WorkflowState.from_dict(d)
    assert ws1 == ws2

def test_serialization_round_trip_with_design():

    f = Factor(
        name="temp",
        type="continuous",
        lower_bound=0.0,
        upper_bound=100.0
    )

    r = Response(
        name="yield",
        type="continuous"
    )

    exp = Experiment(
        name="Yield Optimization",
        factors=[f],
        responses=[r],
        design_type="full_factorial"
    ) 

    design = Design(
        experiment_ref=exp.experiment_id,
        runs = [
        Run(
            factor_values={
                "temperature":0.0,
                "catalyst":"A"
            }
        )
    ]
    )

    ws1 = WorkflowState(
        step="design_generated",
        experiment=exp,
        design=design,
        audit={"action": "design_generated"}
    )

    d = ws1.to_dict()

    assert d["step"] == "design_generated"
    assert d["experiment"]["name"] == "Yield Optimization"
    assert d["design"] is not None

    ws2 = WorkflowState.from_dict(d)

    assert ws1 == ws2

def test_workflow_state_json_acceptance_with_design(tmp_path):
    f = Factor(
        name="temp",
        type="continuous",
        lower_bound=0.0,
        upper_bound=100.0
    )

    r = Response(
        name="yield",
        type="continuous"
    )

    exp = Experiment(
        name="Yield Optimization",
        factors=[f],
        responses=[r],
        design_type="full_factorial"
    )

    design = Design(
        experiment_ref=exp.experiment_id,
        runs = [
            Run(
                factor_values={
                    "temperature":0.0,
                    "catalyst":"A"
                }
            )
        ]
    )

    ws = WorkflowState(
        step="design_generated",
        experiment=exp,
        design=design
    )

    file_path = tmp_path / "workflow.json"

    ws.save_to_json(file_path)

    import json

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # Acceptance criteria
    assert data["experiment"] is not None
    assert data["design"] is not None

    assert data["results"] is None
    assert data["analysis"] is None

def test_valid_transition_experiment_created_to_design_generated(
    sample_experiment,
    sample_design,
):
    state = WorkflowState(
        step="experiment_created",
        experiment=sample_experiment,
        audit={
            "action": "create_experiment"
        },
    )

    new_state = state.transition_to(
        "design_generated",
        design=sample_design,
        audit={
            "action": "generate_design"
        },
    )

    assert new_state.step == "design_generated"
    assert new_state.experiment == sample_experiment
    assert new_state.design == sample_design
    assert new_state.results is None
    assert new_state.analysis is None


def test_invalid_transition_empty_to_design_generated():
    state = WorkflowState(
        step="empty"
    )

    with pytest.raises(WorkflowStateMismatchError):
        state.transition_to("design_generated")


def test_backward_transition_design_generated_to_experiment_created(
    sample_experiment,
    sample_design,
):
    state = WorkflowState(
        step="design_generated",
        experiment=sample_experiment,
        design=sample_design,
    )

    with pytest.raises(WorkflowStateMismatchError):
        state.transition_to("experiment_created")


def test_invalid_skip_transition_experiment_created_to_results_complete(
    sample_experiment,
    sample_design,
):
    state = WorkflowState(
        step="experiment_created",
        experiment=sample_experiment,
    )

    with pytest.raises(WorkflowStateMismatchError):
        state.transition_to(
            "results_complete",
            design=sample_design,
        )


def test_transition_preserves_previous_audit(
    sample_experiment,
    sample_design,
):
    state = WorkflowState(
        step="experiment_created",
        experiment=sample_experiment,
        audit={
            "experiment_id": sample_experiment.experiment_id
        },
    )

    new_state = state.transition_to(
        "design_generated",
        design=sample_design,
        audit={
            "design_id": sample_design.design_id
        },
    )

    assert new_state.audit["experiment_id"] == sample_experiment.experiment_id
    assert new_state.audit["design_id"] == sample_design.design_id

def test_design_generation_end_to_end(
    sample_workflow_state,
    tmp_path
):

    # Generate design
    generated_state = generate_design(sample_workflow_state)

    assert generated_state.step == "design_generated"
    assert generated_state.design is not None

    # Validate generated runs
    assert len(generated_state.design.runs) == 4

    # Persist
    file_path = tmp_path / "workflow.json"
    generated_state.save_to_json(file_path)

    # Reload
    loaded_state = WorkflowState.load_from_json(file_path)

    # Integrity after serialization
    assert loaded_state.step == "design_generated"
    assert loaded_state.design is not None
    assert loaded_state.design.runs == generated_state.design.runs
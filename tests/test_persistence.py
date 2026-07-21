import pytest
from doe.models import (
    WorkflowState,
    Experiment,
    Factor,
    Response,
    SchemaVersionMismatchError,
    WorkflowStateMismatchError,
)

def test_persistence_empty_state_roundtrip(tmp_path):
    ws = WorkflowState(step="empty", audit={"initial": "true"})
    file_path = tmp_path / "workflow.json"
    
    # Save
    ws.save_to_json(str(file_path))
    assert file_path.exists()
    
    # Load
    ws_loaded = WorkflowState.load_from_json(str(file_path))
    assert ws == ws_loaded

def test_persistence_experiment_created_roundtrip(tmp_path):
    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Yield Optimization", factors=[f], responses=[r], design_type="full_factorial")
    
    ws = WorkflowState(step="experiment_created", experiment=exp, audit={"user": "martin"})
    file_path = tmp_path / "workflow.json"
    
    # Save
    ws.save_to_json(str(file_path))
    
    # Load
    ws_loaded = WorkflowState.load_from_json(str(file_path))
    assert ws == ws_loaded
    assert ws_loaded.experiment.name == "Yield Optimization"
    assert ws_loaded.experiment.factors[0].name == "temp"

def test_persistence_version_mismatch(tmp_path):
    file_path = tmp_path / "workflow_bad_ver.json"
    import json
    # Writing JSON with invalid schema version
    bad_data = {
        "schema_version": "2.0",
        "step": "empty",
        "audit": {},
        "experiment": None,
        "design": None,
        "results": None,
        "analysis": None
    }
    with open(file_path, mode="w", encoding="utf-8") as f:
        json.dump(bad_data, f)
        
    with pytest.raises(SchemaVersionMismatchError, match="Unsupported schema version: 2.0"):
        WorkflowState.load_from_json(str(file_path))

def test_persistence_invalid_state_on_load(tmp_path):
    file_path = tmp_path / "workflow_bad_state.json"
    import json
    # Writing JSON with inconsistent step (empty but has experiment)
    bad_data = {
        "schema_version": "1.0",
        "step": "empty",
        "audit": {},
        "experiment": {
            "schema_version": "1.0",
            "experiment_id": "exp123",
            "name": "Yield Optimization",
            "description": None,
            "factors": [],
            "responses": [],
            "design_type": "full_factorial",
            "planned_runs": None,
            "metadata": None
        },
        "design": None,
        "results": None,
        "analysis": None
    }
    with open(file_path, mode="w", encoding="utf-8") as f:
        json.dump(bad_data, f)
        
    with pytest.raises(WorkflowStateMismatchError, match="no entities can be defined"):
        WorkflowState.load_from_json(str(file_path))

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
    exp = Experiment(name="Yield Optimization", factors=[f], responses=[r])
    
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
        "schema_version": "1.1",
        "step": "empty",
        "audit": {},
        "experiment": {
            "schema_version": "1.1",
            "experiment_id": "exp123",
            "name": "Yield Optimization",
            "description": None,
            "factors": [],
            "responses": [],
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


def test_persistence_results_roundtrip(tmp_path):
    from doe.models.design import Design, Run
    from doe.models.results import ResultEntry, Results

    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Yield Optimization", factors=[f], responses=[r])
    design = Design(
        design_id="des_001",
        design_type="full_factorial",
        experiment_ref=exp.experiment_id,
        runs=[
            Run(run_id="run_001", factor_values={"temp": 0.0}),
            Run(run_id="run_002", factor_values={"temp": 100.0}),
        ],
    )
    res_entry1 = ResultEntry(run_ref="run_001", values={"yield": 94.2}, status="complete")
    res_entry2 = ResultEntry(run_ref="run_002", values={"yield": 96.8}, status="complete")
    results = Results(design_ref=design.design_id, entries=[res_entry1, res_entry2], completeness="complete")


    ws = WorkflowState(
        step="results_complete",
        experiment=exp,
        design=design,
        results=results,
        audit={"step": "results_complete"},
    )

    file_path = tmp_path / "workflow_results.json"
    ws.save_to_json(str(file_path))

    ws_loaded = WorkflowState.load_from_json(str(file_path))
    assert ws_loaded == ws
    assert ws_loaded.step == "results_complete"
    assert ws_loaded.results is not None
    assert ws_loaded.results.completeness == "complete"
    assert len(ws_loaded.results.entries) == 2
    assert ws_loaded.results.entries[0].run_ref == "run_001"
    assert ws_loaded.results.entries[0].values == {"yield": 94.2}


def test_persistence_analysis_created_roundtrip(tmp_path):
    from doe.models.design import Design, Run
    from doe.models.results import ResultEntry, Results
    from doe.models.analysis import Analysis

    f = Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0)
    r = Response(name="yield", type="continuous")
    exp = Experiment(name="Yield Optimization", factors=[f], responses=[r])
    design = Design(
        design_id="des_001",
        design_type="full_factorial",
        experiment_ref=exp.experiment_id,
        runs=[
            Run(run_id="run_001", factor_values={"temp": 0.0}),
            Run(run_id="run_002", factor_values={"temp": 100.0}),
        ],
    )
    res_entry1 = ResultEntry(run_ref="run_001", values={"yield": 94.2}, status="complete")
    res_entry2 = ResultEntry(run_ref="run_002", values={"yield": 96.8}, status="complete")
    results = Results(design_ref=design.design_id, entries=[res_entry1, res_entry2], completeness="complete")

    analysis = Analysis(
        experiment_ref=exp.experiment_id,
        design_ref=design.design_id,
        results_ref=results.results_id,
        model_type="linear",
        coefficients={"Intercept": 94.2, "temp": 0.026},
        r_squared=0.99,
        adjusted_r_squared=0.98,
        residuals=[0.0, 0.0],
    )

    ws = WorkflowState(
        step="analysis_created",
        experiment=exp,
        design=design,
        results=results,
        analysis=analysis,
        audit={"step": "analysis_created"},
    )

    file_path = tmp_path / "workflow_analysis.json"
    ws.save_to_json(str(file_path))

    ws_loaded = WorkflowState.load_from_json(str(file_path))
    assert ws_loaded == ws
    assert ws_loaded.step == "analysis_created"
    assert ws_loaded.analysis is not None
    assert isinstance(ws_loaded.analysis, Analysis)
    assert ws_loaded.analysis.coefficients == {"Intercept": 94.2, "temp": 0.026}
    assert ws_loaded.analysis.r_squared == 0.99




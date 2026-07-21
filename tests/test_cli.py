import pytest
import sys
from doe.main import main
from doe.models import WorkflowState

def test_cli_init_experiment_success(tmp_path, capsys):
    # Setup temporary CSV factors file
    csv_file = tmp_path / "factors.csv"
    csv_file.write_text(
        "name,type,unit,lower_bound,upper_bound\ntemp,continuous,C,0,100\nconc,continuous,%,10,50",
        encoding="utf-8"
    )
    
    output_state_file = tmp_path / "workflow.json"
    
    # Run CLI
    args = [
        "init-experiment",
        "--name", "My Experiment",
        "--factors-csv", str(csv_file),
        "--response", "yield:continuous:g",
        "--response", "purity:continuous:%",
        "--design-type", "full_factorial",
        "--planned-runs", "16",
        "--description", "This is a test run",
        "--output", str(output_state_file)
    ]
    
    with pytest.raises(SystemExit) as exc_info:
        main(args)
        
    assert exc_info.value.code == 0
    
    # Check printed message
    captured = capsys.readouterr()
    assert "Experiment successfully created" in captured.out
    
    # Verify WorkflowState output
    assert output_state_file.exists()
    state = WorkflowState.load_from_json(str(output_state_file))
    assert state.step == "experiment_created"
    assert state.experiment.name == "My Experiment"
    assert len(state.experiment.factors) == 2
    assert len(state.experiment.responses) == 2
    assert state.experiment.design_type == "full_factorial"
    assert state.experiment.planned_runs == 16
    assert state.experiment.description == "This is a test run"

def test_cli_init_experiment_invalid_csv(tmp_path, capsys):
    # Setup malformed factors file (missing 'type' column)
    csv_file = tmp_path / "bad_factors.csv"
    csv_file.write_text("name,lower_bound,upper_bound\ntemp,0,100", encoding="utf-8")
    
    output_state_file = tmp_path / "workflow.json"
    
    args = [
        "init-experiment",
        "--name", "Bad Experiment",
        "--factors-csv", str(csv_file),
        "--response", "yield:continuous:g",
        "--design-type", "full_factorial",
        "--output", str(output_state_file)
    ]
    
    with pytest.raises(SystemExit) as exc_info:
        main(args)
        
    assert exc_info.value.code == 1
    
    captured = capsys.readouterr()
    assert "Missing required columns in CSV header" in captured.err
    assert not output_state_file.exists()

def test_cli_init_experiment_domain_validation_failure(tmp_path, capsys):
    csv_file = tmp_path / "factors.csv"
    csv_file.write_text("name,type,lower_bound,upper_bound\ntemp,continuous,100,0", encoding="utf-8") # invalid bounds
    
    output_state_file = tmp_path / "workflow.json"
    
    args = [
        "init-experiment",
        "--name", "Bad Bounds Exp",
        "--factors-csv", str(csv_file),
        "--response", "yield:continuous:g",
        "--design-type", "full_factorial",
        "--output", str(output_state_file)
    ]
    
    with pytest.raises(SystemExit) as exc_info:
        main(args)
        
    assert exc_info.value.code == 1
    
    captured = capsys.readouterr()
    assert "Domain Validation/Workflow Error" in captured.err
    assert "must be less than upper_bound" in captured.err
    assert not output_state_file.exists()

def test_cli_init_experiment_invalid_response_format(tmp_path, capsys):
    csv_file = tmp_path / "factors.csv"
    csv_file.write_text("name,type,lower_bound,upper_bound\ntemp,continuous,0,100", encoding="utf-8")
    
    output_state_file = tmp_path / "workflow.json"
    
    args = [
        "init-experiment",
        "--name", "Bad Response Exp",
        "--factors-csv", str(csv_file),
        # Empty response string or unsupported format
        "--response", "",
        "--design-type", "full_factorial",
        "--output", str(output_state_file)
    ]
    
    with pytest.raises(SystemExit) as exc_info:
        main(args)
        
    assert exc_info.value.code == 1
    
    captured = capsys.readouterr()
    assert "Response name is required" in captured.err or "Invalid response format" in captured.err
    assert not output_state_file.exists()

def test_cli_no_arguments(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main([])
        
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "show this help message and exit" in captured.out or "show this help message and exit" in captured.err

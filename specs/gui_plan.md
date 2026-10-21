# Implementation Plan: Minimal Desktop GUI for DOE Toolkit (PySide6)
I have inspected the existing repository at C:\Users\marti\Documents\DOE_v1. All 184 existing automated tests run and pass cleanly.

Below is the inspection summary and the proposed architectural plan for integrating the PySide6 desktop GUI.

## 1. Codebase Inspection Summary
### Architecture & Current State
- Core Package (doe/): Completely decoupled domain and workflow engine written with standard library tools (dataclasses, typing, json, math, uuid).
- CLI (doe/main.py): Subcommand-based interface (init-experiment, generate-design, insert-results, analyze, report, status). Operates without GUI dependencies.
- Persistence: Strict JSON serialization implemented on WorkflowState.save_to_json(file_path) and WorkflowState.load_from_json(file_path) supporting schema versions 1.0 and 1.1.
- Dependencies: The core engine requires zero third-party packages at runtime (with optional scipy.stats fallback). requirements.txt currently contains PySide6. Both PySide6 (6.12.0) and pytest (9.1.1) are already installed and verified in the environment.

### Core Entities & Functions Reused by the GUI

#### 1. Experiment Creation:
- create_experiment(name: str, factors: List[Factor], responses: List[Response], description: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> WorkflowState

#### 2. Domain Models:
- Factor(name, type, unit, levels, lower_bound, upper_bound):
    - continuous: requires lower_bound < upper_bound (floats), no levels.
    - categorical: requires levels (list of $\ge 2$ unique items), optional unit.
- Response(name, type="continuous", unit=None): Continuous responses only.
- Experiment(name, factors, responses, description, experiment_id, ...)
- WorkflowState(step, experiment, design, results, analysis, audit, ...)

#### 3. Workflow & Domain Exceptions:
- DomainValidationError, InvalidFactorTypeError, InvalidFactorBoundsError, MissingFactorLevelsError, DuplicateFactorNameError, DuplicateFactorLevelsError, MissingResponseError, InvalidResponseTypeError, WorkflowStateMismatchError, SchemaVersionMismatchError.

## 2. Minimal GUI Module Structure
The GUI will be added as a thin layer in doe/gui/ without modifying any domain or workflow logic:

```
doe/
├── gui/
│   ├── __init__.py               # Exports main entry point
│   ├── __main__.py              # Allows launching via: python -m doe.gui
│   ├── app.py                   # Application bootstrapping & PySide6 QApplication lifecycle
│   ├── session.py               # GUI Session state (active WorkflowState, current_file_path, is_dirty)
│   ├── main_window.py           # Persistent sidebar, QStackedWidget navigation, toolbar/actions
│   ├── views/
│   │   ├── __init__.py
│   │   ├── experiment_view.py   # Functional Experiment view (inputs, factor/response tables, creation summary)
│   │   └── placeholder_view.py  # Informative placeholder for Design, Results, Analysis, Report
│   └── dialogs/
│       ├── __init__.py
│       ├── factor_dialog.py     # Adaptive dialog for Continuous vs Categorical factors
│       └── response_dialog.py   # Dialog for Response (name, optional unit)
run_gui.py                       # Root-level convenience launcher
tests/
└── test_gui.py                  # PySide6 offscreen GUI test suite
```

## 3. Key Design Decisions

### 1. Launching without CLI Disruption:

Primary launch command: python -m doe.gui or python run_gui.py.
doe/main.py remains untouched, preserving the existing CLI subcommands.

### 2. Persistent Sidebar & Navigation:
A persistent left sidebar with navigation buttons for:
- Experiment (fully functional)
- Design (placeholder)
- Results (placeholder)
- Analysis (placeholder)
- Report (placeholder)

A status indicator reflecting the active workflow step (e.g. Empty, Experiment Created, Design Generated, etc.).
Navigation between sections remains unrestricted at all times.
### 3. Workflow File Operations & Dirty Tracking:
- New: Prompts to save if unsaved modifications exist, then resets to empty workflow state.
- Open Workflow: Prompts for file, loads via WorkflowState.load_from_json, updates current file path, and populates the GUI. Catches JSON errors, schema mismatches, and domain validation errors gracefully.
- Save: Saves directly to current_file_path via WorkflowState.save_to_json. If no path exists, delegates to Save As.
- Save As: Prompts for a destination .json file, saves state, and updates current_file_path.
### 4. Experiment Replacement & Downstream Invalidation:
- If downstream entities (design, results, analysis) exist in the active workflow and the user clicks Create Experiment, the GUI warns the user that downstream data will be reset.
- Upon confirmation, calls create_experiment(...) which assigns a fresh experiment_id and produces a clean WorkflowState(step="experiment_created").
- Marks the workflow as unsaved without touching the existing file on disk until the user explicitly saves.
### 5. Factor & Response Management:
- Dynamic dialog for factors switching between numeric lower/upper bounds (Continuous) and comma-separated/itemized category levels (Categorical).
- Validation is delegated to Factor.validate() and Response.validate() with error messages shown in user-friendly dialogs.
### 6. Dependency Management:
Ensure requirements.txt specifies:
```
PySide6>=6.5.0
pytest>=7.0.0
```

## 4. Implementation Steps

- Step 1: Verify requirements.txt and create the doe/gui/ structure and run_gui.py.
- Step 2: Implement app.py, session.py, main_window.py, and placeholder_view.py with persistent navigation, file actions, and workflow step indicator.
- Step 3: Implement factor_dialog.py, response_dialog.py, and experiment_view.py with full factor/response CRUD, experiment creation, error surfacing, and summary display.
- Step 4: Connect New, Open, Save, Save As, and downstream reset confirmations.
- Step 5: Implement tests/test_gui.py running in headless mode (QT_QPA_PLATFORM=offscreen) verifying:
    - Window initialization and section switching.
    - Experiment creation with continuous and categorical factors.
    - Surfacing of domain validation errors.
    - File save/load roundtrips and error handling on corrupted/unsupported JSON.
    - Downstream data reset behavior.
Ensure all 184 existing unit tests continue to pass.
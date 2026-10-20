# DOE Core Engine (DOE_v1)

A modular, contract-driven Python engine and CLI tool for orchestrating Design of Experiments (DOE) workflows. Built as a personal engineering project to explore Domain-Driven Design (DDD), Finite State Machine (FSM) state tracking, and algorithmic experimental design without external framework bloat.

---

## Project Overview

In experimental research and lab environments, planning multi-factor experiments and running downstream statistical regressions is often handled manually across disconnected spreadsheets or opaque commercial software. This leads to configuration errors, inconsistent parameter scaling, and lost traceability.

`DOE_v1` provides a deterministic, lightweight command-line engine that guides an experiment through a strict, sequential lifecycle. The system validates domain invariants at every stage (Design by Contract), persists state transitions immutably in JSON files, and generates structured Markdown summary reports.

---

## Features

- **Experimental Design Generation**:
  - **Full Factorial**: Generates all Cartesian combinations ($2^k$ for continuous factors using lower and upper bounds, and full level sets for categorical factors) via `FullFactorialGenerator` in `doe/designs/full_factorial.py`.
  - **Fractional Factorial**: Generates standard half-fraction ($2^{k-1}$) subsets for $k \ge 3$ factors using parity defining relations, with automatic fallback to full factorial for $k < 3$, via `FractionalFactorialGenerator` in `doe/designs/fractional_factorial.py`.
- **Factor Level Coding**:
  - Implemented in `doe/designs/utils.py` (`generate_factor_codings`) and modeled in `doe/models/design.py` (`FactorCoding`).
  - Maps natural experimental bounds into standard two-level $[-1.0, +1.0]$ coded space with built-in linear interpolation/extrapolation for continuous intermediate values.
- **Statistical Modeling & ANOVA**:
  - **Models Available**: User-selectable regression models (`linear`, pairwise `interaction`, and `quadratic` with squared terms for continuous factors), located in `doe/statistics/`.
  - **Custom OLS Matrix Solver**: Native Python linear algebra routines (`_matrix_multiply`, `_matrix_transpose`, and `_matrix_inverse` via Gauss-Jordan elimination with partial pivoting) that detect singular matrices and raise `NonEstimableModelError`.
  - **ANOVA & Diagnostics**: Computes Sum of Squares ($SS$), Degrees of Freedom ($DF$), Mean Squares ($MS$), $F$-statistic, $R^2$, adjusted $R^2$, and $p$-values (using `scipy.stats` when available, with an internal analytical fallback).
- **Data Ingestion & Validation**:
  - Factor definition import (`doe/imports/csv_factor_importer.py`) with row-level validation and detailed error reporting (`CsvRowImportError`).
  - Experimental result import (`doe/imports/csv_result_importer.py`) supporting run mapping via `run_id` or `run_number`.
- **State Machine & JSON Persistence**:
  - Strict finite state machine in `doe/models/workflow_state.py` validating state invariants across steps (`empty` $\to$ `experiment_created` $\to$ `design_generated` $\to$ `results_in_progress` / `results_complete` $\to$ `analysis_created` $\to$ `report_generated`).
  - Full round-trip JSON serialization with version tracking and an append-only audit trail.
- **Markdown Report Generation**:
  - Produces structured, publication-ready GitHub-flavored Markdown reports (`doe/report_generation.py`) containing factor/response tables, run matrices, recorded responses, and complete ANOVA tables.
- **CLI Interface**:
  - Complete CLI entry point (`doe/main.py`) exposing subcommands for each step of the pipeline.

---

## Workflow

The workflow follows a strict state transition graph:

```
[ CSV Factor File ]
         │
         ▼
  init-experiment     ──► Step: experiment_created (WorkflowState JSON)
         │
         ▼
  generate-design     ──► Step: design_generated (Runs + FactorCoding)
         │
         ▼
   insert-results     ──► Step: results_in_progress / results_complete
         │
         ▼
      analyze         ──► Step: analysis_created (OLS + ANOVA)
         │
         ▼
      report          ──► Step: report_generated (Markdown Report)
```

Each command reads a valid `WorkflowState` JSON file, performs its action, verifies preconditions and postconditions, and writes back an updated state.

---

## Installation

### Requirements

- Python 3.10+ (tested on Python 3.13)
- Optional: `scipy` (for exact $t$ and $F$ distribution $p$-values; if absent, an internal analytical approximation is used)
- Test dependencies: `pytest`

### Setup

1. Clone or download the repository:
   ```bash
   git clone <repository-url>
   cd DOE_v1
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. (Optional) Install `scipy` and `pytest`:
   ```bash
   pip install scipy pytest
   ```

---

## Usage

All commands are executed through `doe/main.py` using `python -m doe.main`.

### 1. Initialize an Experiment
Define factors in a CSV file (e.g., `factors.csv`):
```csv
name,type,unit,lower_bound,upper_bound
temperature,continuous,C,100,200
pressure,continuous,bar,1,3
```

Run `init-experiment`:
```bash
python -m doe.main init-experiment \
  --name "Reaction_Study" \
  --factors-csv factors.csv \
  --response "yield:continuous:%" \
  --output state_01.json
```

### 2. Generate a Design
Generate a full factorial design (default) or fractional factorial design:
```bash
python -m doe.main generate-design \
  --state state_01.json \
  --design-type full_factorial \
  --output state_02.json
```

### 3. Check Workflow Status
Inspect the current state and completed runs:
```bash
python -m doe.main status --state state_02.json
```

### 4. Insert Experimental Results
Provide measured results in a CSV file referencing `run_id` or `run_number` (e.g., `results.csv`):
```csv
run_number,yield
1,54.2
2,62.1
3,78.5
4,89.0
```

Import the results into the state:
```bash
python -m doe.main insert-results \
  --state state_02.json \
  --csv results.csv \
  --output state_03.json
```

### 5. Run Statistical Analysis
Compute OLS regression (`linear`, `interaction`, or `quadratic`):
```bash
python -m doe.main analyze \
  --state state_03.json \
  --model-type interaction \
  --output state_04.json
```

### 6. Generate a Markdown Report
Generate a summary report:
```bash
python -m doe.main report \
  --state state_04.json \
  --output report.md
```

---

## Testing

The project includes unit, integration, and end-to-end tests covering models, importers, design algorithms, matrix algebra, CLI handlers, and persistence.

Run the test suite with:
```bash
python -m pytest tests/
```

**Verified Test Result:**
- **184 passed in 1.17s** (executed across 28 test files in `tests/`, 100% pass rate).

---

## Current Limitations

- **Design Strategies**: Only two-level full factorial and $2^{k-1}$ half-fraction designs are implemented. Higher fractional resolutions ($2^{k-p}$ for $p > 1$), Plackett-Burman, and response surface designs (e.g., Central Composite or Box-Behnken) are not implemented.
- **Continuous Factor Discretization**: The full factorial generator samples continuous factors strictly at two points (`lower_bound` and `upper_bound`).
- **No Automatic Randomization/Blocking**: The `Design` model includes schema fields for `randomization`, `replications`, and `Block`, but design generators currently emit deterministic standard-order runs without automated block assignment.
- **Response Types**: Only continuous response variables (`type="continuous"`) are supported. Categorical or count responses are rejected by domain validation.
- **Report Formats**: Report export is currently limited to GitHub-flavored Markdown.
- **Persistence Backend**: State persistence is file-based JSON only; there is no relational or database storage layer.

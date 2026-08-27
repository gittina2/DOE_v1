# Implementation Plan — Technical Specification Extension v1.1

## Goal

Implement the changes defined in [technical_spec_extention1.md](file:///c:/Users/marti/Documents/DOE_v1/specs/technical_spec_extention1.md) on top of the current codebase governed by [technical_spec.md](file:///c:/Users/marti/Documents/DOE_v1/specs/technical_spec.md).

The extension introduces five interconnected changes:

1. Remove `design_type` and `planned_runs` from Experiment (separation of concerns).
2. Move `design_type` selection into `generate_design()` via `DesignGenerationOptions`.
3. Add `FactorCoding` model and generate factor coding during design generation.
4. Add user-selectable statistical models (`linear`, `interaction`, `quadratic`).
5. Add `formula` and `terms` fields to the Analysis model.

---

## 1. Current Architecture Assessment

### 1.1 Existing Modules

| Module | File | Responsibility |
|---|---|---|
| **Factor model** | [factor.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/factor.py) | Dataclass + validation for `Factor` (continuous / categorical) |
| **Response model** | [response.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/response.py) | Dataclass + validation for `Response` (continuous only) |
| **Experiment model** | [experiment.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/experiment.py) | Dataclass + validation for `Experiment` — **currently includes `design_type` and `planned_runs`** |
| **Design model** | [design.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/design.py) | `Run`, `Block`, `Design` dataclasses — `Design.validate()` **compares `self.design_type` to `experiment.design_type`** |
| **Results model** | [results.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/results.py) | `ResultEntry`, `Results` dataclasses |
| **Analysis model** | [analysis.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/analysis.py) | Analysis dataclass — already has `model_type` (defaults to `"linear"`) and `model_formula`, but **no `formula` or `terms` fields** |
| **Exceptions** | [exceptions.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/exceptions.py) | Full hierarchy of domain/workflow/design/analysis/CSV exceptions |
| **WorkflowState** | [workflow_state.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/workflow_state.py) | State machine with `transition_to()`, `save_to_json()`, `load_from_json()` |
| **Models `__init__`** | [\_\_init\_\_.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/__init__.py) | Re-exports all domain types including `DesignType` |
| **Generator interface** | [generator_interface.py](file:///c:/Users/marti/Documents/DOE_v1/doe/designs/generator_interface.py) | Abstract `DesignGenerator` with `generate(experiment)` |
| **Full factorial** | [full_factorial.py](file:///c:/Users/marti/Documents/DOE_v1/doe/designs/full_factorial.py) | Concrete generator — **checks `experiment.design_type == "full_factorial"`** |
| **Experiment creation** | [experiment_creation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/experiment_creation.py) | `create_experiment()` — accepts `design_type` parameter |
| **Design generation** | [design_generation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/design_generation.py) | `generate_design(state)` — reads `experiment.design_type` to pick generator |
| **Result input** | [result_input.py](file:///c:/Users/marti/Documents/DOE_v1/doe/result_input.py) | `insert_results()` orchestration |
| **Analysis computation** | [analysis_computation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/analysis_computation.py) | `fit_linear_model()` + `analyze_experiment(state)` — **hardcoded to linear model** |
| **Report generation** | [report_generation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/report_generation.py) | Markdown report — **reads `exp.design_type`** in report text |
| **CLI** | [main.py](file:///c:/Users/marti/Documents/DOE_v1/doe/main.py) | argparse CLI — `init-experiment` has `--design-type` flag, `analyze` has no model selection |
| **CSV importers** | [doe/imports/](file:///c:/Users/marti/Documents/DOE_v1/doe/imports/) | `csv_factor_importer.py`, `csv_result_importer.py` |

### 1.2 Current Domain Models

```
Experiment
  ├── design_type: DesignType         ← TO BE REMOVED
  ├── planned_runs: int | None        ← TO BE REMOVED
  ├── factors: list[Factor]
  ├── responses: list[Response]
  └── ...

Design
  ├── design_type: str
  ├── experiment_ref: str
  ├── runs: list[Run]
  ├── blocks: list[Block]
  └── ...                              ← MISSING: factor_coding, replications

Analysis
  ├── model_type: str = "linear"
  ├── model_formula: str | None
  └── ...                              ← MISSING: formula, terms
```

### 1.3 Current Workflow Implementation

- `create_experiment()` → builds `Experiment` with `design_type` → returns `WorkflowState(step="experiment_created")`
- `generate_design(state)` → reads `experiment.design_type` → dispatches to `FullFactorialGenerator` → returns `WorkflowState(step="design_generated")`
- `Design.validate(experiment)` checks `self.design_type == experiment.design_type`
- `FullFactorialGenerator.generate()` checks `experiment.design_type == "full_factorial"`
- `analyze_experiment(state)` → always calls `fit_linear_model()` (hardcoded)

### 1.4 Current Test Coverage

**175 tests, all passing** across 28 test files:

| Test File | Tests | Covers |
|---|---|---|
| `test_factor.py` | 7 | Factor model validation |
| `test_response.py` | 3 | Response model validation |
| `test_experiment.py` | 11 | Experiment model validation, serialization |
| `test_design.py` | 7 | Design model validation |
| `test_run.py` | 9 | Run model validation |
| `test_block.py` | 6 | Block model validation |
| `test_results.py` | 8 | Results & ResultEntry validation |
| `test_analysis_model.py` | 7 | Analysis model validation, serialization |
| `test_workflow_state.py` | 14 | State machine validation, transitions, serialization |
| `test_experiment_creation.py` | 5 | `create_experiment()` orchestration |
| `test_design_generation.py` | 5 | `generate_design()` orchestration |
| `test_full_factorial.py` | 12 | Full factorial generator |
| `test_result_input.py` | 7 | `insert_results()` orchestration |
| `test_analysis_computation.py` | 4 | `fit_linear_model()` computation |
| `test_analyze_workflow.py` | 4 | `analyze_experiment()` orchestration |
| `test_report_generation.py` | 9 | Report generation |
| `test_report_workflow.py` | 3 | Report workflow transitions |
| `test_persistence.py` | 9 | JSON round-trip persistence |
| `test_e2e_full_workflow.py` | 2 | Full lifecycle (API + CLI) |
| `test_cli*.py` | 15 | CLI handlers |
| `test_csv_*.py` | 14 | CSV import/parsing |
| `test_exceptions.py` | 2 | Exception hierarchy |
| `conftest.py` | — | Shared fixtures (use `design_type="full_factorial"`) |

---

## 2. Impact Analysis

### 2.1 Moving `design_type` from Experiment to Design generation

> **High-impact, cross-cutting change. Affects nearly every module.**

| Component | Impact |
|---|---|
| [experiment.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/experiment.py) | Remove `design_type` and `planned_runs` fields, remove from `validate()`, `to_dict()`, `from_dict()` |
| [experiment_creation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/experiment_creation.py) | Remove `design_type` parameter from `create_experiment()` |
| [design.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/design.py) L192-196 | `Design.validate()` currently checks `self.design_type == experiment.design_type` — this check must be **removed** since Experiment no longer has `design_type` |
| [design_generation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/design_generation.py) L71 | `generate_design()` currently reads `experiment.design_type` — must accept `design_type` as an explicit parameter |
| [full_factorial.py](file:///c:/Users/marti/Documents/DOE_v1/doe/designs/full_factorial.py) L132 | Generator checks `experiment.design_type == "full_factorial"` — must be **removed or refactored** (the dispatcher already handles this) |
| [main.py](file:///c:/Users/marti/Documents/DOE_v1/doe/main.py) L201-206 | `--design-type` must move from `init-experiment` to `generate-design` CLI subcommand |
| [report_generation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/report_generation.py) L28 | Report reads `exp.design_type` — must read from `design.design_type` instead |
| [models/\_\_init\_\_.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/__init__.py) | `DesignType` was defined in `experiment.py` — needs to move to `design.py` or a shared types module |
| [conftest.py](file:///c:/Users/marti/Documents/DOE_v1/tests/conftest.py) L42 | `sample_experiment` fixture uses `design_type=` — must be updated |
| **18+ test files** | All tests that create `Experiment` objects with `design_type` must be updated |
| [workflow_state.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/workflow_state.py) L166 | `load_from_json` hardcodes `schema_version == "1.0"` — needs to accept `"1.1"` |

### 2.2 Adding Factor Coding

| Component | Impact |
|---|---|
| [design.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/design.py) | Add `factor_coding: list[FactorCoding] | None` field, add `FactorCoding` dataclass, update `to_dict()`/`from_dict()` |
| [full_factorial.py](file:///c:/Users/marti/Documents/DOE_v1/doe/designs/full_factorial.py) | Optionally generate `FactorCoding` when creating the design |
| [design_generation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/design_generation.py) | Pass through coding configuration |
| [models/\_\_init\_\_.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/__init__.py) | Export `FactorCoding` |
| New test file | `test_factor_coding.py` — validation, serialization, round-trip |

### 2.3 Adding Fractional Factorial Design Support

| Component | Impact |
|---|---|
| **New file**: `doe/designs/fractional_factorial.py` | Implement `FractionalFactorialGenerator` |
| [design_generation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/design_generation.py) L9-11 | Register `"fractional_factorial"` → `FractionalFactorialGenerator` in `_DESIGN_GENERATORS` |
| [design.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/design.py) L198-210 | `Design.validate()` run-count check is hardcoded for `full_factorial` only — must be extended |
| New test file | `test_fractional_factorial.py` |

### 2.4 Introducing Selectable Statistical Models

| Component | Impact |
|---|---|
| [analysis.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/analysis.py) | Add `formula: str | None` and `terms: list[str] | None` fields (note: `model_formula` already exists — needs alignment with spec). Define `ModelType`. |
| [analysis_computation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/analysis_computation.py) | `analyze_experiment()` must accept `model_type` parameter; must dispatch to the correct model implementation |
| **New directory**: `doe/statistics/` | Create package with `__init__.py` |
| **New file**: `doe/statistics/linear_model.py` | Extract current `fit_linear_model()` logic here |
| **New file**: `doe/statistics/interaction_model.py` | Implement interaction model: `y ~ x1 + x2 + x1:x2` |
| **New file**: `doe/statistics/quadratic_model.py` | Implement quadratic model: `y ~ x1 + x2 + x1^2 + x2^2` |
| [main.py](file:///c:/Users/marti/Documents/DOE_v1/doe/main.py) L244-259 | `analyze` CLI subcommand must add `--model-type` flag |

### 2.5 Schema Version Bump

| Component | Impact |
|---|---|
| All models | `schema_version` default changes from `"1.0"` to `"1.1"` |
| [workflow_state.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/workflow_state.py) L166-169 | `load_from_json()` version check must accept `"1.1"` (and ideally migrate `"1.0"` states) |

---

## 3. Proposed Implementation Order

The changes have the following dependency graph:

```
Step 1: Domain model changes (Experiment, Design, Analysis, FactorCoding)
  └─> Step 2: Serialization changes (to_dict/from_dict, schema_version)
       └─> Step 3: Workflow state changes (transition rules, validation, version bump)
            ├─> Step 4: Design generators (refactor full_factorial, add fractional_factorial)
            │    └─> Step 5: Factor coding generation
            ├─> Step 6: Statistical models (extract linear, add interaction + quadratic)
            └─> Step 7: CLI updates
                 └─> Step 8: Test updates + new tests
```

### Detailed Steps

---

### Step 1 — Domain Model Changes

#### [MODIFY] [experiment.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/experiment.py)

- Remove `design_type: DesignType` field (L20)
- Remove `planned_runs: Optional[int]` field (L22)
- Remove `design_type` validation in `validate()` (L40-41)
- Remove `planned_runs` validation in `validate()` (L43-45)
- Remove `design_type` and `planned_runs` from `to_dict()` (L75-76)
- Remove `design_type` and `planned_runs` from `from_dict()` (L95-96)
- Remove `InvalidDesignTypeError`, `InvalidPlannedRunsError` imports (L9-10)
- Remove the `DesignType` Literal type alias (L13) — move to a shared location

**Risks:**
- This is the most disruptive change. Every consumer that passes `design_type` to `Experiment()` will break.
- The `DesignType` type alias is currently imported from `experiment.py` by other modules and re-exported in `__init__.py`.

#### [MODIFY] [design.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/design.py)

- Add `DesignType` Literal type alias (moved from experiment.py), extended to include future types
- Add `FactorCoding` dataclass with fields: `factor_ref`, `method`, `mapping`, `metadata`
- Add `FactorCoding.validate()`, `to_dict()`, `from_dict()`
- Add `factor_coding: Optional[List[FactorCoding]]` field to `Design` (after `runs`)
- Add `replications: Optional[int]` field to `Design` (from the spec)
- Update `Design.validate()`: remove the `self.design_type != experiment.design_type` check (L193-196)
- Update `Design.validate()`: validate `factor_coding` entries if present
- Update `Design.to_dict()`: include `factor_coding` and `replications`
- Update `Design.from_dict()`: deserialize `factor_coding` and `replications`

**Risks:**
- `Design.validate()` currently receives an `Experiment` — it can no longer compare `design_type` fields since Experiment no longer has one.
- Run count validation (L198-210) is only for `full_factorial` — must remain but not try to read `experiment.design_type`.

#### [MODIFY] [analysis.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/analysis.py)

- Define `ModelType = Literal["linear", "interaction", "quadratic"]`
- Change `model_type: str` to `model_type: ModelType`
- Add `formula: Optional[str]` field (spec §9.1) — assess overlap with existing `model_formula`
- Add `terms: Optional[List[str]]` field (spec §9.1)
- Add validation for `model_type` against supported values
- Update `to_dict()` and `from_dict()` to include `formula` and `terms`

**Risks:**
- The existing field is `model_formula` while the spec says `formula`. Need to decide: rename `model_formula` → `formula`, or keep both. Keeping `model_formula` as an alias would break spec compliance. **See Open Question §5.1.**

---

### Step 2 — Serialization & Package Exports

#### [MODIFY] [models/\_\_init\_\_.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/__init__.py)

- Update `DesignType` import source (from `experiment` → `design`)
- Add export for `FactorCoding`
- Add export for `ModelType`

#### [MODIFY] All models with `schema_version`

- Update default `schema_version` from `"1.0"` to `"1.1"` across: `Experiment`, `Design`, `Run`, `Block`, `Results`, `Analysis`, `WorkflowState`

**Risks:**
- Existing `"1.0"` JSON files become incompatible unless we add migration support.

---

### Step 3 — Workflow State Changes

#### [MODIFY] [workflow_state.py](file:///c:/Users/marti/Documents/DOE_v1/doe/models/workflow_state.py)

- Update `load_from_json()` to accept schema version `"1.1"` (and optionally `"1.0"` with migration)
- `validate()` for `design_generated` step currently calls `self.experiment.validate()` and `self.design.validate(self.experiment)` — no changes needed since `Experiment.validate()` will no longer check `design_type`.

**Risks:**
- If `"1.0"` states must be loadable, a migration path is needed to strip `design_type`/`planned_runs` from the experiment portion of the JSON.

---

### Step 4 — Design Generators

#### [MODIFY] [experiment_creation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/experiment_creation.py)

- Remove `design_type` parameter from `create_experiment()`
- Remove `design_type` from `Experiment()` constructor call

#### [MODIFY] [design_generation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/design_generation.py)

- Change `generate_design(state)` signature to `generate_design(state, design_type: str)` (or accept a `DesignGenerationOptions` dict)
- Use the explicit `design_type` parameter to look up the generator (instead of `experiment.design_type`)
- Register `"fractional_factorial": FractionalFactorialGenerator` in `_DESIGN_GENERATORS`

#### [MODIFY] [full_factorial.py](file:///c:/Users/marti/Documents/DOE_v1/doe/designs/full_factorial.py)

- Remove the `experiment.design_type != "full_factorial"` check (L132-136) — the dispatcher already ensures the correct generator is called
- Add factor coding generation (two_level coding for continuous factors)

#### [NEW] `doe/designs/fractional_factorial.py`

- Implement `FractionalFactorialGenerator(DesignGenerator)`
- Generate a fractional subset of the full factorial matrix
- Generate factor coding
- Validate the resulting design

**Risks:**
- Fractional factorial design requires selecting a defining relation (e.g., I = ABC for a 2^(3-1) design). The spec does not specify how the resolution or defining relation is chosen. **See Open Question §5.2.**

#### [MODIFY] [generator_interface.py](file:///c:/Users/marti/Documents/DOE_v1/doe/designs/generator_interface.py)

- Potentially update `generate()` signature — currently `generate(self, experiment: Experiment) -> Design`. May need to pass `design_type` explicitly or coding options.

---

### Step 5 — Factor Coding Generation

Integrated into Step 4. The design generators produce `FactorCoding` entries:

- `two_level` coding: maps `[lower_bound, upper_bound]` → `[-1, +1]` for continuous factors
- `center_scale` coding: maps by `(value - center) / half_range`
- Categorical factors: map level values to coded integers

This is done inside each generator's `generate()` method and attached to the resulting `Design`.

---

### Step 6 — Statistical Models

#### [NEW] `doe/statistics/__init__.py`

- Package init with exports

#### [NEW] `doe/statistics/linear_model.py`

- Extract `fit_linear_model()` from [analysis_computation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/analysis_computation.py) (lines 99-290)
- Move the pure-Python matrix math utilities (`_matrix_transpose`, `_matrix_multiply`, `_matrix_inverse`) into a shared utility or keep in this module
- The model builds: `y ~ x1 + x2 + ... + xn` (main effects only)

#### [NEW] `doe/statistics/interaction_model.py`

- Implement interaction model fitting
- Build design matrix with main effects + all pairwise interactions: `y ~ x1 + x2 + x1:x2`
- Reuse the matrix math utilities

#### [NEW] `doe/statistics/quadratic_model.py`

- Implement quadratic model fitting
- Build design matrix with main effects + squared terms: `y ~ x1 + x2 + x1^2 + x2^2`
- Reuse the matrix math utilities

#### [MODIFY] [analysis_computation.py](file:///c:/Users/marti/Documents/DOE_v1/doe/analysis_computation.py)

- Change `analyze_experiment(state)` to `analyze_experiment(state, model_type: str = "linear")`
- Add model dispatcher similar to `_DESIGN_GENERATORS`:
  ```
  _STAT_MODELS = {
      "linear": fit_linear_model,
      "interaction": fit_interaction_model,
      "quadratic": fit_quadratic_model,
  }
  ```
- Validate `model_type` against supported values
- Raise `NonEstimableModelError` if the selected model cannot be estimated from available data

**Risks:**
- Quadratic model requires squared terms, which need at least 3 levels per factor to be estimable. With a 2-level factorial design, `x^2` is constant and the model is non-estimable. The system must detect and report this clearly. **See Open Question §5.3.**

---

### Step 7 — CLI Updates

#### [MODIFY] [main.py](file:///c:/Users/marti/Documents/DOE_v1/doe/main.py)

- **`init-experiment`**: Remove `--design-type` and `--planned-runs` arguments
- **`generate-design`**: Add `--design-type` required argument with choices `["full_factorial", "fractional_factorial"]`
- **`handle_generate_design()`**: Pass `design_type` to `generate_design(state, design_type=args.design_type)`
- **`analyze`**: Add `--model-type` optional argument (default `"linear"`, choices `["linear", "interaction", "quadratic"]`)
- **`handle_analyze()`**: Pass `model_type` to `analyze_experiment(state, model_type=args.model_type)`

---

### Step 8 — Tests

#### [MODIFY] [conftest.py](file:///c:/Users/marti/Documents/DOE_v1/tests/conftest.py)

- Remove `design_type="full_factorial"` from `sample_experiment` fixture
- All other fixtures that depend on `design_type` in the experiment

#### [MODIFY] Existing test files (bulk update)

All files that construct `Experiment(... design_type=...)` must be updated:

| Test File | Key Changes |
|---|---|
| `test_experiment.py` | Remove `design_type` from valid experiments; remove tests for `InvalidDesignTypeError` on Experiment |
| `test_experiment_creation.py` | Remove `design_type` parameter |
| `test_design.py` | Remove `design_type` match checks against experiment |
| `test_design_generation.py` | Pass `design_type` to `generate_design()` |
| `test_full_factorial.py` | Remove `experiment.design_type` checks |
| `test_analysis_computation.py` | Test with model_type parameter |
| `test_analyze_workflow.py` | Test with model_type parameter |
| `test_e2e_full_workflow.py` | Update both lifecycle tests end-to-end |
| `test_cli*.py` | Update CLI invocation arguments |
| `test_persistence.py` | Update schema_version expectations |
| `test_workflow_state.py` | Update fixtures, serialization tests |
| `test_report_generation.py` | Update to read design_type from design |

#### [NEW] Test files

| New Test File | Tests |
|---|---|
| `test_factor_coding.py` | FactorCoding validation, serialization, two_level/center_scale methods |
| `test_fractional_factorial.py` | FractionalFactorialGenerator, run count, factor coding |
| `test_interaction_model.py` | Interaction model fitting, term generation, estimability |
| `test_quadratic_model.py` | Quadratic model fitting, term generation, estimability |
| `test_model_selection.py` | Dispatching to correct model, unknown model_type errors |
| `test_e2e_extension.py` | Full lifecycle with new features (fractional factorial + interaction/quadratic models) |

---

## 4. Per-Step Risk Summary

| Step | Risk Level | Key Risks |
|---|---|---|
| 1. Domain models | 🔴 **High** | Cross-cutting breakage; `DesignType` relocation; every test that builds an Experiment breaks |
| 2. Serialization | 🟡 Medium | Schema version compatibility; existing JSON files become invalid |
| 3. Workflow state | 🟡 Medium | Migration of v1.0 states; version check in `load_from_json` |
| 4. Design generators | 🟡 Medium | Fractional factorial algorithm decisions; generator interface change |
| 5. Factor coding | 🟢 Low | Additive change; no existing behavior broken |
| 6. Statistical models | 🟡 Medium | Model estimability checks; matrix math for interaction/quadratic terms |
| 7. CLI updates | 🟢 Low | Straightforward argument changes |
| 8. Tests | 🔴 **High** | Largest volume of changes; every fixture and E2E test needs updating |

---

## 5. Open Questions & Ambiguities

> [!IMPORTANT]
> The following items require confirmation before implementation proceeds.

### 5.1 `model_formula` vs `formula`

The current Analysis model has a field named `model_formula`. The extension spec (§9.1) introduces `formula: str | null` and `terms: list[str] | null`.

**Options:**
- **A)** Rename existing `model_formula` → `formula` to match the spec.
- **B)** Keep `model_formula` and add `formula` as a second field.
- **C)** Treat `model_formula` as already satisfying the spec's `formula` intent, and just add `terms`.

> **Recommendation:** Option A — rename to `formula` for spec compliance, since no external consumers exist yet.

### 5.2 Fractional Factorial: Resolution and Defining Relation

The spec lists `fractional_factorial` as a supported design type but does not specify:
- How the **resolution** is selected (Resolution III, IV, V?).
- Whether the **defining relation** is automatic or user-supplied.
- What the **minimum runs** formula is (e.g., `2^(k-p)` for what `p`?).

**Options:**
- **A)** Default to Resolution III (minimum runs), with user override via options.
- **B)** Default to highest resolution possible.
- **C)** Require the user to specify the number of runs, and derive the fraction automatically.

> **Recommendation:** Clarify intended behavior before implementing.

### 5.3 Quadratic Model Estimability with 2-Level Designs

A quadratic model (`x^2` terms) requires at least 3 levels per factor. A full or fractional factorial design with only 2 levels makes `x^2` a constant column, causing `NonEstimableModelError`.

**Question:** Should the system:
- **A)** Simply raise `NonEstimableModelError` and leave it to the user to choose a compatible design?
- **B)** Warn the user at `generate_design()` time that the design won't support quadratic analysis?
- **C)** Prevent the combination entirely with a cross-validation check?

> **Recommendation:** Option A for the MVP (fail clearly at analysis time), with a possible warning in future extensions.

### 5.4 Schema Version Migration Strategy

**Question:** Must v1.0 JSON workflow states be loadable after this extension is implemented?
- **A)** Yes — implement an automatic migration (strip `design_type`/`planned_runs` from experiment, bump version).
- **B)** No — require users to re-create experiments. Reject v1.0 states.

> **Recommendation:** Implement basic migration (Option A) as specified in the original spec §8.2: "version migrations must be explicit."

### 5.5 `replications` Field on Design

The extension spec (§5.2) lists `replications: int | null` as a Design field. The current `Design` model **does not** have this field, though it was mentioned in the original spec (§3.6).

**Question:** Should `replications` be added as part of this extension, or deferred?

> **Recommendation:** Add it now as an optional field to match both specs, even if no generator uses it yet.

### 5.6 Interaction Model: Full vs Subset Interactions

The spec shows `y ~ x1 + x2 + x1:x2` (all pairwise interactions).

**Question:** For experiments with 3+ factors, should the interaction model include:
- **A)** Only 2-way interactions (e.g., `x1:x2 + x1:x3 + x2:x3`)?
- **B)** All possible interactions (including 3-way, 4-way, etc.)?

> **Recommendation:** Option A (2-way only) for the MVP, matching standard DOE practice.

---

## Verification Plan

### Automated Tests

```bash
# Run the full test suite after each step
python -m pytest tests/ -v --tb=short

# Run only new tests
python -m pytest tests/test_factor_coding.py tests/test_fractional_factorial.py tests/test_interaction_model.py tests/test_quadratic_model.py tests/test_model_selection.py -v

# Run E2E tests
python -m pytest tests/test_e2e_full_workflow.py tests/test_e2e_extension.py -v
```

### Manual Verification

- Verify CLI `--help` output reflects new argument structure
- Verify that a full lifecycle (init → design → results → analyze → report) works via CLI with the new argument placement
- Verify that existing v1.0 JSON files are either migrated or rejected with a clear error message

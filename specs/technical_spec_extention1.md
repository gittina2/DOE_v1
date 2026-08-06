Technical Specification Extension
Version: 1.1

# DOE Python Core Technical Specification Extension v1.1

## 1. Purpose

This document extends the original DOE Python Core Technical Specification.

The original technical specification remains the baseline reference for the project architecture and implementation principles.

This extension introduces the architectural changes required to support:

- separation between experiment definition and design generation;
- multiple DOE design generators;
- factor coding for statistical analysis;
- user-selectable statistical models;
- multiple statistical model implementations.

Unless explicitly overridden by this document, all requirements defined in the original technical specification remain valid.

---

# 2. Architectural rationale

The original MVP specification defined the experiment and the design generation strategy together.

This extension separates these concepts.

An Experiment represents the scientific definition of the study:

- which factors are investigated;
- which responses are measured;
- metadata describing the study.

A Design represents the generated experimental plan:

- which experimental runs are performed;
- which DOE strategy is used;
- how factor values are represented.

Similarly, statistical model selection is moved from a fixed implementation detail to an explicit analysis-time decision.

The workflow becomes:
experiment definition
|
v
design generation
|
v
results collection
|
v
statistical analysis
|
v
reporting

The extension preserves the original architectural principles:

- domain-first architecture;
- separation of concerns;
- algorithm independence;
- JSON workflow persistence;
- explicit validation.

---

# 3. Experiment model changes

## 3.1 Responsibility

The Experiment model represents only the scientific definition of the study.

Experiment MUST NOT contain:

- generated runs;
- design generation strategy;
- statistical model selection.

The Experiment model defines what should be studied, not how the study should be executed.

---

## 3.2 Fields

The Experiment model contains:

- schema_version: str
- experiment_id: str
- name: str
- description: str | null
- factors: list[Factor]
- responses: list[Response]
- metadata: dict[str, Any] | null

---

## 3.3 Removed fields

The following fields are removed from Experiment:

- design_type
- planned_runs


Design-related decisions are postponed until the design generation step.

---

# 4. Design generation

## 4.1 Responsibility

Design generation transforms a valid Experiment into an executable experimental plan.

The user selects the design type during design generation.

Workflow:

experiment
|
v
generate_design(design_ type=)
|
v
design


---

# 5. Design model extensions

## 5.1 Design responsibility

The Design model represents the experimental plan generated from an Experiment.

It contains:

- generated runs;
- DOE design type;
- factor coding;
- execution information.

---

## 5.2 Fields

The Design model contains:

- schema_version: str
- design_id: str
- design_type: DesignType
- experiment_ref: str
- runs: list[Run]
- factor_coding: list[FactorCoding] | null
- randomization: bool
- order: list[str] | null
- blocks: list[Block] | null
- replications: int | null
- metadata: dict[str, Any] | null

---

# 6. Design types

## 6.1 Supported design types

The extension introduces support for multiple design generators.

Supported MVP design types:

- full_factorial
- fractional_factorial

Future extensions may include:

- central_composite_design
- box_behnken_design
- optimal_designs

---

## 6.2 Design generator responsibility

Each design generator MUST:

- receive a valid Experiment;
- generate a valid Design;
- validate generated runs;
- preserve references to the original Experiment.

Design generators MUST remain separated from domain models.

---

# 7. Factor coding

## 7.1 Purpose

DOE statistical models commonly operate on coded factor values.

The original experimental values must always be preserved.

Coding is an additional representation stored in the Design because it depends on how the experimental plan is generated.

Example:

Temperature:
- 20 °C -> -1
- 60 °C -> +1

---

## 7.2 FactorCoding model

FactorCoding represents the transformation between experimental values and coded DOE levels.

Fields:

- factor_ref: str
- method: str
- mapping: dict[str, float]
- metadata: dict[str, Any] | null

---

## 7.3 Supported coding methods

MVP supported methods:

- two_level
- center_scale

---

## 7.4 Invariants

FactorCoding MUST satisfy:

- factor_ref references an existing factor;
- coded values are numeric;
- two_level coding uses -1 and +1 levels.

---

# 8. Statistical models

## 8.1 Responsibility

Statistical model selection occurs during analysis.

The same Design and Results can be analyzed using different statistical models.

Example:

Design + Results
    |

    +---- Analysis (linear)

    |

    +---- Analysis (interaction)

    |

    +---- Analysis (quadratic)


The MVP workflow stores the latest generated Analysis object.

Support for storing multiple analyses simultaneously may be introduced in a future extension.

---

# 9. Analysis model changes

## 9.1 New fields

Analysis is extended with:

- model_type: ModelType
- formula: str | null
- terms: list[str] | null

The complete Analysis model becomes:
- schema_version: str
- analysis_id: str
- model_type: ModelType
- experiment_ref: str
- design_ref: str
- results_ref: str
- formula: str | null
- terms: list[str] | null
- coefficients: dict[str, float] | null
- anova_table: list[dict[str, Any]] | null
- p_values: dict[str, float] | null
- r_squared: float | null
- adjusted_r_squared: float | null
- residuals: list[float] | null
- diagnostics: dict[str, Any] | null
- metadata: dict[str, Any] | null

---

# 10. Supported statistical models

## 10.1 Model types

The extension introduces:
- linear
- interaction
- quadratic

---

## 10.2 Example formulas

Linear:
y ~ x1 + x2

Interaction:
y ~ x1 + x2 + x1:x2

Quadratic:
y ~ x1 + x2 + x1^2 + x2^2

---

# 11. Workflow changes

The workflow remains:

empty
    |
    v
experiment_created
    |
    v
design_generated
    |
    v
results_in_progress
    |
    v
result_complet
    |
    v
analysis_created
    |
    v
report_generated


The difference is when user decisions occur.

| Step | User decision |
|---|---|
| create_experiment | define factors and responses |
| generate_design | choose DOE design type |
| insert_results | provide experimental measurements |
| analyze_experiment | choose statistical model |
| generate_report | export results |

---

# 12. Function changes

## 12.1 generate_design()

The function is extended with a design selection input.

Input:
-   WorkflowState
- DesignGenerationOptions:
    - design_type

Example:
{
    "design_type": "fractional_factorial"
}

The function MUST:

- validate the selected design type;
- invoke the correct generator;
- generate valid runs;
- generate factor coding when required;
- return a valid Design object.

---

## 12.2 analyze_experiment()

The function is extended with model selection.

Input:
- WorkflowState
- AnalysisOptions:
    - model_type

Example:
{
    "model_type": "linear"
}

The function MUST:

- validate the selected model type;
- generate model terms;
- estimate model parameters;
- store formula and terms in Analysis.

If the selected model cannot be estimated from available data:
NonEstimableModelError must be raised.

---

# 13. File structure extensions

The project structure is extended with:
doe/
designs/
    fractional_factorial.py
statistics/
    linear_model.py
    interaction_model.py
    quadratic_model.py


Statistics implementations and DOE generators remain independent from domain models.

---

# 14. Compatibility

This extension preserves the original architecture.

The following concepts remain unchanged:

- Experiment;
- Design;
- Results;
- Analysis;
- WorkflowState;
- JSON persistence.

The extension modifies responsibilities but does not invalidate the original domain model.

Schema versions must be incremented and migrations must remain explicit.

---

# 15. Future extensions

Possible future improvements:

- multiple Analysis objects stored in the same workflow;
- ModelSpecification domain object;
- automatic model selection;
- design-model compatibility validation;
- response surface methodology;
- optimal experimental designs;
- richer CLI configuration.
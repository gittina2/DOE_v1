Technical Specification
Version: 1.0

1. Purpose and principles
1.1 Purpose
This document defines the technical specification for the Python core of the open-source DOE (Design of Experiments) project. The MVP goal is to provide a command-line engine to create experiments, generate designs, enter results, compute statistical analyses, and produce reports, while keeping the system modular, extensible, and maintainable.

1.2 Principles
Separation of concerns: each module has a single responsibility.

Design by Contract: every model and every function exposes preconditions, postconditions, and invariants.

Domain-first architecture: models represent real scientific domain concepts.

Algorithm independence: DOE algorithms are separated from models and orchestration.

Workflow state persistence: each step produces a JSON-serializable state that is passed to the next step.

Compatibility safety: schema versioning and explicit validation are used to reduce compatibility issues.

2. Architectural decisions
2.1 Domain models
Domain models are lightweight Python objects, preferably implemented as dataclasses. Each model may include local validation and serialization methods, but must not contain DOE algorithms or workflow orchestration.

Every persisted domain object has a system-generated unique identifier.
\*\_ref fields are strings that must resolve to existing \*\_id values of the corresponding entity type.
User-provided name values are descriptive only and must not be used as authoritative references.

2.2 Validation
Validation is performed through validate() methods on models and through explicit checks inside orchestration functions. Contract violations must raise domain-specific exceptions.

2.3 Persistence
The MVP uses JSON as the persistence format and as the state handoff mechanism between steps. The main workflow state is represented by a serializable WorkflowState. No database is planned for the MVP.

2.4 Reporting
The initial report format is Markdown. Other formats may be added later.

2.5 Dependencies
The MVP should remain lightweight. Preference should be given to the standard library and only minimal external dependencies if truly necessary.

2.6 Input formats
The system MUST use JSON as the workflow state format.

The system MAY accept CSV files as input sources for factor definitions and result entries in the CLI MVP.

CSV parsing is outside the domain model and must be implemented in dedicated import modules.

CSV rows are parsed into raw field values and then mapped to domain objects (Factor for experiment setup, ResultEntry for result import), which are validated by the domain layer.

Invalid CSV rows must produce row-level import errors, including the row number, field name, and invalid value.

CSV is not a persistence format for the domain. The workflow state continues to use JSON as the source of truth.

3. Models
3.1 Common conventions
Every domain model must support:

schema\_version: str.

validate() -> None.

to\_dict() -> dict.

from\_dict(data: dict) -> Model.

Serialization must use JSON-compatible types only. Validation must raise domain exceptions, not simple booleans.

3.2 Factor
Represents an experimental factor.

Fields:

name: str

type: FactorType

unit: str | null

levels: list\[Any] | null

lower\_bound: float | null

upper\_bound: float | null

metadata: dict\[str, Any] | null

Supported types:

continuous

categorical

Invariants:

name is required and non-empty.

type is required and supported.

if type = continuous, then lower\_bound and upper\_bound are required and lower\_bound < upper\_bound.

if type = categorical, then levels is required and contains at least 2 distinct values.

a factor cannot be both continuous and categorical.

3.3 Response
Represents an output variable.

Fields:

name: str

type: ResponseType

unit: str | null

metadata: dict\[str, Any] | null

Supported types for the MVP:

continuous

Invariants:

name is required and non-empty.

type is required and supported.

unit, if present, is non-empty.

3.4 Experiment
Represents the study definition.

Fields:

schema\_version: str

experiment\_id: str

name: str

description: str | null

factors: list\[Factor]

responses: list\[Response]

design\_type: DesignType

planned\_runs: int | null

metadata: dict\[str, Any] | null

Supported design types in the MVP:

full\_factorial

fractional\_factorial

Invariants:

experiment\_id is required and unique.

experiment\_id is a system-generated unique identifier.

at least one factor.

at least one response.

factor names are unique.

response names are unique.

every factor and response is individually valid.

design\_type is supported.

planned\_runs, if present, is a positive integer.

planned\_runs cannot be lower than the minimum number of runs required by the design\_type, if such a minimum is defined.

it does not contain runs, results, or analysis.

3.5 Run
Represents a single execution of the design.

Fields:

run\_id: str

factor\_values: dict\[str, Any]

metadata: dict\[str, Any] | null

Invariants:

run\_id is required and unique within the design.

run\_id is a system-generated unique identifier within the design.

factor\_values contains all required factors.

values are compatible with the factor constraints.

3.6 Design
Represents the experimental plan generated from the experiment.

Fields:

schema\_version: str

design\_id: str

design\_type: DesignType

experiment\_ref: str

runs: list\[Run]

randomization: bool

order: list\[str] | null

blocks: list\[Block] | null

replications: int | null

metadata: dict\[str, Any] | null

Invariants:

at least one run.

every run has an ID.

run IDs are unique.

every run contains all factors required by the experiment.

design\_type is consistent with the referenced experiment.

the number of runs is consistent with the design type.

randomization is not required for validity.

order, if present, must be a permutation of the run\_id values in runs.

order is generated automatically when randomization is enabled.

blocks, if present, partition the runs into groups associated with external experimental conditions.

replications, if present, indicates how many times the design is repeated.

it does not contain results or analysis.

experiment\_ref references an existing Experiment.experiment\_id.

3.6.1 Block
Represents a group of runs executed under the same external condition.

Fields:

block\_id: str

run\_ids: list\[str]

metadata: dict\[str, Any] | null

Invariants:

block\_id is required and unique within the design.

run\_ids contains valid Run.run\_id values from the same Design.

each run\_id appears in at most one block.

blocks are optional in the MVP.

3.7 ResultEntry
Represents the result of a run.

Fields:

run\_ref: str

values: dict\[str, Any]

status: ResultStatus

metadata: dict\[str, Any] | null

Supported statuses:

partial

complete

Invariants:

run\_ref refers to an existing Run.run\_id.

values is consistent with the defined responses.

status = complete only if all required responses are present.

3.8 Results
Contains the set of observed results.

Fields:

schema\_version: str

results\_id: str

design\_ref: str

entries: list\[ResultEntry]

completeness: ResultStatus

metadata: dict\[str, Any] | null

Invariants:

design\_ref references an existing Design.design\_id

every entry refers to a run in the design.

completeness reflects the actual state of the results.

partial results are allowed.

3.9 Analysis
Contains the statistical analysis output.

Fields:

schema\_version: str

analysis\_id: str

model\_type: str

experiment\_ref: str

design\_ref: str

results\_ref: str

coefficients: dict\[str, float] | null

anova\_table: list\[dict\[str, Any]] | null

p\_values: dict\[str, float] | null

r\_squared: float | null

adjusted\_r\_squared: float | null

residuals: list\[float] | null

diagnostics: dict\[str, Any] | null

metadata: dict\[str, Any] | null

Invariants:

references to experiment, design, and results are consistent.

experiment\_ref references an existing Experiment.experiment\_id.

design\_ref references an existing Design.design\_id.

results\_ref references an existing Results.results\_id.

r\_squared and adjusted\_r\_squared, if present, are between 0 and 1.

analysis is produced only if the model is estimable.

For the MVP, the statistical model is fixed to a linear model.

Model selection may be exposed as a CLI parameter in a future iteration.

3.10 WorkflowState
Represents the persistent CLI workflow state.

Fields:

schema\_version: str

step: WorkflowStep

experiment: Experiment | null

design: Design | null

results: Results | null

analysis: Analysis | null

audit: dict\[str, Any]

Supported steps:

empty

experiment\_created

design\_generated

results\_in\_progress

results\_complete

analysis\_created

report\_generated

Invariants:

the step must be consistent with the present objects/entities.

transitions are monotonic and controlled.

the workflow is always JSON-serializable.

4. Functions
4.1 create\_experiment()
Responsibility: create and validate an Experiment.

Input:

structured payload with name, description, factors, responses, design\_type.

Preconditions:

at least one factor.

at least one response.

all elements are consistent with their respective models.

Output:

WorkflowState updated with experiment.

Postconditions:

step = experiment\_created.

no design, results, or analysis are present.

Errors:

missing data.

invalid factors or responses.

unsupported design type.

4.2 generate\_design()
Responsibility: generate the Design from the Experiment.

Input:

WorkflowState with a valid experiment.

Preconditions:

experiment is present and valid.

design\_type is supported.

Output:

WorkflowState updated with design.

Postconditions:

step = design\_generated.

runs are present and validated.

Errors:

missing experiment.

incompatible design.

invalid matrix.

4.3 insert\_results()
Responsibility: attach measurements to runs.

Input:

WorkflowState with a valid design.

run\_id.

response values.

Preconditions:

design is present and valid.

run exists.

values are compatible with the responses.

Output:

WorkflowState updated with results.

Postconditions:

step = results\_in\_progress or results\_complete.

completeness is consistent with inserted data.

Errors:

unknown run.

inconsistent values.

duplicate or inconsistent results.

4.4 analyze\_experiment()
Responsibility: compute the statistical analysis.

Input:

WorkflowState with experiment, design, and results.

Preconditions:

all required blocks are present and valid.

sufficient observations exist.

the model is estimable.

Output:

WorkflowState updated with analysis.

Postconditions:

step = analysis\_created.

metrics and diagnostics are produced when possible.

Errors:

insufficient data.

non-estimable model.

referential inconsistencies.

4.5 generate\_report()
Responsibility: produce a readable report.

Input:

WorkflowState.

requested output format.

Preconditions:

at least experiment is available.

any required sections are present.

Output:

text, Markdown, or JSON report.

Postconditions:

optional step = report\_generated if export tracking is desired.

Errors:

missing data.

unsupported format.

5. Workflow state
Expected transitions:

empty -> experiment\_created

experiment\_created -> design\_generated

design\_generated -> results\_in\_progress

results\_in\_progress -> results\_complete

results\_complete -> analysis\_created

analysis\_created -> report\_generated

Rules:

every transition must be explicit.

there is no backward movement without a migration.

the JSON state is the source of truth between steps.

6. Errors
6.1 Domain validation errors
InvalidFactorTypeError

InvalidFactorBoundsError

MissingFactorLevelsError

DuplicateFactorNameError

DuplicateFactorLevelsError

MissingResponseError

InvalidResponseTypeError

InvalidDesignTypeError

InvalidPlannedRunsError

6.2 Workflow errors
InvalidWorkflowTransitionError

WorkflowStateMismatchError

SchemaVersionMismatchError

InconsistentReferenceError

6.3 Design and results errors
UnsupportedDesignTypeError

RunCountMismatchError

IncompatibleFactorDefinitionError

InvalidDesignMatrixError

DuplicateRunIdError

UnknownRunIdError

InvalidResponseValueError

PartialResultInconsistentError

DuplicateResultForRunError

6.4 Analysis errors
InsufficientObservationsError

NonEstimableModelError

InvalidAnalysisInputError

6.5 CSV import errors

CsvImportError

CsvHeaderError

CsvFieldMappingError

CsvFormatError

CsvRowImportError

7. File structure
Initial proposal:

doe/

doe/main.py

doe/experiment\_creation.py

doe/design\_generation.py

doe/result\_input.py

doe/analysis\_computation.py

doe/report\_generation.py

doe/models/

doe/models/factor.py

doe/models/response.py

doe/models/experiment.py

doe/models/design.py

doe/models/results.py

doe/models/analysis.py

doe/models/workflow\_state.py

doe/designs/

doe/designs/full\_factorial.py

doe/designs/fractional\_factorial.py

tests/

Module responsibilities:

models/: data definitions, local validation, serialization.

designs/: specific generator implementations.

\*\_creation.py and \*\_generation.py: workflow orchestration and validation.

tests/: unit tests, contract tests, end-to-end tests.

Nested domain types such as Run, Block, and ResultEntry are implemented inside the module of their parent aggregate (Design or Results) rather than as standalone top-level files.

8. Persistence
8.1 MVP strategy
The base format is JSON. Each step saves a versioned WorkflowState and passes it to the next step. JSON is the source of truth for the workflow state.

8.2 Requirements
files must be round-trippable.

the format must include schema\_version.

version migrations must be explicit.

JSON must contain data only, not behavior.

The system is responsible for generating unique internal identifiers for domain entities and for maintaining referential links between them.

User-provided names are descriptive only and must not be used as authoritative references.

All \*\_ref fields are strings that must resolve to existing system-generated \*\_id values of the corresponding entity type.

8.3 Recommended conventions
a main session file, e.g. workflow\_state.json.

separate exports for experiment, design, results, and analysis only if needed.

SQLite may be introduced later without changing the domain model.

9. Test and quality
9.1 Test types
Unit tests for models.

Contract tests for functions and invariants.

Serialization tests for JSON round-trip.

End-to-end workflow tests.

Regression tests for schema-version compatibility.

9.2 Quality criteria
every model must be validatable in isolation.

every function must respect its contracts.

every workflow transition must be tested.

DOE generators must be interchangeable behind a stable interface.

9.3 MVP priorities
Experiment validation.

Design generation for full factorial.

partial and complete result insertion.

basic analysis.

simple text-based report generation.

10. Consolidated decisions
The consolidated MVP decisions are:

domain models as lightweight dataclasses;

local validation in models and workflow validation in functions;

JSON as the main workflow state;

Markdown as the initial report format;

no database in the MVP;

DOE algorithms separated from models and orchestrators.

11. Open decisions
Only implementation details remain, such as:

exact validation library, if a future external dependency is introduced;

exact Markdown report formatting;

JSON migration strategy as the schema evolves;

possible richer CLI support beyond the base workflow.

The project may be extended through versioned technical specification extensions.
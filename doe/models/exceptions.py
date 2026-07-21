class DoeError(Exception):
    """Base exception for all DOE engine errors."""
    pass


# 6.1 Domain validation errors
class DomainValidationError(DoeError):
    """Base for all domain model validation errors."""
    pass


class InvalidFactorTypeError(DomainValidationError):
    """Raised when a factor type is not supported."""
    pass


class InvalidFactorBoundsError(DomainValidationError):
    """Raised when continuous factor bounds are missing, invalid, or inverted."""
    pass


class MissingFactorLevelsError(DomainValidationError):
    """Raised when a categorical factor is missing levels."""
    pass


class DuplicateFactorNameError(DomainValidationError):
    """Raised when there are multiple factors with the same name in an experiment."""
    pass


class DuplicateFactorLevelsError(DomainValidationError):
    """Raised when categorical factor levels contain duplicates or insufficient distinct values."""
    pass


class MissingResponseError(DomainValidationError):
    """Raised when responses are missing or response name is empty."""
    pass


class InvalidResponseTypeError(DomainValidationError):
    """Raised when a response type is not supported."""
    pass


class InvalidDesignTypeError(DomainValidationError):
    """Raised when the specified design type is not supported."""
    pass


class InvalidPlannedRunsError(DomainValidationError):
    """Raised when planned runs is invalid."""
    pass


# 6.2 Workflow errors
class WorkflowError(DoeError):
    """Base for all workflow-related errors."""
    pass


class InvalidWorkflowTransitionError(WorkflowError):
    """Raised when an invalid state transition is attempted."""
    pass


class WorkflowStateMismatchError(WorkflowError):
    """Raised when the workflow state is inconsistent with loaded entities."""
    pass


class SchemaVersionMismatchError(WorkflowError):
    """Raised when there is a mismatch in version schemas."""
    pass


class InconsistentReferenceError(WorkflowError):
    """Raised when references between entities are inconsistent."""
    pass


# 6.3 Design and results errors
class DesignResultError(DoeError):
    """Base for all design matrix and results-related errors."""
    pass


class UnsupportedDesignTypeError(DesignResultError):
    """Raised when the design type is unsupported for the given configuration."""
    pass


class RunCountMismatchError(DesignResultError):
    """Raised when the actual number of runs deviates from planned runs."""
    pass


class IncompatibleFactorDefinitionError(DesignResultError):
    """Raised when factors in a design do not match the experiment definition."""
    pass


class InvalidDesignMatrixError(DesignResultError):
    """Raised when the generated design matrix is invalid."""
    pass


class DuplicateRunIdError(DesignResultError):
    """Raised when duplicate run IDs are detected."""
    pass


class UnknownRunIdError(DesignResultError):
    """Raised when a run reference points to a non-existent run ID."""
    pass


class InvalidResponseValueError(DesignResultError):
    """Raised when a response value is invalid or incompatible."""
    pass


class PartialResultInconsistentError(DesignResultError):
    """Raised when partial results are inconsistent with design constraints."""
    pass


class DuplicateResultForRunError(DesignResultError):
    """Raised when multiple results are provided for a single run."""
    pass


# 6.4 Analysis errors
class AnalysisError(DoeError):
    """Base for all analysis-related errors."""
    pass


class InsufficientObservationsError(AnalysisError):
    """Raised when there are not enough data points to compute the analysis."""
    pass


class NonEstimableModelError(AnalysisError):
    """Raised when the design matrix is rank-deficient and coefficients cannot be estimated."""
    pass


class InvalidAnalysisInputError(AnalysisError):
    """Raised when inputs for analysis are malformed or invalid."""
    pass


# 6.5 CSV import errors
class CsvImportError(DoeError):
    """Base exception for CSV import errors."""
    pass


class CsvHeaderError(CsvImportError):
    """Raised when the CSV header is missing or invalid."""
    pass


class CsvFieldMappingError(CsvImportError):
    """Raised when CSV fields cannot be mapped to model properties."""
    pass


class CsvFormatError(CsvImportError):
    """Raised when the CSV formatting is invalid."""
    pass


class CsvRowImportError(CsvImportError):
    """Raised when a specific CSV row fails to import.

    Attributes:
        row_number: The line number in the CSV.
        field_name: The column name with the error.
        invalid_value: The value that caused the validation failure.
    """
    def __init__(self, row_number: int, field_name: str, invalid_value: str, message: str = ""):
        self.row_number = row_number
        self.field_name = field_name
        self.invalid_value = invalid_value
        super().__init__(
            message or f"Row {row_number}, Field '{field_name}' invalid value: '{invalid_value}'"
        )

import pytest
from doe.models import (
    DoeError,
    DomainValidationError,
    InvalidFactorTypeError,
    InvalidFactorBoundsError,
    MissingFactorLevelsError,
    DuplicateFactorNameError,
    DuplicateFactorLevelsError,
    MissingResponseError,
    InvalidResponseTypeError,
    InvalidDesignTypeError,
    InvalidPlannedRunsError,
    WorkflowError,
    InvalidWorkflowTransitionError,
    WorkflowStateMismatchError,
    SchemaVersionMismatchError,
    InconsistentReferenceError,
    DesignResultError,
    UnsupportedDesignTypeError,
    RunCountMismatchError,
    IncompatibleFactorDefinitionError,
    InvalidDesignMatrixError,
    DuplicateRunIdError,
    UnknownRunIdError,
    InvalidResponseValueError,
    PartialResultInconsistentError,
    DuplicateResultForRunError,
    AnalysisError,
    InsufficientObservationsError,
    NonEstimableModelError,
    InvalidAnalysisInputError,
    CsvImportError,
    CsvHeaderError,
    CsvFieldMappingError,
    CsvFormatError,
    CsvRowImportError,
)

def test_exceptions_inheritance():
    # Domain validation exceptions
    assert issubclass(DomainValidationError, DoeError)
    assert issubclass(InvalidFactorTypeError, DomainValidationError)
    assert issubclass(InvalidFactorBoundsError, DomainValidationError)
    assert issubclass(MissingFactorLevelsError, DomainValidationError)
    assert issubclass(DuplicateFactorNameError, DomainValidationError)
    assert issubclass(DuplicateFactorLevelsError, DomainValidationError)
    assert issubclass(MissingResponseError, DomainValidationError)
    assert issubclass(InvalidResponseTypeError, DomainValidationError)
    assert issubclass(InvalidDesignTypeError, DomainValidationError)
    assert issubclass(InvalidPlannedRunsError, DomainValidationError)

    # Workflow exceptions
    assert issubclass(WorkflowError, DoeError)
    assert issubclass(InvalidWorkflowTransitionError, WorkflowError)
    assert issubclass(WorkflowStateMismatchError, WorkflowError)
    assert issubclass(SchemaVersionMismatchError, WorkflowError)
    assert issubclass(InconsistentReferenceError, WorkflowError)

    # Design and result exceptions
    assert issubclass(DesignResultError, DoeError)
    assert issubclass(UnsupportedDesignTypeError, DesignResultError)
    assert issubclass(RunCountMismatchError, DesignResultError)
    assert issubclass(IncompatibleFactorDefinitionError, DesignResultError)
    assert issubclass(InvalidDesignMatrixError, DesignResultError)
    assert issubclass(DuplicateRunIdError, DesignResultError)
    assert issubclass(UnknownRunIdError, DesignResultError)
    assert issubclass(InvalidResponseValueError, DesignResultError)
    assert issubclass(PartialResultInconsistentError, DesignResultError)
    assert issubclass(DuplicateResultForRunError, DesignResultError)

    # Analysis exceptions
    assert issubclass(AnalysisError, DoeError)
    assert issubclass(InsufficientObservationsError, AnalysisError)
    assert issubclass(NonEstimableModelError, AnalysisError)
    assert issubclass(InvalidAnalysisInputError, AnalysisError)

    # CSV import exceptions
    assert issubclass(CsvImportError, DoeError)
    assert issubclass(CsvHeaderError, CsvImportError)
    assert issubclass(CsvFieldMappingError, CsvImportError)
    assert issubclass(CsvFormatError, CsvImportError)
    assert issubclass(CsvRowImportError, CsvImportError)

def test_csv_row_import_error_properties():
    err = CsvRowImportError(row_number=5, field_name="bounds", invalid_value="abc")
    assert err.row_number == 5
    assert err.field_name == "bounds"
    assert err.invalid_value == "abc"
    assert "Row 5" in str(err)
    assert "bounds" in str(err)
    assert "abc" in str(err)

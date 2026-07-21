import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from doe.models.exceptions import (
    DomainValidationError,
    DuplicateResultForRunError,
    InvalidResponseValueError,
)


@dataclass
class ResultEntry:
    run_ref: str
    values: Dict[str, Any]
    status: str = "complete"
    metadata: Optional[Dict[str, Any]] = None

    def validate(self) -> None:
        if not isinstance(self.run_ref, str) or not self.run_ref.strip():
            raise DomainValidationError("run_ref must be a non-empty string.")

        if not isinstance(self.values, dict) or len(self.values) == 0:
            raise InvalidResponseValueError("values must be a non-empty dictionary.")

        if self.status not in ("partial", "complete"):
            raise DomainValidationError(
                f"Invalid result status: {self.status}. Allowed values are 'partial' or 'complete'."
            )

        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise DomainValidationError("metadata must be a dictionary or None.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_ref": self.run_ref,
            "values": self.values,
            "status": self.status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResultEntry":
        if not isinstance(data, dict):
            raise DomainValidationError("ResultEntry data must be a dictionary.")

        return cls(
            run_ref=data.get("run_ref", ""),
            values=data.get("values", {}),
            status=data.get("status", "complete"),
            metadata=data.get("metadata"),
        )


@dataclass
class Results:
    design_ref: str
    entries: List[ResultEntry] = field(default_factory=list)
    completeness: str = "complete"
    results_id: str = field(default_factory=lambda: f"res_{uuid.uuid4().hex[:8]}")
    schema_version: str = "1.0"
    metadata: Optional[Dict[str, Any]] = None

    def validate(self) -> None:
        if not isinstance(self.results_id, str) or not self.results_id.strip():
            raise DomainValidationError("results_id must be a non-empty string.")

        if not isinstance(self.design_ref, str) or not self.design_ref.strip():
            raise DomainValidationError("design_ref must be a non-empty string.")

        if self.completeness not in ("partial", "complete"):
            raise DomainValidationError(
                f"Invalid completeness: {self.completeness}. Allowed values are 'partial' or 'complete'."
            )

        if not isinstance(self.entries, list):
            raise DomainValidationError("entries must be a list of ResultEntry objects.")

        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise DomainValidationError("metadata must be a dictionary or None.")

        seen_runs = set()
        for entry in self.entries:
            if not isinstance(entry, ResultEntry):
                raise DomainValidationError("All entries in Results must be ResultEntry instances.")
            entry.validate()
            if entry.run_ref in seen_runs:
                raise DuplicateResultForRunError(
                    f"Duplicate result entry detected for run '{entry.run_ref}'."
                )
            seen_runs.add(entry.run_ref)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "results_id": self.results_id,
            "design_ref": self.design_ref,
            "entries": [e.to_dict() for e in self.entries],
            "completeness": self.completeness,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Results":
        if not isinstance(data, dict):
            raise DomainValidationError("Results data must be a dictionary.")

        raw_entries = data.get("entries", [])
        entries = [
            ResultEntry.from_dict(e) if isinstance(e, dict) else e for e in raw_entries
        ]

        return cls(
            schema_version=data.get("schema_version", "1.0"),
            results_id=data.get("results_id", f"res_{uuid.uuid4().hex[:8]}"),
            design_ref=data.get("design_ref", ""),
            entries=entries,
            completeness=data.get("completeness", "complete"),
            metadata=data.get("metadata"),
        )

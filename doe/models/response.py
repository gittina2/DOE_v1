from dataclasses import dataclass
from typing import Any, Literal, Optional, Dict
from doe.models.exceptions import (
    DomainValidationError,
    MissingResponseError,
    InvalidResponseTypeError,
)

ResponseType = Literal["continuous"]

@dataclass
class Response:
    name: str
    type: ResponseType
    unit: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    schema_version: str = "1.1"

    def validate(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise MissingResponseError("Response name is required and must be non-empty.")
            
        if self.type != "continuous":
            raise InvalidResponseTypeError(f"Unsupported response type: {self.type}")
            
        if self.unit is not None:
            if not isinstance(self.unit, str) or not self.unit.strip():
                raise DomainValidationError("Response unit, if present, must be non-empty.")

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "type": self.type,
            "unit": self.unit,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Response":
        return cls(
            schema_version=data.get("schema_version", "1.1"),
            name=data.get("name", ""),
            type=data.get("type", ""),
            unit=data.get("unit"),
            metadata=data.get("metadata"),
        )

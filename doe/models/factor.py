from dataclasses import dataclass
from typing import Any, Literal, Optional, List, Dict
from doe.models.exceptions import (
    DomainValidationError,
    InvalidFactorTypeError,
    InvalidFactorBoundsError,
    MissingFactorLevelsError,
    DuplicateFactorLevelsError,
)

FactorType = Literal["continuous", "categorical"]

@dataclass
class Factor:
    name: str
    type: FactorType
    unit: Optional[str] = None
    levels: Optional[List[Any]] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    schema_version: str = "1.0"

    def validate(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise DomainValidationError("Factor name is required and must be non-empty.")
            
        if self.type not in ("continuous", "categorical"):
            raise InvalidFactorTypeError(f"Unsupported factor type: {self.type}")
            
        if self.type == "continuous":
            if self.levels is not None:
                raise DomainValidationError("Continuous factor cannot have levels defined.")
            if self.lower_bound is None or self.upper_bound is None:
                raise InvalidFactorBoundsError("Continuous factor must have lower_bound and upper_bound defined.")
            if not isinstance(self.lower_bound, (int, float)) or not isinstance(self.upper_bound, (int, float)):
                raise InvalidFactorBoundsError("Bounds must be numeric.")
            if self.lower_bound >= self.upper_bound:
                raise InvalidFactorBoundsError(f"lower_bound ({self.lower_bound}) must be less than upper_bound ({self.upper_bound}).")
                
        if self.type == "categorical":
            if self.lower_bound is not None or self.upper_bound is not None:
                raise DomainValidationError("Categorical factor cannot have lower_bound or upper_bound defined.")
            if self.levels is None:
                raise MissingFactorLevelsError("Categorical factor must have levels defined.")
            if not isinstance(self.levels, list):
                raise MissingFactorLevelsError("Levels must be a list.")
            if len(self.levels) < 2:
                raise DuplicateFactorLevelsError("Categorical factor levels must contain at least 2 values.")
            
            # Check levels contain numbers or letters (strings, ints, floats)
            for level in self.levels:
                if not isinstance(level, (str, int, float)):
                    raise DomainValidationError(f"Invalid level type: {type(level)}. Levels must be numbers or letters.")
            
            # Check duplicates
            if len(set(self.levels)) != len(self.levels):
                raise DuplicateFactorLevelsError("Categorical factor levels must not contain duplicate values.")

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "type": self.type,
            "unit": self.unit,
            "levels": self.levels,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Factor":
        return cls(
            schema_version=data.get("schema_version", "1.0"),
            name=data.get("name", ""),
            type=data.get("type", ""),
            unit=data.get("unit"),
            levels=data.get("levels"),
            lower_bound=data.get("lower_bound"),
            upper_bound=data.get("upper_bound"),
            metadata=data.get("metadata"),
        )

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, List, Dict
from doe.models.factor import Factor
from doe.models.response import Response
from doe.models.exceptions import (
    DomainValidationError,
    DuplicateFactorNameError,
    InvalidDesignTypeError,
    InvalidPlannedRunsError,
)

DesignType = Literal["full_factorial", "fractional_factorial"]

@dataclass
class Experiment:
    name: str
    factors: List[Factor]
    responses: List[Response]
    design_type: DesignType
    description: Optional[str] = None
    planned_runs: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = "1.0"

    def validate(self) -> None:
        if not isinstance(self.experiment_id, str) or not self.experiment_id.strip():
            raise DomainValidationError("experiment_id is required and must be non-empty.")
            
        if not isinstance(self.name, str) or not self.name.strip():
            raise DomainValidationError("Experiment name is required and must be non-empty.")
            
        if not self.factors:
            raise DomainValidationError("At least one factor is required.")
            
        if not self.responses:
            raise DomainValidationError("At least one response is required.")
            
        if self.design_type not in ("full_factorial", "fractional_factorial"):
            raise InvalidDesignTypeError(f"Unsupported design type: {self.design_type}")
            
        if self.planned_runs is not None:
            if not isinstance(self.planned_runs, int) or isinstance(self.planned_runs, bool) or self.planned_runs <= 0:
                raise InvalidPlannedRunsError(f"planned_runs must be a positive integer, got: {self.planned_runs}")
                
        # Validate all factors and check for unique names
        factor_names = set()
        for factor in self.factors:
            if not isinstance(factor, Factor):
                raise DomainValidationError("All items in factors list must be Factor instances.")
            factor.validate()
            if factor.name in factor_names:
                raise DuplicateFactorNameError(f"Duplicate factor name detected: {factor.name}")
            factor_names.add(factor.name)
            
        # Validate all responses and check for unique names
        response_names = set()
        for response in self.responses:
            if not isinstance(response, Response):
                raise DomainValidationError("All items in responses list must be Response instances.")
            response.validate()
            if response.name in response_names:
                raise DomainValidationError(f"Duplicate response name detected: {response.name}")
            response_names.add(response.name)

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "experiment_id": self.experiment_id,
            "name": self.name,
            "description": self.description,
            "factors": [f.to_dict() for f in self.factors],
            "responses": [r.to_dict() for r in self.responses],
            "design_type": self.design_type,
            "planned_runs": self.planned_runs,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Experiment":
        raw_factors = data.get("factors")
        raw_responses = data.get("responses")
        
        factors = [Factor.from_dict(f) for f in raw_factors] if raw_factors is not None else []
        responses = [Response.from_dict(r) for r in raw_responses] if raw_responses is not None else []
        
        return cls(
            schema_version=data.get("schema_version", "1.0"),
            experiment_id=data.get("experiment_id", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            factors=factors,
            responses=responses,
            design_type=data.get("design_type", ""),
            planned_runs=data.get("planned_runs"),
            metadata=data.get("metadata"),
        )

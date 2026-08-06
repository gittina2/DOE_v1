import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from doe.models.exceptions import DomainValidationError, InvalidAnalysisInputError


@dataclass
class Analysis:
    experiment_ref: str
    design_ref: str
    results_ref: str
    model_type: str = "linear"
    model_formula: Optional[str] = None
    coefficients: Optional[Dict[str, float]] = None
    anova_table: Optional[List[Dict[str, Any]]] = None
    p_values: Optional[Dict[str, float]] = None
    r_squared: Optional[float] = None
    adjusted_r_squared: Optional[float] = None
    residuals: Optional[List[float]] = None
    diagnostics: Optional[Dict[str, Any]] = None
    analysis_id: str = field(default_factory=lambda: f"ana_{uuid.uuid4().hex[:8]}")
    schema_version: str = "1.0"
    metadata: Optional[Dict[str, Any]] = None

    def validate(self) -> None:
        if not isinstance(self.analysis_id, str) or not self.analysis_id.strip():
            raise DomainValidationError("analysis_id must be a non-empty string.")

        if not isinstance(self.experiment_ref, str) or not self.experiment_ref.strip():
            raise DomainValidationError("experiment_ref must be a non-empty string.")

        if not isinstance(self.design_ref, str) or not self.design_ref.strip():
            raise DomainValidationError("design_ref must be a non-empty string.")

        if not isinstance(self.results_ref, str) or not self.results_ref.strip():
            raise DomainValidationError("results_ref must be a non-empty string.")

        if not isinstance(self.model_type, str) or not self.model_type.strip():
            raise DomainValidationError("model_type must be a non-empty string.")

        if self.r_squared is not None:
            if not isinstance(self.r_squared, (int, float)) or not (0.0 <= self.r_squared <= 1.0):
                raise DomainValidationError("r_squared must be a float between 0.0 and 1.0.")

        if self.adjusted_r_squared is not None:
            if not isinstance(self.adjusted_r_squared, (int, float)) or not (0.0 <= self.adjusted_r_squared <= 1.0):
                raise DomainValidationError("adjusted_r_squared must be a float between 0.0 and 1.0.")

        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise DomainValidationError("metadata must be a dictionary or None.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "analysis_id": self.analysis_id,
            "model_type": self.model_type,
            "model_formula": self.model_formula,
            "experiment_ref": self.experiment_ref,
            "design_ref": self.design_ref,
            "results_ref": self.results_ref,
            "coefficients": self.coefficients,
            "anova_table": self.anova_table,
            "p_values": self.p_values,
            "r_squared": self.r_squared,
            "adjusted_r_squared": self.adjusted_r_squared,
            "residuals": self.residuals,
            "diagnostics": self.diagnostics,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Analysis":
        if not isinstance(data, dict):
            raise DomainValidationError("Analysis data must be a dictionary.")

        return cls(
            schema_version=data.get("schema_version", "1.0"),
            analysis_id=data.get("analysis_id", f"ana_{uuid.uuid4().hex[:8]}"),
            model_type=data.get("model_type", "linear"),
            model_formula=data.get("model_formula"),
            experiment_ref=data.get("experiment_ref", ""),
            design_ref=data.get("design_ref", ""),
            results_ref=data.get("results_ref", ""),
            coefficients=data.get("coefficients"),
            anova_table=data.get("anova_table"),
            p_values=data.get("p_values"),
            r_squared=data.get("r_squared"),
            adjusted_r_squared=data.get("adjusted_r_squared"),
            residuals=data.get("residuals"),
            diagnostics=data.get("diagnostics"),
            metadata=data.get("metadata"),
        )

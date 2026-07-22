from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Dict
from doe.models.design import Design
from doe.models.experiment import Experiment
from doe.models.results import Results
from doe.models.analysis import Analysis
from doe.models.exceptions import WorkflowStateMismatchError, SchemaVersionMismatchError


WorkflowStep = Literal[
    "empty",
    "experiment_created",
    "design_generated",
    "results_in_progress",
    "results_complete",
    "analysis_created",
    "report_generated",
]

@dataclass
class WorkflowState:
    step: WorkflowStep
    audit: Dict[str, Any] = field(default_factory=dict)
    experiment: Optional[Experiment] = None
    design: Optional[Design] = None
    results: Optional[Results] = None
    analysis: Optional[Any] = None
    schema_version: str = "1.0"

    def validate(self) -> None:
        supported_steps = (
            "empty",
            "experiment_created",
            "design_generated",
            "results_in_progress",
            "results_complete",
            "analysis_created",
            "report_generated",
        )
        if self.step not in supported_steps:
            raise WorkflowStateMismatchError(f"Unsupported workflow step: {self.step}")

        if not isinstance(self.audit, dict):
            raise WorkflowStateMismatchError("Audit field must be a dictionary.")
        if not all(isinstance(k, str) for k in self.audit.keys()):
            raise WorkflowStateMismatchError("All audit dictionary keys must be strings.")

        if self.step == "empty":
            if (
                self.experiment is not None
                or self.design is not None
                or self.results is not None
                or self.analysis is not None
            ):
                raise WorkflowStateMismatchError("For step 'empty', no entities can be defined.")
                
        elif self.step == "experiment_created":
            if self.experiment is None:
                raise WorkflowStateMismatchError("For step 'experiment_created', experiment must be defined.")
            if (
                self.design is not None
                or self.results is not None
                or self.analysis is not None
            ):
                raise WorkflowStateMismatchError(
                    "For step 'experiment_created', design, results, and analysis must be None."
                )
            self.experiment.validate()
            
        elif self.step == "design_generated":
            if self.experiment is None or self.design is None:
                raise WorkflowStateMismatchError(
                    "For step 'design_generated', experiment and design must be defined."
                )
            if self.results is not None or self.analysis is not None:
                raise WorkflowStateMismatchError(
                    "For step 'design_generated', results and analysis must be None."
                )
            self.experiment.validate()
            self.design.validate(self.experiment)
            
        elif self.step in ("results_in_progress", "results_complete"):
            if self.experiment is None or self.design is None or self.results is None:
                raise WorkflowStateMismatchError(
                    f"For step '{self.step}', experiment, design, and results must be defined."
                )
            if self.analysis is not None:
                raise WorkflowStateMismatchError(
                    f"For step '{self.step}', analysis must be None."
                )
            self.experiment.validate()
            self.design.validate(self.experiment)
            if hasattr(self.results, "validate"):
                self.results.validate()
            
        elif self.step == "analysis_created":
            if (
                self.experiment is None
                or self.design is None
                or self.results is None
                or self.analysis is None
            ):
                raise WorkflowStateMismatchError("For step 'analysis_created', all entities must be defined.")
            self.experiment.validate()
            self.design.validate(self.experiment)
            if hasattr(self.results, "validate"):
                self.results.validate()
            if hasattr(self.analysis, "validate"):
                self.analysis.validate()

            
        elif self.step == "report_generated":
            if self.experiment is None:
                raise WorkflowStateMismatchError(
                    "For step 'report_generated', at least experiment must be defined."
                )
            self.experiment.validate()

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "step": self.step,
            "audit": self.audit,
            "experiment": self.experiment.to_dict() if self.experiment is not None else None,
            "design": self.design.to_dict() if self.design is not None else None,
            "results": self.results.to_dict() if hasattr(self.results, "to_dict") else self.results,
            "analysis": self.analysis.to_dict() if hasattr(self.analysis, "to_dict") else self.analysis,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowState":
        exp_data = data.get("experiment")
        experiment = Experiment.from_dict(exp_data) if exp_data is not None else None
        
        design_data = data.get("design")
        design = Design.from_dict(design_data) if design_data is not None else None

        results_data = data.get("results")
        results = Results.from_dict(results_data) if isinstance(results_data, dict) else results_data

        analysis_data = data.get("analysis")
        analysis = Analysis.from_dict(analysis_data) if isinstance(analysis_data, dict) else analysis_data

        return cls(
            schema_version=data.get("schema_version", "1.0"),
            step=data.get("step", "empty"),
            audit=data.get("audit", {}),
            experiment=experiment,
            design=design,
            results=results,
            analysis=analysis,
        )

    def save_to_json(self, file_path: str) -> None:
        import json
        with open(file_path, mode="w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load_from_json(cls, file_path: str) -> "WorkflowState":
        import json
        with open(file_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
            
        version = data.get("schema_version")
        if version != "1.0":
            raise SchemaVersionMismatchError(
                f"Unsupported schema version: {version}. Expected '1.0'."
            )
            
        state = cls.from_dict(data)
        state.validate()
        return state

    def transition_to(self, new_step: WorkflowStep, **kwargs) -> "WorkflowState":
        
        self.validate()

        allowed_transitions = {
            "empty": ["experiment_created"],
            "experiment_created": ["design_generated"],
            "design_generated": ["results_in_progress", "results_complete"],
            "results_in_progress": ["results_in_progress", "results_complete"],
            "results_complete": ["results_in_progress", "results_complete", "analysis_created"],
            "analysis_created": ["report_generated"],
            "report_generated": []
        }

        if new_step not in allowed_transitions[self.step]:
            raise WorkflowStateMismatchError(
                f"Invalid transition from {self.step} to {new_step}."
            )

        new_state = WorkflowState(
            step=new_step,
            audit={
                **self.audit,
                **kwargs.get("audit", {}),
                "transition": f"{self.step} -> {new_step}",
            },
            experiment=kwargs.get("experiment", self.experiment),
            design=kwargs.get("design", self.design),
            results=kwargs.get("results", self.results),
            analysis=kwargs.get("analysis", self.analysis),
            schema_version=self.schema_version,
        )

        new_state.validate()

        return new_state
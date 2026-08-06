from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from doe.models.exceptions import (
    DomainValidationError,
    MissingFactorLevelsError,
    IncompatibleFactorDefinitionError,
    RunCountMismatchError,
    DuplicateRunIdError,
    InconsistentReferenceError,
)

from doe.models.experiment import Experiment

DesignType = Literal["full_factorial", "fractional_factorial"]

# ---------------------------------------------------------------------------
# Run model
# ---------------------------------------------------------------------------

@dataclass
class Run:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_number: Optional[int] = None
    factor_values: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None
    schema_version: str = "1.1"

    def validate(self, experiment: Experiment) -> None:
        """Validate that this run conforms to the provided experiment.

        * All factor names defined in the experiment must be present.
        * No extra factor names are allowed.
        * Values must respect the corresponding Factor constraints.
        """
        if not self.run_id:
            raise DomainValidationError("Run identifier must be non‑empty.")

        # Ensure the run contains exactly the factor set defined by the experiment
        exp_factor_names = {f.name for f in experiment.factors}
        run_factor_names = set(self.factor_values.keys())
        missing = exp_factor_names - run_factor_names
        extra = run_factor_names - exp_factor_names
        if missing:
            raise DomainValidationError(f"Run missing required factors: {missing}")
        if extra:
            raise DomainValidationError(f"Run contains unknown factors: {extra}")

        # Validate each factor value against its definition
        for factor in experiment.factors:
            value = self.factor_values[factor.name]
            if factor.type == "continuous":
                # Continuous values must be numeric and within bounds
                if not isinstance(value, (int, float)):
                    raise DomainValidationError(
                        f"Continuous factor '{factor.name}' requires a numeric value."
                    )
                if factor.lower_bound is not None and value < factor.lower_bound:
                    raise DomainValidationError(
                        f"Value {value} for factor '{factor.name}' below lower bound {factor.lower_bound}."
                    )
                if factor.upper_bound is not None and value > factor.upper_bound:
                    raise DomainValidationError(
                        f"Value {value} for factor '{factor.name}' above upper bound {factor.upper_bound}."
                    )
            else:  # categorical
                if factor.levels is None:
                    raise DomainValidationError(
                        f"Categorical factor '{factor.name}' missing level definition."
                    )
                if value not in factor.levels:
                    raise DomainValidationError(
                        f"Value {value!r} for factor '{factor.name}' not in allowed levels {factor.levels}."
                    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "run_number": self.run_number,
            "factor_values": self.factor_values,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Run":
        return cls(
            schema_version=data.get("schema_version", "1.1"),
            run_id=data.get("run_id", ""),
            run_number=data.get("run_number"),
            factor_values=data.get("factor_values", {}),
            metadata=data.get("metadata"),
        )


# ---------------------------------------------------------------------------
# Block model (optional grouping of runs)
# ---------------------------------------------------------------------------

@dataclass
class Block:
    block_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_ids: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    schema_version: str = "1.1"

    def validate(self, design: "Design") -> None:
        if not self.block_id:
            raise DomainValidationError("Block identifier must be non‑empty.")
        if not self.run_ids:
            raise DomainValidationError("Block must contain at least one run identifier.")
        # Ensure all referenced run IDs exist in the design
        design_run_ids = {run.run_id for run in design.runs}
        missing = set(self.run_ids) - design_run_ids
        if missing:
            raise InconsistentReferenceError(
                f"Block references unknown run IDs: {missing}"
            )
        # Ensure a run does not belong to multiple blocks
        # (Checked at Design level – we just validate uniqueness here)
        if len(set(self.run_ids)) != len(self.run_ids):
            raise DomainValidationError("Block contains duplicate run IDs.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "block_id": self.block_id,
            "run_ids": self.run_ids,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        return cls(
            schema_version=data.get("schema_version", "1.1"),
            block_id=data.get("block_id", ""),
            run_ids=data.get("run_ids", []),
            metadata=data.get("metadata"),
        )


# ---------------------------------------------------------------------------
# FactorCoding model – transformation between experimental and coded values
# ---------------------------------------------------------------------------

@dataclass
class FactorCoding:
    """Represents the transformation between experimental values and coded DOE levels.

    Supported coding methods (MVP):
        - two_level: maps [lower_bound, upper_bound] → [-1, +1]
        - center_scale: maps by (value - center) / half_range
    """
    factor_ref: str
    method: str
    mapping: Dict[str, float]
    metadata: Optional[Dict[str, Any]] = None

    def validate(self) -> None:
        if not isinstance(self.factor_ref, str) or not self.factor_ref.strip():
            raise DomainValidationError("factor_ref must be a non-empty string.")

        supported_methods = ("two_level", "center_scale")
        if self.method not in supported_methods:
            raise DomainValidationError(
                f"Unsupported coding method: {self.method}. Supported: {supported_methods}"
            )

        if not isinstance(self.mapping, dict) or not self.mapping:
            raise DomainValidationError("mapping must be a non-empty dictionary.")

        for key, value in self.mapping.items():
            if not isinstance(value, (int, float)):
                raise DomainValidationError(
                    f"Coded value for '{key}' must be numeric, got {type(value).__name__}."
                )

        if self.method == "two_level":
            coded_values = set(self.mapping.values())
            if coded_values != {-1.0, 1.0} and coded_values != {-1, 1}:
                raise DomainValidationError(
                    "two_level coding must use exactly -1 and +1 coded values."
                )

        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise DomainValidationError("metadata must be a dictionary or None.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_ref": self.factor_ref,
            "method": self.method,
            "mapping": self.mapping,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactorCoding":
        return cls(
            factor_ref=data.get("factor_ref", ""),
            method=data.get("method", ""),
            mapping=data.get("mapping", {}),
            metadata=data.get("metadata"),
        )


# ---------------------------------------------------------------------------
# Design model – aggregate of runs (and optional blocks)
# ---------------------------------------------------------------------------

@dataclass
class Design:
    experiment_ref: str
    design_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    design_type: str = "full_factorial"
    runs: List[Run] = field(default_factory=list)
    factor_coding: Optional[List[FactorCoding]] = None
    blocks: List[Block] = field(default_factory=list)  # optional grouping
    randomization: bool = False
    order: Optional[List[str]] = None  # permutation of run IDs if supplied
    replications: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    schema_version: str = "1.1"

    def validate(self, experiment: Experiment) -> None:
        # Basic structural checks
        if not self.design_id:
            raise DomainValidationError("Design identifier must be non‑empty.")
        if not self.runs:
            raise DomainValidationError("Design must contain at least one run.")
        if not self.experiment_ref:
            raise InconsistentReferenceError(
                "Design has no experiment reference."
            )
        if self.experiment_ref != experiment.experiment_id:
            raise InconsistentReferenceError(
                "Design reference does not match experiment."
            )
        # Unique run identifiers
        run_ids = [run.run_id for run in self.runs]
        if len(set(run_ids)) != len(run_ids):
            raise DuplicateRunIdError("Run identifiers must be unique within a design.")
        # Validate each run against the experiment definition
        for run in self.runs:
            run.validate(experiment)
        # Validate optional order permutation
        if self.order is not None:
            if set(self.order) != set(run_ids):
                raise DomainValidationError("Order must be a permutation of all run IDs.")
        # Validate blocks (if any)
        if self.blocks:
            # Ensure no run belongs to more than one block
            all_blocked = []
            for block in self.blocks:
                block.validate(self)
                all_blocked.extend(block.run_ids)
            if len(set(all_blocked)) != len(all_blocked):
                raise DomainValidationError("A run cannot belong to multiple blocks.")
        # Run count matches expected factorial size for full factorial
        if self.design_type == "full_factorial":
            expected = 1
            for factor in experiment.factors:
                if factor.type == "categorical":
                    if factor.levels is None:
                        raise MissingFactorLevelsError("Categorical factor missing levels.")
                    expected *= len(factor.levels)
                else:  # In the MVP full factorial implementation, continuous factors are discretized into two levels using lower_bound and upper_bound.
                    expected *= 2
            if len(self.runs) != expected:
                raise RunCountMismatchError(
                    f"Full factorial design expected {expected} runs, got {len(self.runs)}."
                )
        # Validate factor coding (if any)
        if self.factor_coding is not None:
            factor_names = {f.name for f in experiment.factors}
            for fc in self.factor_coding:
                fc.validate()
                if fc.factor_ref not in factor_names:
                    raise InconsistentReferenceError(
                        f"FactorCoding references unknown factor: '{fc.factor_ref}'."
                    )
        # Validate replications (if present)
        if self.replications is not None:
            if not isinstance(self.replications, int) or self.replications < 1:
                raise DomainValidationError("replications must be a positive integer.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "design_id": self.design_id,
            "design_type": self.design_type,
            "experiment_ref": self.experiment_ref,
            "runs": [run.to_dict() for run in self.runs],
            "factor_coding": [fc.to_dict() for fc in self.factor_coding] if self.factor_coding is not None else None,
            "blocks": [block.to_dict() for block in self.blocks],
            "randomization": self.randomization,
            "order": self.order,
            "replications": self.replications,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Design":
        exp = data.get("experiment_ref", "")
        runs = [Run.from_dict(r) for r in data.get("runs", [])]
        blocks = [Block.from_dict(b) for b in data.get("blocks", [])]
        raw_fc = data.get("factor_coding")
        factor_coding = [FactorCoding.from_dict(fc) for fc in raw_fc] if raw_fc is not None else None
        return cls(
            schema_version=data.get("schema_version", "1.1"),
            design_id=data.get("design_id", ""),
            design_type=data.get("design_type", "full_factorial"),
            experiment_ref=exp,
            runs=runs,
            factor_coding=factor_coding,
            blocks=blocks,
            randomization=data.get("randomization"),
            order=data.get("order"),
            replications=data.get("replications"),
            metadata=data.get("metadata"),
        )

# End of design module


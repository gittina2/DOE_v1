"""Full factorial design generator.

Generates every possible combination of factor levels for a given
experiment, creating one Run per combination.

MVP representation for continuous factors:
    [lower_bound, upper_bound]  — standard 2-level design.

Categorical factors use the levels list as-is.
"""

from doe.models import InvalidDesignMatrixError, DuplicateRunIdError, FactorCoding
import itertools
import uuid
from typing import Any, Dict, List, Tuple

from doe.designs.generator_interface import DesignGenerator
from doe.models.experiment import Experiment
from doe.models.factor import Factor
from doe.models.design import Design, Run
from doe.models.exceptions import IncompatibleFactorDefinitionError


def _factor_levels(factor: Factor) -> List[Any]:
    """Return the discrete levels for a factor.

    * **Categorical**: uses the ``levels`` list directly.
    * **Continuous** (MVP): uses ``[lower_bound, upper_bound]``.
    """
    if factor.type == "categorical":
        if factor.levels is None or len(factor.levels) < 2:
            raise IncompatibleFactorDefinitionError(
                f"Categorical factor '{factor.name}' must have at least 2 levels."
            )
        return list(factor.levels)

    # continuous
    if factor.lower_bound is None or factor.upper_bound is None:
        raise IncompatibleFactorDefinitionError(
            f"Continuous factor '{factor.name}' must have lower_bound and upper_bound."
        )
    return [factor.lower_bound, factor.upper_bound]


def generate_factorial_combinations(
    experiment: Experiment,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Compute the Cartesian product of all factor levels.

    Returns
    -------
    factor_names : list[str]
        Ordered list of factor names.
    combinations : list[dict[str, Any]]
        One dict per combination mapping factor name → value.
    """
    factor_names: List[str] = []
    level_lists: List[List[Any]] = []

    for factor in experiment.factors:
        factor_names.append(factor.name)
        level_lists.append(_factor_levels(factor))

    combinations: List[Dict[str, Any]] = []
    for values in itertools.product(*level_lists):
        combinations.append(dict(zip(factor_names, values)))

    return factor_names, combinations

def combinations_to_runs(
    combinations: List[Dict[str, Any]],
    experiment: Experiment,
) -> List[Run]:
    """Convert combinations into validated Run objects."""

    if not combinations:
        raise InvalidDesignMatrixError(
            "Cannot create runs from an empty factorial matrix."
        )

    runs: List[Run] = []
    run_ids = set()

    for idx, combo in enumerate(combinations, start=1):      
        run = Run(
            run_number=idx,
            factor_values=combo
        )

        # ensure generated IDs are unique
        if run.run_id in run_ids:
            raise DuplicateRunIdError(
                f"Duplicate run id generated: {run.run_id}"
            )

        run_ids.add(run.run_id)

        # validate run against experiment definition
        run.validate(experiment)

        runs.append(run)

    if len({r.run_id for r in runs}) != len(runs):
        raise DuplicateRunIdError(
            "Generated runs contain duplicate identifiers."
        )
    return runs


def generate_factor_codings(experiment: Experiment) -> List[FactorCoding]:
    """Generate factor codings for factors in an experiment."""
    codings: List[FactorCoding] = []
    for factor in experiment.factors:
        f_type = factor.type.value if hasattr(factor.type, "value") else str(factor.type)
        if f_type == "continuous":
            codings.append(
                FactorCoding(
                    factor_ref=factor.name,
                    method="two_level",
                    mapping={
                        str(factor.lower_bound): -1.0,
                        str(factor.upper_bound): 1.0,
                    },
                )
            )
        elif f_type == "categorical" and factor.levels and len(factor.levels) == 2:
            codings.append(
                FactorCoding(
                    factor_ref=factor.name,
                    method="two_level",
                    mapping={
                        str(factor.levels[0]): -1.0,
                        str(factor.levels[1]): 1.0,
                    },
                )
            )
    return codings


class FullFactorialGenerator(DesignGenerator):
    """Concrete generator that produces a full factorial design.

    Every possible combination of factor levels is generated.
    """

    def generate(self, experiment: Experiment) -> Design:
        """Generate a full factorial Design from *experiment*."""
        # Pre-condition: validate experiment
        experiment.validate()

        # Generate all factor combinations
        _factor_names, combinations = generate_factorial_combinations(experiment)

        # Convert each combination into a Run
        runs = combinations_to_runs(
            combinations,
            experiment
        )

        # Generate factor coding
        factor_coding = generate_factor_codings(experiment)

        # Assemble the Design
        design = Design(
            design_id=str(uuid.uuid4()),
            design_type="full_factorial",
            experiment_ref=experiment.experiment_id,
            runs=runs,
            factor_coding=factor_coding,
        )

        # Post-condition: validate the assembled design
        design.validate(experiment=experiment)

        return design

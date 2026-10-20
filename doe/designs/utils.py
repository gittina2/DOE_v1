"""Shared utility functions for DOE design generation.

Contains reusable helper functions for level extraction, factorial combination
generation, run creation, and factor coding generation across different design
generators.
"""

import itertools
from typing import Any, Dict, List, Tuple

from doe.models.experiment import Experiment
from doe.models.factor import Factor
from doe.models.design import Run, FactorCoding
from doe.models.exceptions import (
    IncompatibleFactorDefinitionError,
    InvalidDesignMatrixError,
    DuplicateRunIdError,
)


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
            factor_values=combo,
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
    """Generate factor codings for factors in an experiment.

    Generates two_level [-1, +1] codings for:
    - continuous factors using [lower_bound, upper_bound]
    - categorical factors with exactly 2 levels
    """
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

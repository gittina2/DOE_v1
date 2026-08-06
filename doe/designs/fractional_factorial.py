"""Fractional factorial design generator.

Generates a fractional subset of standard 2-level factorial designs.
For k >= 3 factors, generates a half-fraction 2^(k-1) design using defining relation.
For k < 3 factors, falls back to full factorial.
"""

import uuid
from typing import Any, Dict, List, Tuple

from doe.designs.generator_interface import DesignGenerator
from doe.designs.full_factorial import (
    generate_factorial_combinations,
    combinations_to_runs,
    generate_factor_codings,
)
from doe.models.experiment import Experiment
from doe.models.design import Design
from doe.models.exceptions import UnsupportedDesignTypeError


class FractionalFactorialGenerator(DesignGenerator):
    """Concrete generator that produces a fractional factorial design.

    Generates a 2^(k-1) half-fraction design when possible.
    """

    def generate(self, experiment: Experiment) -> Design:
        """Generate a fractional factorial Design from *experiment*."""
        experiment.validate()

        factor_names, full_combinations = generate_factorial_combinations(experiment)
        k = len(factor_names)

        if k >= 3:
            # Generate 2^(k-1) half-fraction subset.
            fractional_combinations = []
            for combo in full_combinations:
                coded_sum = 0
                for fname in factor_names[:-1]:
                    factor = next(f for f in experiment.factors if f.name == fname)
                    val = combo[fname]
                    if factor.type == "continuous" and factor.lower_bound is not None and factor.upper_bound is not None:
                        coded = -1 if abs(val - factor.lower_bound) < abs(val - factor.upper_bound) else 1
                    elif factor.type == "categorical" and factor.levels:
                        coded = -1 if val == factor.levels[0] else 1
                    else:
                        coded = 1
                    coded_sum += (1 if coded > 0 else 0)

                last_fname = factor_names[-1]
                last_factor = next(f for f in experiment.factors if f.name == last_fname)
                last_val = combo[last_fname]
                if last_factor.type == "continuous" and last_factor.lower_bound is not None and last_factor.upper_bound is not None:
                    last_coded = -1 if abs(last_val - last_factor.lower_bound) < abs(last_val - last_factor.upper_bound) else 1
                elif last_factor.type == "categorical" and last_factor.levels:
                    last_coded = -1 if last_val == last_factor.levels[0] else 1
                else:
                    last_coded = 1

                expected_coded = 1 if (coded_sum % 2 == 0) else -1
                if last_coded == expected_coded:
                    fractional_combinations.append(combo)

            combinations = fractional_combinations if fractional_combinations else full_combinations[::2]
        else:
            combinations = full_combinations

        runs = combinations_to_runs(combinations, experiment)
        factor_coding = generate_factor_codings(experiment)

        design = Design(
            design_id=str(uuid.uuid4()),
            design_type="fractional_factorial",
            experiment_ref=experiment.experiment_id,
            runs=runs,
            factor_coding=factor_coding,
        )

        design.validate(experiment=experiment)
        return design

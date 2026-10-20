"""Full factorial design generator.

Generates every possible combination of factor levels for a given
experiment, creating one Run per combination.

MVP representation for continuous factors:
    [lower_bound, upper_bound]  — standard 2-level design.

Categorical factors use the levels list as-is.
"""

import uuid
from doe.designs.generator_interface import DesignGenerator
from doe.designs.utils import (
    _factor_levels,
    generate_factorial_combinations,
    combinations_to_runs,
    generate_factor_codings,
)
from doe.models.experiment import Experiment
from doe.models.design import Design


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

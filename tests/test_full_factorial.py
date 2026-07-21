"""Tests for the full factorial design generator (Task 2.2)."""

import pytest

from doe.models.factor import Factor
from doe.models.response import Response
from doe.models.experiment import Experiment
from doe.models.design import Design, Run
from doe.models.exceptions import (
    IncompatibleFactorDefinitionError,
    UnsupportedDesignTypeError,
)
from doe.designs.full_factorial import (
    FullFactorialGenerator,
    generate_factorial_combinations,
    _factor_levels,
)


# ---------------------------------------------------------------------------
# _factor_levels helper
# ---------------------------------------------------------------------------

class TestFactorLevels:
    def test_categorical_factor_returns_levels(self):
        f = Factor(name="color", type="categorical", levels=["red", "green", "blue"])
        assert _factor_levels(f) == ["red", "green", "blue"]

    def test_continuous_factor_returns_bounds(self):
        f = Factor(name="temp", type="continuous", lower_bound=20.0, upper_bound=80.0)
        assert _factor_levels(f) == [20.0, 80.0]

    def test_categorical_factor_missing_levels_raises(self):
        f = Factor(name="color", type="categorical", levels=None)
        with pytest.raises(IncompatibleFactorDefinitionError, match="at least 2 levels"):
            _factor_levels(f)

    def test_continuous_factor_missing_bounds_raises(self):
        f = Factor(name="temp", type="continuous", lower_bound=None, upper_bound=None)
        with pytest.raises(IncompatibleFactorDefinitionError, match="lower_bound and upper_bound"):
            _factor_levels(f)


# ---------------------------------------------------------------------------
# generate_factorial_combinations
# ---------------------------------------------------------------------------

class TestGenerateFactorialCombinations:
    def test_two_categorical_factors(self):
        exp = Experiment(
            name="test",
            factors=[
                Factor(name="A", type="categorical", levels=["a1", "a2"]),
                Factor(name="B", type="categorical", levels=["b1", "b2", "b3"]),
            ],
            responses=[Response(name="Y", type="continuous")],
            design_type="full_factorial",
        )
        names, combos = generate_factorial_combinations(exp)
        assert names == ["A", "B"]
        assert len(combos) == 6  # 2 * 3
        # Verify all combinations are present
        expected = [
            {"A": "a1", "B": "b1"},
            {"A": "a1", "B": "b2"},
            {"A": "a1", "B": "b3"},
            {"A": "a2", "B": "b1"},
            {"A": "a2", "B": "b2"},
            {"A": "a2", "B": "b3"},
        ]
        assert combos == expected

    def test_one_continuous_factor(self):
        exp = Experiment(
            name="test",
            factors=[
                Factor(name="temp", type="continuous", lower_bound=10.0, upper_bound=90.0),
            ],
            responses=[Response(name="Y", type="continuous")],
            design_type="full_factorial",
        )
        names, combos = generate_factorial_combinations(exp)
        assert names == ["temp"]
        assert len(combos) == 2  # [lower, upper]
        assert combos[0] == {"temp": 10.0}
        assert combos[1] == {"temp": 90.0}

    def test_mixed_factors(self):
        exp = Experiment(
            name="test",
            factors=[
                Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0),
                Factor(name="material", type="categorical", levels=["steel", "wood"]),
            ],
            responses=[Response(name="Y", type="continuous")],
            design_type="full_factorial",
        )
        names, combos = generate_factorial_combinations(exp)
        assert len(combos) == 4  # 2 * 2
        # Check that all factor names present in every combo
        for c in combos:
            assert set(c.keys()) == {"temp", "material"}

    def test_three_factors(self):
        exp = Experiment(
            name="test",
            factors=[
                Factor(name="A", type="categorical", levels=["lo", "hi"]),
                Factor(name="B", type="categorical", levels=["x", "y", "z"]),
                Factor(name="C", type="continuous", lower_bound=1.0, upper_bound=5.0),
            ],
            responses=[Response(name="Y", type="continuous")],
            design_type="full_factorial",
        )
        names, combos = generate_factorial_combinations(exp)
        assert len(combos) == 2 * 3 * 2  # = 12


# ---------------------------------------------------------------------------
# FullFactorialGenerator
# ---------------------------------------------------------------------------

class TestFullFactorialGenerator:
    def _make_experiment(self, **kwargs):
        defaults = dict(
            name="test experiment",
            factors=[
                Factor(name="A", type="categorical", levels=["lo", "hi"]),
                Factor(name="B", type="categorical", levels=["x", "y"]),
            ],
            responses=[Response(name="Y", type="continuous")],
            design_type="full_factorial",
        )
        defaults.update(kwargs)
        return Experiment(**defaults)

    def test_generates_correct_number_of_runs(self):
        gen = FullFactorialGenerator()
        exp = self._make_experiment()
        design = gen.generate(exp)
        assert len(design.runs) == 4  # 2 * 2

    def test_all_runs_have_unique_ids(self):
        gen = FullFactorialGenerator()
        exp = self._make_experiment()
        design = gen.generate(exp)
        ids = [r.run_id for r in design.runs]
        assert len(set(ids)) == len(ids)

    def test_all_runs_contain_all_factors(self):
        gen = FullFactorialGenerator()
        exp = self._make_experiment()
        design = gen.generate(exp)
        for run in design.runs:
            assert set(run.factor_values.keys()) == {"A", "B"}

    def test_design_passes_validation(self):
        gen = FullFactorialGenerator()
        exp = self._make_experiment()
        design = gen.generate(exp)
        # Should not raise
        design.validate(experiment=exp)

    def test_design_type_is_full_factorial(self):
        gen = FullFactorialGenerator()
        exp = self._make_experiment()
        design = gen.generate(exp)
        assert design.design_type == "full_factorial"

    def test_design_references_experiment(self):
        gen = FullFactorialGenerator()
        exp = self._make_experiment()
        design = gen.generate(exp)
        assert design.experiment_ref == exp.experiment_id

    def test_rejects_unsupported_design_type(self):
        gen = FullFactorialGenerator()
        exp = self._make_experiment(design_type="fractional_factorial")
        with pytest.raises(UnsupportedDesignTypeError, match="does not support"):
            gen.generate(exp)

    def test_continuous_factor_generates_two_level_runs(self):
        gen = FullFactorialGenerator()
        exp = self._make_experiment(
            factors=[
                Factor(name="temp", type="continuous", lower_bound=20.0, upper_bound=80.0),
            ],
        )
        design = gen.generate(exp)
        assert len(design.runs) == 2
        values = sorted(r.factor_values["temp"] for r in design.runs)
        assert values == [20.0, 80.0]

    def test_mixed_continuous_and_categorical(self):
        gen = FullFactorialGenerator()
        exp = self._make_experiment(
            factors=[
                Factor(name="temp", type="continuous", lower_bound=0.0, upper_bound=100.0),
                Factor(name="mat", type="categorical", levels=["A", "B", "C"]),
            ],
        )
        design = gen.generate(exp)
        assert len(design.runs) == 6  # 2 * 3

    def test_design_has_valid_id(self):
        gen = FullFactorialGenerator()
        exp = self._make_experiment()
        design = gen.generate(exp)
        assert design.design_id  # non-empty
        assert isinstance(design.design_id, str)

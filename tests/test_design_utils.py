"""Unit tests for shared DOE design utilities (doe.designs.utils).

Verifies level extraction, combination generation, run conversion,
factor coding generation, and compatibility with both full and fractional
factorial design generators.
"""

import pytest

from doe.models.factor import Factor
from doe.models.response import Response
from doe.models.experiment import Experiment
from doe.models.design import Run, FactorCoding
from doe.models.exceptions import (
    IncompatibleFactorDefinitionError,
    InvalidDesignMatrixError,
)
from doe.designs.utils import (
    _factor_levels,
    generate_factorial_combinations,
    combinations_to_runs,
    generate_factor_codings,
)
from doe.designs.full_factorial import FullFactorialGenerator
from doe.designs.fractional_factorial import FractionalFactorialGenerator


# ---------------------------------------------------------------------------
# _factor_levels tests
# ---------------------------------------------------------------------------

def test_factor_levels_continuous():
    f = Factor(name="temp", type="continuous", lower_bound=20.0, upper_bound=80.0)
    assert _factor_levels(f) == [20.0, 80.0]


def test_factor_levels_categorical():
    f = Factor(name="catalyst", type="categorical", levels=["CatA", "CatB"])
    assert _factor_levels(f) == ["CatA", "CatB"]


def test_factor_levels_invalid_continuous():
    f = Factor(name="temp", type="continuous", lower_bound=None, upper_bound=80.0)
    with pytest.raises(IncompatibleFactorDefinitionError, match="lower_bound and upper_bound"):
        _factor_levels(f)


def test_factor_levels_invalid_categorical():
    f = Factor(name="cat", type="categorical", levels=["only_one"])
    with pytest.raises(IncompatibleFactorDefinitionError, match="at least 2 levels"):
        _factor_levels(f)


# ---------------------------------------------------------------------------
# generate_factorial_combinations tests
# ---------------------------------------------------------------------------

def test_generate_factorial_combinations():
    f1 = Factor(name="T", type="continuous", lower_bound=10.0, upper_bound=50.0)
    f2 = Factor(name="solvent", type="categorical", levels=["water", "ethanol"])
    exp = Experiment(
        name="test_exp",
        factors=[f1, f2],
        responses=[Response(name="yield", type="continuous")],
    )

    factor_names, combos = generate_factorial_combinations(exp)
    assert factor_names == ["T", "solvent"]
    assert len(combos) == 4
    expected = [
        {"T": 10.0, "solvent": "water"},
        {"T": 10.0, "solvent": "ethanol"},
        {"T": 50.0, "solvent": "water"},
        {"T": 50.0, "solvent": "ethanol"},
    ]
    assert combos == expected


# ---------------------------------------------------------------------------
# combinations_to_runs tests
# ---------------------------------------------------------------------------

def test_combinations_to_runs_success():
    f1 = Factor(name="T", type="continuous", lower_bound=10.0, upper_bound=50.0)
    exp = Experiment(
        name="test_exp",
        factors=[f1],
        responses=[Response(name="yield", type="continuous")],
    )
    combos = [{"T": 10.0}, {"T": 50.0}]
    runs = combinations_to_runs(combos, exp)

    assert len(runs) == 2
    assert runs[0].run_number == 1
    assert runs[0].factor_values == {"T": 10.0}
    assert runs[1].run_number == 2
    assert runs[1].factor_values == {"T": 50.0}
    assert runs[0].run_id != runs[1].run_id


def test_combinations_to_runs_empty_raises():
    exp = Experiment(
        name="test_exp",
        factors=[Factor(name="T", type="continuous", lower_bound=10.0, upper_bound=50.0)],
        responses=[Response(name="yield", type="continuous")],
    )
    with pytest.raises(InvalidDesignMatrixError, match="empty factorial matrix"):
        combinations_to_runs([], exp)


# ---------------------------------------------------------------------------
# generate_factor_codings tests
# ---------------------------------------------------------------------------

def test_generate_factor_codings_continuous_and_categorical():
    f_cont = Factor(name="temperature", type="continuous", lower_bound=100.0, upper_bound=200.0)
    f_cat2 = Factor(name="catalyst", type="categorical", levels=["A", "B"])
    f_cat3 = Factor(name="solvent", type="categorical", levels=["S1", "S2", "S3"])
    exp = Experiment(
        name="coding_exp",
        factors=[f_cont, f_cat2, f_cat3],
        responses=[Response(name="yield", type="continuous")],
    )

    codings = generate_factor_codings(exp)
    # Continuous and 2-level categorical get codings; 3-level categorical does not get 2-level coding
    assert len(codings) == 2

    # Continuous coding verification
    temp_coding = next(c for c in codings if c.factor_ref == "temperature")
    assert temp_coding.method == "two_level"
    assert temp_coding.mapping == {"100.0": -1.0, "200.0": 1.0}
    assert temp_coding.code("100.0") == -1.0
    assert temp_coding.code(200.0) == 1.0
    assert temp_coding.code(150.0) == 0.0

    # Categorical 2-level coding verification
    cat_coding = next(c for c in codings if c.factor_ref == "catalyst")
    assert cat_coding.method == "two_level"
    assert cat_coding.mapping == {"A": -1.0, "B": 1.0}
    assert cat_coding.code("A") == -1.0
    assert cat_coding.code("B") == 1.0


# ---------------------------------------------------------------------------
# Integration with both Full and Fractional Factorial Generators
# ---------------------------------------------------------------------------

def test_full_and_fractional_generators_use_utils():
    f1 = Factor(name="A", type="continuous", lower_bound=10.0, upper_bound=20.0)
    f2 = Factor(name="B", type="continuous", lower_bound=1.0, upper_bound=5.0)
    f3 = Factor(name="C", type="continuous", lower_bound=100.0, upper_bound=200.0)
    exp = Experiment(
        name="three_factor_exp",
        factors=[f1, f2, f3],
        responses=[Response(name="yield", type="continuous")],
    )

    # 1. Full factorial generator
    full_gen = FullFactorialGenerator()
    full_design = full_gen.generate(exp)
    assert full_design.design_type == "full_factorial"
    assert len(full_design.runs) == 8  # 2^3 = 8
    assert full_design.factor_coding is not None
    assert len(full_design.factor_coding) == 3
    assert full_design.is_factor_coded("A")
    assert full_design.get_coded_value("A", 10.0) == -1.0
    assert full_design.get_coded_value("A", 20.0) == 1.0

    # 2. Fractional factorial generator (half-fraction 2^(3-1) = 4)
    frac_gen = FractionalFactorialGenerator()
    frac_design = frac_gen.generate(exp)
    assert frac_design.design_type == "fractional_factorial"
    assert len(frac_design.runs) == 4  # 2^(3-1) = 4
    assert frac_design.factor_coding is not None
    assert len(frac_design.factor_coding) == 3
    assert frac_design.is_factor_coded("B")
    assert frac_design.get_coded_value("B", 1.0) == -1.0
    assert frac_design.get_coded_value("B", 5.0) == 1.0

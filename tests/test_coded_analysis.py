import pytest
from doe.models.experiment import Experiment
from doe.models.factor import Factor
from doe.models.response import Response
from doe.models.design import Design, Run, FactorCoding
from doe.models.results import Results, ResultEntry
from doe.statistics import fit_linear_model, fit_interaction_model, fit_quadratic_model
from doe.models.exceptions import InvalidAnalysisInputError

def test_factor_coding_interpolation_and_lookup():
    # 1. Continuous two-level coding
    coding_temp = FactorCoding(
        factor_ref="temp",
        method="two_level",
        mapping={"100.0": -1.0, "200.0": 1.0}
    )
    # Direct lookup boundary values
    assert coding_temp.code("100.0") == -1.0
    assert coding_temp.code(200.0) == 1.0
    # Interpolated values
    assert coding_temp.code(150.0) == 0.0
    assert coding_temp.code(125.0) == -0.5
    # Extrapolated values
    assert coding_temp.code(250.0) == 2.0
    assert coding_temp.code(50.0) == -2.0

    # 2. Categorical two-level lookup
    coding_cat = FactorCoding(
        factor_ref="catalyst",
        method="two_level",
        mapping={"CatA": -1.0, "CatB": 1.0}
    )
    assert coding_cat.code("CatA") == -1.0
    assert coding_cat.code("CatB") == 1.0

    # Non-matching categorical lookup should raise ValueError
    with pytest.raises(ValueError, match="is not numeric and not found in the mapping"):
        coding_cat.code("CatC")

def test_linear_model_with_coded_factors():
    # Create experiment
    f_temp = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    f_press = Factor(name="pressure", type="continuous", lower_bound=1.0, upper_bound=2.0)
    r_yield = Response(name="yield", type="continuous")
    exp = Experiment(
        name="Yield Exp",
        factors=[f_temp, f_press],
        responses=[r_yield],
        experiment_id="exp_test_coded",
    )

    # Design with coding
    runs = [
        Run(run_id="run_1", factor_values={"temp": 100.0, "pressure": 1.0}, run_number=1),
        Run(run_id="run_2", factor_values={"temp": 100.0, "pressure": 2.0}, run_number=2),
        Run(run_id="run_3", factor_values={"temp": 200.0, "pressure": 1.0}, run_number=3),
        Run(run_id="run_4", factor_values={"temp": 200.0, "pressure": 2.0}, run_number=4),
    ]
    coding_temp = FactorCoding(factor_ref="temp", method="two_level", mapping={"100.0": -1.0, "200.0": 1.0})
    coding_press = FactorCoding(factor_ref="pressure", method="two_level", mapping={"1.0": -1.0, "2.0": 1.0})
    design = Design(
        experiment_ref=exp.experiment_id,
        design_type="full_factorial",
        runs=runs,
        factor_coding=[coding_temp, coding_press],
        design_id="des_test_coded",
    )

    # Yield = 50 + 10 * temp_coded + 5 * press_coded
    # temp_coded ranges [-1, 1], press_coded ranges [-1, 1]
    # yield:
    # run 1 (-1, -1) -> 50 - 10 - 5 = 35 (with non-planar noise: 35.15)
    # run 2 (-1,  1) -> 50 - 10 + 5 = 45 (with non-planar noise: 44.85)
    # run 3 ( 1, -1) -> 50 + 10 - 5 = 55 (with non-planar noise: 55.30)
    # run 4 ( 1,  1) -> 50 + 10 + 5 = 65 (with non-planar noise: 64.70)
    entries = [
        ResultEntry(run_ref="run_1", values={"yield": 35.15}),
        ResultEntry(run_ref="run_2", values={"yield": 44.85}),
        ResultEntry(run_ref="run_3", values={"yield": 55.30}),
        ResultEntry(run_ref="run_4", values={"yield": 64.70}),
    ]
    results = Results(design_ref=design.design_id, entries=entries, results_id="res_test_coded")

    # Fit linear model
    analysis = fit_linear_model(exp, design, results)
    analysis.validate()

    assert "Intercept" in analysis.coefficients
    assert "temp" in analysis.coefficients
    assert "pressure" in analysis.coefficients

    # Expect coefficients to be in coded units:
    # Intercept ~ 50.0
    # temp ~ 10.0
    # pressure ~ 4.775 (due to non-planar noise added)
    assert abs(analysis.coefficients["Intercept"] - 50.0) < 0.1
    assert abs(analysis.coefficients["temp"] - 10.0) < 0.1
    assert abs(analysis.coefficients["pressure"] - 4.775) < 0.1

def test_interaction_model_with_coded_factors():
    f_temp = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    f_press = Factor(name="pressure", type="continuous", lower_bound=1.0, upper_bound=2.0)
    r_yield = Response(name="yield", type="continuous")
    exp = Experiment(
        name="Yield Exp",
        factors=[f_temp, f_press],
        responses=[r_yield],
        experiment_id="exp_test_coded_int",
    )

    # 4 runs + 1 replicate center point to allow interaction and residual degrees of freedom
    # interaction model has 4 terms (Intercept, temp, pressure, temp:pressure).
    # N must be > 4 (at least 5 observations) to fit interaction model.
    runs = [
        Run(run_id="run_1", factor_values={"temp": 100.0, "pressure": 1.0}, run_number=1),
        Run(run_id="run_2", factor_values={"temp": 100.0, "pressure": 2.0}, run_number=2),
        Run(run_id="run_3", factor_values={"temp": 200.0, "pressure": 1.0}, run_number=3),
        Run(run_id="run_4", factor_values={"temp": 200.0, "pressure": 2.0}, run_number=4),
        Run(run_id="run_5", factor_values={"temp": 150.0, "pressure": 1.5}, run_number=5),
        Run(run_id="run_6", factor_values={"temp": 150.0, "pressure": 1.5}, run_number=6),
    ]
    coding_temp = FactorCoding(factor_ref="temp", method="two_level", mapping={"100.0": -1.0, "200.0": 1.0})
    coding_press = FactorCoding(factor_ref="pressure", method="two_level", mapping={"1.0": -1.0, "2.0": 1.0})
    design = Design(
        experiment_ref=exp.experiment_id,
        design_type="custom",
        runs=runs,
        factor_coding=[coding_temp, coding_press],
        design_id="des_test_coded_int",
    )

    # yield = 50 + 10*temp_coded + 5*press_coded + 2*(temp_coded * press_coded) + noise
    # run 1 (-1, -1) -> 50 - 10 - 5 + 2 = 37 (with noise: 37.1)
    # run 2 (-1,  1) -> 50 - 10 + 5 - 2 = 43 (with noise: 42.9)
    # run 3 ( 1, -1) -> 50 + 10 - 5 - 2 = 53 (with noise: 52.8)
    # run 4 ( 1,  1) -> 50 + 10 + 5 + 2 = 67 (with noise: 67.2)
    # run 5 ( 0,  0) -> 50 + 0 + 0 + 0 = 50 (with noise: 50.1)
    # run 6 ( 0,  0) -> 50 + 0 + 0 + 0 = 50 (with noise: 49.9)
    entries = [
        ResultEntry(run_ref="run_1", values={"yield": 37.1}),
        ResultEntry(run_ref="run_2", values={"yield": 42.9}),
        ResultEntry(run_ref="run_3", values={"yield": 52.8}),
        ResultEntry(run_ref="run_4", values={"yield": 67.2}),
        ResultEntry(run_ref="run_5", values={"yield": 50.1}),
        ResultEntry(run_ref="run_6", values={"yield": 49.9}),
    ]
    results = Results(design_ref=design.design_id, entries=entries, results_id="res_test_coded_int")

    analysis = fit_interaction_model(exp, design, results)
    analysis.validate()

    assert "Intercept" in analysis.coefficients
    assert "temp" in analysis.coefficients
    assert "pressure" in analysis.coefficients
    assert "temp:pressure" in analysis.coefficients

    # Expect coefficients:
    assert abs(analysis.coefficients["Intercept"] - 50.0) < 0.5
    assert abs(analysis.coefficients["temp"] - 10.0) < 0.5
    assert abs(analysis.coefficients["pressure"] - 5.0) < 0.5
    assert abs(analysis.coefficients["temp:pressure"] - 2.0) < 0.5

def test_quadratic_model_with_coded_factors():
    f_temp = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    r_yield = Response(name="yield", type="continuous")
    exp = Experiment(
        name="Yield Exp",
        factors=[f_temp],
        responses=[r_yield],
        experiment_id="exp_test_coded_quad",
    )

    # For a quadratic model (Intercept, temp, temp^2), we have p=3 parameters.
    # We need at least 4 runs to estimate it with degrees of freedom.
    # The levels must contain at least 3 distinct values (e.g. 100, 150, 200).
    runs = [
        Run(run_id="run_1", factor_values={"temp": 100.0}, run_number=1),
        Run(run_id="run_2", factor_values={"temp": 150.0}, run_number=2),
        Run(run_id="run_3", factor_values={"temp": 200.0}, run_number=3),
        Run(run_id="run_4", factor_values={"temp": 150.0}, run_number=4), # replicate
        Run(run_id="run_5", factor_values={"temp": 200.0}, run_number=5), # replicate
    ]
    coding_temp = FactorCoding(factor_ref="temp", method="two_level", mapping={"100.0": -1.0, "200.0": 1.0})
    design = Design(
        experiment_ref=exp.experiment_id,
        design_type="custom",
        runs=runs,
        factor_coding=[coding_temp],
        design_id="des_test_coded_quad",
    )

    # yield = 50 + 10*temp_coded - 4*temp_coded^2 + noise
    # run 1 (-1) -> 50 - 10 - 4 = 36 (with noise: 36.1)
    # run 2 ( 0) -> 50 - 0 - 0 = 50 (with noise: 49.9)
    # run 3 ( 1) -> 50 + 10 - 4 = 56 (with noise: 56.2)
    # run 4 ( 0) -> 50 - 0 - 0 = 50 (with noise: 50.1)
    # run 5 ( 1) -> 50 + 10 - 4 = 56 (with noise: 55.8)
    entries = [
        ResultEntry(run_ref="run_1", values={"yield": 36.1}),
        ResultEntry(run_ref="run_2", values={"yield": 49.9}),
        ResultEntry(run_ref="run_3", values={"yield": 56.2}),
        ResultEntry(run_ref="run_4", values={"yield": 50.1}),
        ResultEntry(run_ref="run_5", values={"yield": 55.8}),
    ]
    results = Results(design_ref=design.design_id, entries=entries, results_id="res_test_coded_quad")

    analysis = fit_quadratic_model(exp, design, results)
    analysis.validate()

    assert "Intercept" in analysis.coefficients
    assert "temp" in analysis.coefficients
    assert "temp^2" in analysis.coefficients

    # Expect coefficients:
    assert abs(analysis.coefficients["Intercept"] - 50.0) < 0.5
    assert abs(analysis.coefficients["temp"] - 10.0) < 0.5
    assert abs(analysis.coefficients["temp^2"] - (-4.0)) < 0.5

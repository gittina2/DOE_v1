import pytest
from doe.models.experiment import Experiment
from doe.models.factor import Factor
from doe.models.response import Response
from doe.models.design import Design, Run
from doe.models.results import Results, ResultEntry
from doe.statistics import fit_linear_model
from doe.models.exceptions import (
    InsufficientObservationsError,
    NonEstimableModelError,
    InvalidAnalysisInputError,
)


def create_sample_experiment_and_design():
    f_temp = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    f_press = Factor(name="pressure", type="continuous", lower_bound=1.0, upper_bound=2.0)
    r_yield = Response(name="yield", type="continuous")
    exp = Experiment(
        name="Yield Exp",
        factors=[f_temp, f_press],
        responses=[r_yield],
        experiment_id="exp_test_001",
    )
    exp.validate()

    runs = [
        Run(run_id="run_1", factor_values={"temp": 100.0, "pressure": 1.0}, run_number=1),
        Run(run_id="run_2", factor_values={"temp": 100.0, "pressure": 2.0}, run_number=2),
        Run(run_id="run_3", factor_values={"temp": 200.0, "pressure": 1.0}, run_number=3),
        Run(run_id="run_4", factor_values={"temp": 200.0, "pressure": 2.0}, run_number=4),
    ]
    design = Design(
        experiment_ref=exp.experiment_id,
        design_type="full_factorial",
        runs=runs,
        design_id="des_test_001",
    )
    design.validate(exp)

    return exp, design


def test_fit_linear_model_benchmark():
    exp, design = create_sample_experiment_and_design()

    # True model: yield = 30 + 0.2 * temp + noise
    # Add non-planar noise so SSE > 0 and MS_res > 0
    entries = [
        ResultEntry(run_ref="run_1", values={"yield": 50.15}),
        ResultEntry(run_ref="run_2", values={"yield": 49.85}),
        ResultEntry(run_ref="run_3", values={"yield": 70.30}),
        ResultEntry(run_ref="run_4", values={"yield": 69.70}),
    ]
    results = Results(design_ref=design.design_id, entries=entries, results_id="res_test_001")
    results.validate()

    analysis = fit_linear_model(exp, design, results)
    analysis.validate()

    assert analysis.experiment_ref == exp.experiment_id
    assert analysis.design_ref == design.design_id
    assert analysis.results_ref == results.results_id
    assert analysis.model_type == "linear"

    assert abs(analysis.coefficients["Intercept"] - 30.675) < 0.01
    assert abs(analysis.coefficients["temp"] - 0.2) < 0.01

    assert analysis.r_squared > 0.99
    assert len(analysis.residuals) == 4
    assert len(analysis.anova_table) == 3

    model_row = next(row for row in analysis.anova_table if row["source"] == "Model")
    assert model_row["df"] == 2
    assert model_row["f_value"] is not None


def test_fit_linear_model_insufficient_observations():
    exp, design = create_sample_experiment_and_design()

    # Only 2 observations for 3 parameters (Intercept, temp, pressure) -> N=2 <= p=3
    entries = [
        ResultEntry(run_ref="run_1", values={"yield": 50.0}),
        ResultEntry(run_ref="run_3", values={"yield": 70.0}),
    ]
    results = Results(design_ref=design.design_id, entries=entries, results_id="res_test_001")

    with pytest.raises(InsufficientObservationsError, match="Insufficient observations"):
        fit_linear_model(exp, design, results)


def test_fit_linear_model_singular_matrix():
    f_temp = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    f_press = Factor(name="pressure", type="continuous", lower_bound=1.0, upper_bound=2.0)
    r_yield = Response(name="yield", type="continuous")
    exp = Experiment(
        name="Yield Exp",
        factors=[f_temp, f_press],
        responses=[r_yield],
        experiment_id="exp_test_002",
    )

    # Collinear columns: pressure is identical to temp / 100
    runs = [
        Run(run_id="run_1", factor_values={"temp": 100.0, "pressure": 1.0}, run_number=1),
        Run(run_id="run_2", factor_values={"temp": 100.0, "pressure": 1.0}, run_number=2),
        Run(run_id="run_3", factor_values={"temp": 200.0, "pressure": 2.0}, run_number=3),
        Run(run_id="run_4", factor_values={"temp": 200.0, "pressure": 2.0}, run_number=4),
    ]
    design = Design(
        experiment_ref=exp.experiment_id,
        design_type="full_factorial",
        runs=runs,
        design_id="des_test_002",
    )
    entries = [
        ResultEntry(run_ref="run_1", values={"yield": 50.0}),
        ResultEntry(run_ref="run_2", values={"yield": 51.0}),
        ResultEntry(run_ref="run_3", values={"yield": 70.0}),
        ResultEntry(run_ref="run_4", values={"yield": 71.0}),
    ]
    results = Results(design_ref=design.design_id, entries=entries, results_id="res_test_002")

    with pytest.raises(NonEstimableModelError, match="singular or rank-deficient"):
        fit_linear_model(exp, design, results)


def test_fit_linear_model_categorical_factor():
    f_cat = Factor(name="catalyst", type="categorical", levels=["CatA", "CatB"])
    f_press = Factor(name="pressure", type="continuous", lower_bound=1.0, upper_bound=2.0)
    r_yield = Response(name="yield", type="continuous")
    exp = Experiment(
        name="Cat Exp",
        factors=[f_cat, f_press],
        responses=[r_yield],
        experiment_id="exp_cat_001",
    )

    runs = [
        Run(run_id="run_1", factor_values={"catalyst": "CatA", "pressure": 1.0}, run_number=1),
        Run(run_id="run_2", factor_values={"catalyst": "CatA", "pressure": 2.0}, run_number=2),
        Run(run_id="run_3", factor_values={"catalyst": "CatB", "pressure": 1.0}, run_number=3),
        Run(run_id="run_4", factor_values={"catalyst": "CatB", "pressure": 2.0}, run_number=4),
    ]
    design = Design(
        experiment_ref=exp.experiment_id,
        design_type="full_factorial",
        runs=runs,
        design_id="des_cat_001",
    )
    entries = [
        ResultEntry(run_ref="run_1", values={"yield": 80.1}),
        ResultEntry(run_ref="run_2", values={"yield": 81.9}),
        ResultEntry(run_ref="run_3", values={"yield": 90.1}),
        ResultEntry(run_ref="run_4", values={"yield": 91.9}),
    ]
    results = Results(design_ref=design.design_id, entries=entries, results_id="res_cat_001")

    analysis = fit_linear_model(exp, design, results)
    analysis.validate()

    assert "Intercept" in analysis.coefficients
    assert "catalyst_CatB" in analysis.coefficients
    assert "pressure" in analysis.coefficients
    assert abs(analysis.coefficients["catalyst_CatB"] - 10.0) < 0.1

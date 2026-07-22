import pytest
from doe.models.analysis import Analysis
from doe.models.exceptions import DomainValidationError


def test_analysis_valid():
    analysis = Analysis(
        experiment_ref="exp_001",
        design_ref="des_001",
        results_ref="res_001",
        model_type="linear",
        coefficients={"Intercept": 10.0, "temp": 2.5},
        anova_table=[
            {"source": "Model", "ss": 100.0, "df": 1, "ms": 100.0, "f_value": 20.0, "p_value": 0.001},
            {"source": "Residuals", "ss": 25.0, "df": 5, "ms": 5.0, "f_value": None, "p_value": None},
            {"source": "Total", "ss": 125.0, "df": 6, "ms": None, "f_value": None, "p_value": None},
        ],
        p_values={"Intercept": 0.0001, "temp": 0.001},
        r_squared=0.80,
        adjusted_r_squared=0.76,
        residuals=[0.5, -0.5, 0.2, -0.2, 0.0],
        metadata={"note": "OLS fit"},
    )
    analysis.validate()
    assert analysis.experiment_ref == "exp_001"
    assert analysis.design_ref == "des_001"
    assert analysis.results_ref == "res_001"
    assert analysis.r_squared == 0.80
    assert analysis.adjusted_r_squared == 0.76
    assert analysis.analysis_id.startswith("ana_")


def test_analysis_invalid_experiment_ref():
    analysis = Analysis(
        experiment_ref="",
        design_ref="des_001",
        results_ref="res_001",
    )
    with pytest.raises(DomainValidationError, match="experiment_ref must be a non-empty string"):
        analysis.validate()


def test_analysis_invalid_design_ref():
    analysis = Analysis(
        experiment_ref="exp_001",
        design_ref="",
        results_ref="res_001",
    )
    with pytest.raises(DomainValidationError, match="design_ref must be a non-empty string"):
        analysis.validate()


def test_analysis_invalid_results_ref():
    analysis = Analysis(
        experiment_ref="exp_001",
        design_ref="des_001",
        results_ref="",
    )
    with pytest.raises(DomainValidationError, match="results_ref must be a non-empty string"):
        analysis.validate()


def test_analysis_invalid_r_squared():
    analysis = Analysis(
        experiment_ref="exp_001",
        design_ref="des_001",
        results_ref="res_001",
        r_squared=1.5,
    )
    with pytest.raises(DomainValidationError, match="r_squared must be a float between 0.0 and 1.0"):
        analysis.validate()

    analysis_neg = Analysis(
        experiment_ref="exp_001",
        design_ref="des_001",
        results_ref="res_001",
        r_squared=-0.1,
    )
    with pytest.raises(DomainValidationError, match="r_squared must be a float between 0.0 and 1.0"):
        analysis_neg.validate()


def test_analysis_invalid_adjusted_r_squared():
    analysis = Analysis(
        experiment_ref="exp_001",
        design_ref="des_001",
        results_ref="res_001",
        adjusted_r_squared=2.0,
    )
    with pytest.raises(DomainValidationError, match="adjusted_r_squared must be a float between 0.0 and 1.0"):
        analysis.validate()


def test_analysis_serialization():
    analysis = Analysis(
        experiment_ref="exp_001",
        design_ref="des_001",
        results_ref="res_001",
        model_type="linear",
        coefficients={"Intercept": 5.0, "x": 1.2},
        r_squared=0.95,
        adjusted_r_squared=0.94,
        analysis_id="ana_custom123",
    )
    d = analysis.to_dict()
    restored = Analysis.from_dict(d)
    restored.validate()

    assert restored.analysis_id == "ana_custom123"
    assert restored.experiment_ref == "exp_001"
    assert restored.design_ref == "des_001"
    assert restored.results_ref == "res_001"
    assert restored.coefficients == {"Intercept": 5.0, "x": 1.2}
    assert restored.r_squared == 0.95
    assert restored.adjusted_r_squared == 0.94

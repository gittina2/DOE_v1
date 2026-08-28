import math
from typing import Any, Dict, List, Optional
from doe.models.analysis import Analysis
from doe.models.design import Design
from doe.models.experiment import Experiment
from doe.models.results import Results
from doe.models.exceptions import (
    InsufficientObservationsError,
    InvalidAnalysisInputError,
    NonEstimableModelError,
)
from doe.statistics.linear_model import (
    _matrix_transpose,
    _matrix_multiply,
    _matrix_inverse,
    _compute_t_pvalue,
    _compute_f_pvalue,
)


def fit_quadratic_model(
    experiment: Experiment,
    design: Design,
    results: Results,
    response_name: Optional[str] = None,
) -> Analysis:
    """Fit a quadratic statistical model (main effects + squared terms)."""
    experiment.validate()
    design.validate(experiment)
    results.validate()

    if response_name is None:
        if not experiment.responses:
            raise InvalidAnalysisInputError("Experiment has no responses defined.")
        response_name = experiment.responses[0].name
    else:
        if not any(r.name == response_name for r in experiment.responses):
            raise InvalidAnalysisInputError(f"Response '{response_name}' is not defined in experiment.")

    results_by_run = {entry.run_ref: entry for entry in results.entries}

    main_terms: List[str] = []
    quadratic_terms: List[str] = []

    for factor in experiment.factors:
        if design.is_factor_coded(factor.name):
            main_terms.append(factor.name)
            # Quadratic terms only apply to continuous variables
            f_type = factor.type.value if hasattr(factor.type, "value") else str(factor.type)
            if f_type == "continuous":
                quadratic_terms.append(f"{factor.name}^2")
        else:
            f_type = factor.type.value if hasattr(factor.type, "value") else str(factor.type)
            if f_type == "continuous":
                main_terms.append(factor.name)
                quadratic_terms.append(f"{factor.name}^2")
            elif f_type == "categorical":
                if not factor.levels or len(factor.levels) < 2:
                    raise InvalidAnalysisInputError(f"Categorical factor '{factor.name}' must have at least 2 levels.")
                for lvl in factor.levels[1:]:
                    main_terms.append(f"{factor.name}_{lvl}")

    terms: List[str] = ["Intercept"] + main_terms + quadratic_terms

    model_formula = f"{response_name} ~ " + " + ".join(terms[1:]) if len(terms) > 1 else f"{response_name} ~ 1"

    p = len(terms)
    X: List[List[float]] = []
    Y: List[float] = []

    for run in design.runs:
        entry = results_by_run.get(run.run_id)
        if not entry or not isinstance(entry.values, dict) or response_name not in entry.values:
            continue

        raw_y = entry.values[response_name]
        try:
            y_val = float(raw_y)
        except (ValueError, TypeError):
            raise InvalidAnalysisInputError(f"Invalid numerical response value for '{response_name}': {raw_y}")

        main_vals: Dict[str, float] = {}
        for factor in experiment.factors:
            val = run.factor_values.get(factor.name)
            if design.is_factor_coded(factor.name):
                try:
                    main_vals[factor.name] = design.get_coded_value(factor.name, val)
                except Exception as e:
                    raise InvalidAnalysisInputError(
                        f"Failed to code value '{val}' for factor '{factor.name}': {e}"
                    )
            else:
                f_type = factor.type.value if hasattr(factor.type, "value") else str(factor.type)
                if f_type == "continuous":
                    main_vals[factor.name] = float(val)
                elif f_type == "categorical":
                    for lvl in factor.levels[1:]:
                        main_vals[f"{factor.name}_{lvl}"] = 1.0 if str(val) == str(lvl) else 0.0

        row: List[float] = [1.0]
        # Main effects
        for term in main_terms:
            row.append(main_vals[term])
        # Quadratic terms
        for q_term in quadratic_terms:
            base_name = q_term.rstrip("^2")
            row.append(main_vals[base_name] ** 2)

        X.append(row)
        Y.append(y_val)

    N = len(Y)
    if N <= p:
        raise InsufficientObservationsError(
            f"Insufficient observations (N={N}) for quadratic model with p={p} parameters."
        )

    XT = _matrix_transpose(X)
    XTX = _matrix_multiply(XT, X)

    try:
        inv_XTX = _matrix_inverse(XTX)
    except NonEstimableModelError:
        raise NonEstimableModelError(
            "Design matrix X^T X is singular or rank-deficient for quadratic model. "
            "Ensure factors have at least 3 distinct levels to estimate quadratic terms."
        )
    except Exception as err:
        raise NonEstimableModelError(f"Failed to invert X^T X matrix for quadratic model: {err}")

    Y_mat = [[y] for y in Y]
    XTY = _matrix_multiply(XT, Y_mat)
    beta_mat = _matrix_multiply(inv_XTX, XTY)
    beta = [beta_mat[j][0] for j in range(p)]

    Y_hat_mat = _matrix_multiply(X, beta_mat)
    Y_hat = [Y_hat_mat[i][0] for i in range(N)]
    residuals = [Y[i] - Y_hat[i] for i in range(N)]

    mean_Y = sum(Y) / N
    SST = sum((y - mean_Y) ** 2 for y in Y)
    SSE = sum(e ** 2 for e in residuals)
    SSR = max(0.0, SST - SSE)

    df_model = p - 1
    df_res = N - p
    df_total = N - 1

    ms_model = SSR / df_model if df_model > 0 else 0.0
    ms_res = SSE / df_res if df_res > 0 else 0.0

    f_value = ms_model / ms_res if (ms_res > 1e-12 and df_model > 0) else None

    if SST > 1e-12:
        r_squared = max(0.0, min(1.0, 1.0 - (SSE / SST)))
    else:
        r_squared = 1.0

    if df_res > 0 and df_total > 0 and SST > 1e-12:
        adj_r2 = 1.0 - ((SSE / df_res) / (SST / df_total))
        adj_r2 = max(0.0, min(1.0, adj_r2))
    else:
        adj_r2 = r_squared

    s2 = ms_res
    coefficients: Dict[str, float] = {}
    p_values: Dict[str, float] = {}

    for j in range(p):
        term = terms[j]
        b_val = beta[j]
        coefficients[term] = float(round(b_val, 6))
        var_b = max(0.0, s2 * inv_XTX[j][j])
        se_b = math.sqrt(var_b)
        t_stat = b_val / se_b if se_b > 1e-12 else 0.0
        p_val = _compute_t_pvalue(t_stat, df_res)
        p_values[term] = float(round(p_val, 6))

    f_pvalue = _compute_f_pvalue(f_value, df_model, df_res) if f_value is not None else None

    anova_table = [
        {
            "source": "Model",
            "ss": float(round(SSR, 6)),
            "df": df_model,
            "ms": float(round(ms_model, 6)),
            "f_value": float(round(f_value, 6)) if f_value is not None else None,
            "p_value": float(round(f_pvalue, 6)) if f_pvalue is not None else None,
        },
        {
            "source": "Residuals",
            "ss": float(round(SSE, 6)),
            "df": df_res,
            "ms": float(round(ms_res, 6)),
            "f_value": None,
            "p_value": None,
        },
        {
            "source": "Total",
            "ss": float(round(SST, 6)),
            "df": df_total,
            "ms": None,
            "f_value": None,
            "p_value": None,
        },
    ]

    analysis = Analysis(
        experiment_ref=experiment.experiment_id,
        design_ref=design.design_id,
        results_ref=results.results_id,
        model_type="quadratic",
        formula=model_formula,
        terms=terms,
        coefficients=coefficients,
        anova_table=anova_table,
        p_values=p_values,
        r_squared=float(round(r_squared, 6)),
        adjusted_r_squared=float(round(adj_r2, 6)),
        residuals=[float(round(r, 6)) for r in residuals],
        diagnostics={
            "response_variable": response_name,
            "n_observations": N,
            "n_parameters": p,
        },
    )
    analysis.validate()
    return analysis

import math
from typing import Any, Dict, List, Optional
from doe.models.analysis import Analysis
from doe.models.design import Design
from doe.models.experiment import Experiment
from doe.models.factor import FactorType
from doe.models.results import Results
from doe.models.workflow_state import WorkflowState
from doe.models.exceptions import (
    InconsistentReferenceError,
    InsufficientObservationsError,
    InvalidAnalysisInputError,
    NonEstimableModelError,
    WorkflowStateMismatchError,
)

try:
    import scipy.stats as stats

    def _compute_t_pvalue(t_stat: float, df: int) -> float:
        if df <= 0:
            return 1.0
        return float(2 * (1 - stats.t.cdf(abs(t_stat), df)))

    def _compute_f_pvalue(f_stat: float, df1: int, df2: int) -> Optional[float]:
        if df1 <= 0 or df2 <= 0 or f_stat is None:
            return None
        return float(1 - stats.f.cdf(f_stat, df1, df2))

except ImportError:

    def _compute_t_pvalue(t_stat: float, df: int) -> float:
        if df <= 0:
            return 1.0
        z = abs(t_stat)
        p = 1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2)))
        return float(2 * p)

    def _compute_f_pvalue(f_stat: float, df1: int, df2: int) -> Optional[float]:
        if df1 <= 0 or df2 <= 0 or f_stat is None:
            return None
        return 0.05


def _matrix_transpose(M: List[List[float]]) -> List[List[float]]:
    rows = len(M)
    cols = len(M[0])
    return [[M[r][c] for r in range(rows)] for c in range(cols)]


def _matrix_multiply(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    rows_A = len(A)
    cols_A = len(A[0])
    rows_B = len(B)
    cols_B = len(B[0])
    if cols_A != rows_B:
        raise ValueError("Cannot multiply matrices with incompatible shapes.")
    result = [[0.0] * cols_B for _ in range(rows_A)]
    for i in range(rows_A):
        for k in range(cols_A):
            if A[i][k] == 0:
                continue
            for j in range(cols_B):
                result[i][j] += A[i][k] * B[k][j]
    return result


def _matrix_inverse(M: List[List[float]]) -> List[List[float]]:
    n = len(M)
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(M)]

    for i in range(n):
        max_row = i
        max_val = abs(aug[i][i])
        for k in range(i + 1, n):
            if abs(aug[k][i]) > max_val:
                max_val = abs(aug[k][i])
                max_row = k
        if max_val < 1e-10:
            raise NonEstimableModelError("Design matrix X^T X is singular or rank-deficient.")

        if max_row != i:
            aug[i], aug[max_row] = aug[max_row], aug[i]

        pivot = aug[i][i]
        for j in range(2 * n):
            aug[i][j] /= pivot

        for k in range(n):
            if k != i:
                factor = aug[k][i]
                if factor != 0:
                    for j in range(2 * n):
                        aug[k][j] -= factor * aug[i][j]

    return [row[n:] for row in aug]


def fit_linear_model(
    experiment: Experiment,
    design: Design,
    results: Results,
    response_name: Optional[str] = None,
) -> Analysis:
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

    terms: List[str] = ["Intercept"]
    for factor in experiment.factors:
        f_type = factor.type.value if hasattr(factor.type, "value") else str(factor.type)
        if f_type == "continuous":
            terms.append(factor.name)
        elif f_type == "categorical":
            if not factor.levels or len(factor.levels) < 2:
                raise InvalidAnalysisInputError(f"Categorical factor '{factor.name}' must have at least 2 levels.")
            for lvl in factor.levels[1:]:
                terms.append(f"{factor.name}_{lvl}")
        else:
            raise InvalidAnalysisInputError(f"Unsupported factor type '{f_type}'.")

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
            raise InvalidAnalysisInputError(
                f"Invalid numerical response value for '{response_name}': {raw_y}"
            )

        row: List[float] = [1.0]
        for factor in experiment.factors:
            f_type = factor.type.value if hasattr(factor.type, "value") else str(factor.type)
            val = run.factor_values.get(factor.name)
            if f_type == "continuous":
                try:
                    row.append(float(val))
                except (ValueError, TypeError):
                    raise InvalidAnalysisInputError(
                        f"Invalid continuous factor value for '{factor.name}': {val}"
                    )
            elif f_type == "categorical":
                for lvl in factor.levels[1:]:
                    row.append(1.0 if str(val) == str(lvl) else 0.0)

        X.append(row)
        Y.append(y_val)

    N = len(Y)
    if N <= p:
        raise InsufficientObservationsError(
            f"Insufficient observations (N={N}) for linear model with p={p} parameters."
        )

    XT = _matrix_transpose(X)
    XTX = _matrix_multiply(XT, X)

    try:
        inv_XTX = _matrix_inverse(XTX)
    except NonEstimableModelError:
        raise
    except Exception as err:
        raise NonEstimableModelError(f"Failed to invert X^T X matrix: {err}")

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
            "df": float(round(SST, 6)) if False else df_total, # df_total
            "ms": None,
            "f_value": None,
            "p_value": None,
        },
    ]

    analysis = Analysis(
        experiment_ref=experiment.experiment_id,
        design_ref=design.design_id,
        results_ref=results.results_id,
        model_type="linear",
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


def analyze_experiment(state: WorkflowState) -> WorkflowState:
    state.validate()

    if state.step != "results_complete":
        raise WorkflowStateMismatchError(
            f"Cannot run analysis from step '{state.step}'. Step must be 'results_complete'."
        )

    if state.experiment is None or state.design is None or state.results is None:
        raise WorkflowStateMismatchError(
            "For analysis computation, experiment, design, and results must all be defined."
        )

    if state.design.experiment_ref != state.experiment.experiment_id:
        raise InconsistentReferenceError(
            f"Design experiment_ref '{state.design.experiment_ref}' does not match Experiment id '{state.experiment.experiment_id}'."
        )

    if state.results.design_ref != state.design.design_id:
        raise InconsistentReferenceError(
            f"Results design_ref '{state.results.design_ref}' does not match Design id '{state.design.design_id}'."
        )

    analysis_obj = fit_linear_model(state.experiment, state.design, state.results)

    new_state = state.transition_to(
        "analysis_created",
        analysis=analysis_obj,
        audit={"analysis_id": analysis_obj.analysis_id},
    )

    return new_state

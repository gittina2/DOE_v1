import os
from typing import Optional
from doe.models.workflow_state import WorkflowState
from doe.models.exceptions import (
    DomainValidationError,
    WorkflowStateMismatchError,
)


def format_markdown_report(state: WorkflowState) -> str:
    state.validate()

    if state.experiment is None:
        raise WorkflowStateMismatchError("Cannot generate report without an experiment defined.")

    exp = state.experiment
    lines = []

    # Title & Experiment Overview
    lines.append(f"# Experiment Report: {exp.name}")
    lines.append("")
    lines.append("## Experiment Overview")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| **Experiment ID** | {exp.experiment_id} |")
    lines.append(f"| **Name** | {exp.name} |")
    lines.append(f"| **Design Type** | {exp.design_type} |")
    lines.append(f"| **Description** | {exp.description or 'N/A'} |")
    lines.append(f"| **Schema Version** | {exp.schema_version} |")
    lines.append(f"| **Current Workflow Step** | {state.step} |")
    lines.append("")

    # Factors & Responses
    lines.append("## Factors & Responses")
    lines.append("")
    lines.append("### Experimental Factors")
    lines.append("")
    lines.append("| Factor Name | Type | Unit | Bounds / Levels |")
    lines.append("| --- | --- | --- | --- |")
    for f in exp.factors:
        f_type = f.type.value if hasattr(f.type, "value") else str(f.type)
        if f_type == "continuous":
            bounds = f"[{f.lower_bound}, {f.upper_bound}]"
        elif f_type == "categorical":
            bounds = ", ".join(str(lvl) for lvl in (f.levels or []))
        else:
            bounds = "N/A"
        lines.append(f"| {f.name} | {f_type} | {f.unit or 'N/A'} | {bounds} |")
    lines.append("")

    lines.append("### Response Variables")
    lines.append("")
    lines.append("| Response Name | Type | Unit |")
    lines.append("| --- | --- | --- |")
    for r in exp.responses:
        r_type = r.type.value if hasattr(r.type, "value") else str(r.type)
        lines.append(f"| {r.name} | {r_type} | {r.unit or 'N/A'} |")
    lines.append("")

    # Design Matrix (if present)
    if state.design is not None:
        design = state.design
        lines.append("## Experimental Design")
        lines.append("")
        lines.append(f"- **Design ID**: {design.design_id}")
        lines.append(f"- **Design Type**: {design.design_type}")
        lines.append(f"- **Total Runs**: {len(design.runs)}")
        lines.append(f"- **Randomization**: {design.randomization}")
        lines.append("")

        factor_names = [f.name for f in exp.factors]
        headers = ["Run ID", "Run Number"] + factor_names
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for run in design.runs:
            row_vals = [run.run_id, str(run.run_number)]
            for fname in factor_names:
                row_vals.append(str(run.factor_values.get(fname, "N/A")))
            lines.append("| " + " | ".join(row_vals) + " |")
        lines.append("")

    # Results (if present)
    if state.results is not None:
        results = state.results
        lines.append("## Experimental Results")
        lines.append("")
        lines.append(f"- **Results ID**: {results.results_id}")
        lines.append(f"- **Completeness**: {results.completeness}")
        lines.append(f"- **Recorded Entries**: {len(results.entries)}")
        lines.append("")

        response_names = [r.name for r in exp.responses]
        headers = ["Run Reference"] + response_names + ["Status"]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for entry in results.entries:
            row_vals = [entry.run_ref]
            for rname in response_names:
                val = entry.values.get(rname, "N/A") if isinstance(entry.values, dict) else "N/A"
                row_vals.append(str(val))
            row_vals.append(entry.status)
            lines.append("| " + " | ".join(row_vals) + " |")
        lines.append("")

    # Statistical Analysis (if present)
    if state.analysis is not None:
        analysis = state.analysis
        lines.append("## Statistical Analysis")
        lines.append("")
        lines.append(f"- **Analysis ID**: {analysis.analysis_id}")
        lines.append(f"- **Model Type**: {analysis.model_type}")
        lines.append(f"- **R²**: {analysis.r_squared if analysis.r_squared is not None else 'N/A'}")
        lines.append(f"- **Adjusted R²**: {analysis.adjusted_r_squared if analysis.adjusted_r_squared is not None else 'N/A'}")
        lines.append("")

        if analysis.coefficients:
            lines.append("### Coefficients")
            lines.append("")
            lines.append("| Term | Estimate | P-Value |")
            lines.append("| --- | --- | --- |")
            for term, est in analysis.coefficients.items():
                p_val = analysis.p_values.get(term, "N/A") if analysis.p_values else "N/A"
                lines.append(f"| {term} | {est} | {p_val} |")
            lines.append("")

        if analysis.anova_table:
            lines.append("### ANOVA Table")
            lines.append("")
            lines.append("| Source | Sum of Squares (SS) | DF | Mean Square (MS) | F-Value | P-Value |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for row in analysis.anova_table:
                ss = row.get("ss", "N/A")
                df = row.get("df", "N/A")
                ms = row.get("ms", "N/A") if row.get("ms") is not None else "N/A"
                f_val = row.get("f_value", "N/A") if row.get("f_value") is not None else "N/A"
                p_val = row.get("p_value", "N/A") if row.get("p_value") is not None else "N/A"
                lines.append(f"| {row.get('source', '')} | {ss} | {df} | {ms} | {f_val} | {p_val} |")
            lines.append("")

    return "\n".join(lines)


def generate_report(
    state: WorkflowState,
    output_path: Optional[str] = None,
    format: str = "markdown",
) -> WorkflowState:
    state.validate()

    if format.lower() != "markdown":
        raise DomainValidationError(f"Unsupported report format: '{format}'. Supported format is 'markdown'.")

    report_content = format_markdown_report(state)

    if output_path:
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(output_path, mode="w", encoding="utf-8") as f:
            f.write(report_content)

    new_state = state.transition_to(
        "report_generated",
        audit={
            "report_format": format,
            "output_path": output_path,
        },
    )

    return new_state

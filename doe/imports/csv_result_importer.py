import csv
import io
from typing import Any, Dict, List, Optional, Union

from doe.models.design import Design
from doe.models.exceptions import CsvHeaderError, CsvRowImportError
from doe.models.response import Response
from doe.models.results import ResultEntry


def import_results_from_csv(
    source: Union[str, io.TextIOBase],
    design: Optional[Design] = None,
    responses: Optional[List[Response]] = None,
) -> List[ResultEntry]:
    """Imports result entries from a CSV file or file-like object.

    Expected CSV header must include a run reference column ('run_id' or 'run_ref')
    and column headers for defined response variables.

    Raises:
        CsvHeaderError: If header is missing required run reference column.
        CsvRowImportError: If a specific cell value cannot be converted or validated.
    """
    if isinstance(source, str):
        with open(source, mode="r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = source.readlines()

    if not lines:
        raise CsvHeaderError("CSV file is empty.")

    reader = csv.reader([line for line in lines if line.strip()])
    try:
        header = next(reader)
    except StopIteration:
        raise CsvHeaderError("CSV file contains no header line.")

    header_clean = [col.strip() for col in header]

    run_ref_col_name = None
    for candidate in ("run_id", "run_ref", "run_number", "run_num"):
        if candidate in header_clean:
            run_ref_col_name = candidate
            break

    if run_ref_col_name is None:
        raise CsvHeaderError(
            "CSV header must contain a run reference column ('run_id', 'run_ref', 'run_number', or 'run_num')."
        )

    run_ref_idx = header_clean.index(run_ref_col_name)

    # Determine response columns
    response_names = [r.name for r in responses] if responses else []
    
    # Identify response indices
    response_indices: Dict[str, int] = {}
    for idx, col in enumerate(header_clean):
        if idx == run_ref_idx:
            continue
        if response_names:
            if col in response_names:
                response_indices[col] = idx
        else:
            response_indices[col] = idx

    if not response_indices:
        raise CsvHeaderError("CSV header contains no valid response columns.")

    # Build run maps if design is provided
    run_id_map: Dict[str, str] = {}
    run_num_map: Dict[str, str] = {}
    if design:
        for run in design.runs:
            run_id_map[run.run_id] = run.run_id
            if run.run_number is not None:
                run_num_map[str(run.run_number)] = run.run_id

    entries: List[ResultEntry] = []
    line_num = 1  # Header was line 1

    for row in reader:
        line_num += 1
        if not row or not any(cell.strip() for cell in row):
            continue

        if len(row) <= run_ref_idx:
            raise CsvRowImportError(
                row_number=line_num,
                field_name=run_ref_col_name,
                invalid_value="",
                message=f"Row {line_num} is missing run reference column value.",
            )

        run_ref_val = row[run_ref_idx].strip()
        if not run_ref_val:
            raise CsvRowImportError(
                row_number=line_num,
                field_name=run_ref_col_name,
                invalid_value="",
                message=f"Row {line_num} has an empty run reference value.",
            )

        resolved_run_id = run_ref_val
        if design:
            if run_ref_val in run_id_map:
                resolved_run_id = run_id_map[run_ref_val]
            elif run_ref_val in run_num_map:
                resolved_run_id = run_num_map[run_ref_val]
            else:
                raise CsvRowImportError(
                    row_number=line_num,
                    field_name=run_ref_col_name,
                    invalid_value=run_ref_val,
                    message=f"Row {line_num}: Unknown run reference '{run_ref_val}'.",
                )


        values: Dict[str, Any] = {}
        for resp_name, resp_idx in response_indices.items():
            if resp_idx >= len(row):
                raise CsvRowImportError(
                    row_number=line_num,
                    field_name=resp_name,
                    invalid_value="",
                    message=f"Row {line_num} is missing value for response '{resp_name}'.",
                )
            cell_val = row[resp_idx].strip()
            if not cell_val:
                raise CsvRowImportError(
                    row_number=line_num,
                    field_name=resp_name,
                    invalid_value="",
                    message=f"Row {line_num} has empty value for response '{resp_name}'.",
                )
            try:
                numeric_val = float(cell_val)
                # Keep int if exact int representation
                if numeric_val.is_integer():
                    numeric_val = int(numeric_val)
                values[resp_name] = numeric_val
            except ValueError:
                raise CsvRowImportError(
                    row_number=line_num,
                    field_name=resp_name,
                    invalid_value=cell_val,
                    message=f"Row {line_num}, Field '{resp_name}' invalid value: '{cell_val}' (expected numeric).",
                )

        entry = ResultEntry(run_ref=resolved_run_id, values=values, status="complete")
        entries.append(entry)

    return entries


import csv
import json
import os
from typing import List, Dict, Any, Optional
from doe.models import (
    Factor,
    DomainValidationError,
    InvalidFactorTypeError,
    InvalidFactorBoundsError,
    MissingFactorLevelsError,
    DuplicateFactorLevelsError,
    CsvHeaderError,
    CsvFormatError,
    CsvRowImportError,
)

def parse_level_value(val: str) -> Any:
    # Try int
    try:
        return int(val)
    except ValueError:
        pass
    # Try float
    try:
        return float(val)
    except ValueError:
        pass
    # Keep as str
    return val


def parse_factors_csv_string(csv_content: str) -> List[Dict[str, Any]]:
    if not csv_content.strip():
        raise CsvHeaderError("CSV content is empty.")
        
    lines = csv_content.splitlines()
    reader = csv.reader(lines)
    
    try:
        headers = next(reader)
    except StopIteration:
        raise CsvHeaderError("CSV is empty or missing headers.")
        
    headers = [h.strip() for h in headers]
    if not headers or all(h == "" for h in headers):
        raise CsvHeaderError("CSV header is empty.")
        
    required_cols = {"name", "type"}
    missing = required_cols - set(headers)
    if missing:
        raise CsvHeaderError(f"Missing required columns in CSV header: {', '.join(missing)}")
        
    parsed_rows = []
    for line_idx, row in enumerate(reader, start=2):
        # Skip completely empty lines
        if not row or all(cell.strip() == "" for cell in row):
            continue
            
        if len(row) != len(headers):
            raise CsvFormatError(
                f"Row {line_idx} has {len(row)} columns, expected {len(headers)}."
            )
            
        row_dict = {headers[i]: row[i].strip() for i in range(len(headers))}
        row_dict["__row_number__"] = line_idx
        parsed_rows.append(row_dict)
        
    return parsed_rows


def parse_factors_csv(file_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(file_path):
        raise CsvFormatError(f"CSV file does not exist: {file_path}")
    try:
        with open(file_path, mode="r", encoding="utf-8", newline="") as f:
            content = f.read()
    except Exception as e:
        raise CsvFormatError(f"Failed to read CSV file: {str(e)}") from e
        
    return parse_factors_csv_string(content)


def map_rows_to_factors(rows: List[Dict[str, Any]]) -> List[Factor]:
    factors = []
    for row in rows:
        row_num = row.get("__row_number__", 0)
        name = row.get("name", "").strip()
        factor_type = row.get("type", "").strip()
        unit = row.get("unit", "").strip() or None
        
        # Parse levels
        levels_str = row.get("levels", "").strip()
        if levels_str:
            parts = levels_str.split(";")
            levels = [parse_level_value(p.strip()) for p in parts if p.strip()]
        else:
            levels = None
            
        # Parse bounds
        lower_bound_str = row.get("lower_bound", "").strip()
        if lower_bound_str:
            try:
                lower_bound = float(lower_bound_str)
            except ValueError:
                raise CsvRowImportError(
                    row_number=row_num,
                    field_name="lower_bound",
                    invalid_value=lower_bound_str,
                    message=f"Row {row_num}, Field 'lower_bound' must be numeric, got '{lower_bound_str}'"
                )
        else:
            lower_bound = None
            
        upper_bound_str = row.get("upper_bound", "").strip()
        if upper_bound_str:
            try:
                upper_bound = float(upper_bound_str)
            except ValueError:
                raise CsvRowImportError(
                    row_number=row_num,
                    field_name="upper_bound",
                    invalid_value=upper_bound_str,
                    message=f"Row {row_num}, Field 'upper_bound' must be numeric, got '{upper_bound_str}'"
                )
        else:
            upper_bound = None
            
        # Parse metadata
        metadata_str = row.get("metadata", "").strip()
        if metadata_str:
            try:
                metadata = json.loads(metadata_str)
            except Exception:
                raise CsvRowImportError(
                    row_number=row_num,
                    field_name="metadata",
                    invalid_value=metadata_str,
                    message=f"Row {row_num}, Field 'metadata' must be valid JSON, got '{metadata_str}'"
                )
        else:
            metadata = None
            
        factor = Factor(
            name=name,
            type=factor_type, # type: ignore
            unit=unit,
            levels=levels,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            metadata=metadata
        )
        
        try:
            factor.validate()
        except DomainValidationError as e:
            # Map exception type to correct field
            if isinstance(e, InvalidFactorTypeError):
                field_name = "type"
                invalid_value = factor_type
            elif isinstance(e, InvalidFactorBoundsError):
                # Distinguish which bound is invalid or missing
                if factor.lower_bound is None:
                    field_name = "lower_bound"
                    invalid_value = lower_bound_str
                elif factor.upper_bound is None:
                    field_name = "upper_bound"
                    invalid_value = upper_bound_str
                else:
                    field_name = "lower_bound"
                    invalid_value = lower_bound_str
            elif isinstance(e, (MissingFactorLevelsError, DuplicateFactorLevelsError)):
                field_name = "levels"
                invalid_value = levels_str
            else:
                field_name = "name"
                invalid_value = name
                
            raise CsvRowImportError(
                row_number=row_num,
                field_name=field_name,
                invalid_value=invalid_value,
                message=f"Row {row_num}, Field '{field_name}' validation failed: {str(e)}"
            ) from e
            
        factors.append(factor)
        
    return factors

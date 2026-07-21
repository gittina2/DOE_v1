import pytest
from doe.imports import parse_factors_csv_string, map_rows_to_factors
from doe.models import Factor, CsvRowImportError

def test_map_success_continuous():
    csv_data = "name,type,unit,lower_bound,upper_bound,metadata\ntemp,continuous,C,20.5,80.5,{\"precision\": 0.1}"
    rows = parse_factors_csv_string(csv_data)
    factors = map_rows_to_factors(rows)
    
    assert len(factors) == 1
    f = factors[0]
    assert isinstance(f, Factor)
    assert f.name == "temp"
    assert f.type == "continuous"
    assert f.unit == "C"
    assert f.lower_bound == 20.5
    assert f.upper_bound == 80.5
    assert f.metadata == {"precision": 0.1}

def test_map_success_categorical():
    csv_data = "name,type,levels\ncatalyst,categorical,A;B;3"
    rows = parse_factors_csv_string(csv_data)
    factors = map_rows_to_factors(rows)
    
    assert len(factors) == 1
    f = factors[0]
    assert f.name == "catalyst"
    assert f.type == "categorical"
    assert f.levels == ["A", "B", 3]

def test_map_invalid_bounds_type():
    # lower_bound not a float
    csv_data = "name,type,lower_bound,upper_bound\ntemp,continuous,abc,100"
    rows = parse_factors_csv_string(csv_data)
    with pytest.raises(CsvRowImportError) as exc_info:
        map_rows_to_factors(rows)
    assert exc_info.value.row_number == 2
    assert exc_info.value.field_name == "lower_bound"
    assert exc_info.value.invalid_value == "abc"

def test_map_invalid_metadata():
    csv_data = "name,type,metadata\ntemp,continuous,invalid_json"
    rows = parse_factors_csv_string(csv_data)
    with pytest.raises(CsvRowImportError) as exc_info:
        map_rows_to_factors(rows)
    assert exc_info.value.row_number == 2
    assert exc_info.value.field_name == "metadata"
    assert exc_info.value.invalid_value == "invalid_json"

def test_map_domain_bounds_validation_error():
    # continuous factor lower_bound >= upper_bound
    csv_data = "name,type,lower_bound,upper_bound\ntemp,continuous,100,50"
    rows = parse_factors_csv_string(csv_data)
    with pytest.raises(CsvRowImportError) as exc_info:
        map_rows_to_factors(rows)
    assert exc_info.value.row_number == 2
    assert exc_info.value.field_name == "lower_bound"
    assert exc_info.value.invalid_value == "100"

def test_map_domain_levels_validation_error():
    # categorical factor with duplicate levels
    csv_data = "name,type,levels\ncatalyst,categorical,A;B;A"
    rows = parse_factors_csv_string(csv_data)
    with pytest.raises(CsvRowImportError) as exc_info:
        map_rows_to_factors(rows)
    assert exc_info.value.row_number == 2
    assert exc_info.value.field_name == "levels"
    assert exc_info.value.invalid_value == "A;B;A"

def test_map_domain_type_validation_error():
    csv_data = "name,type\ntemp,invalid_type"
    rows = parse_factors_csv_string(csv_data)
    with pytest.raises(CsvRowImportError) as exc_info:
        map_rows_to_factors(rows)
    assert exc_info.value.row_number == 2
    assert exc_info.value.field_name == "type"
    assert exc_info.value.invalid_value == "invalid_type"

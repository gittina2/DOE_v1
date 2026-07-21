import pytest
from doe.imports import parse_factors_csv, parse_factors_csv_string
from doe.models import CsvHeaderError, CsvFormatError

def test_parse_valid_csv():
    content = """name,type,unit,lower_bound,upper_bound
temp,continuous,C,0,100
catalyst,categorical,,,"""
    rows = parse_factors_csv_string(content)
    assert len(rows) == 2
    assert rows[0] == {
        "name": "temp",
        "type": "continuous",
        "unit": "C",
        "lower_bound": "0",
        "upper_bound": "100",
        "__row_number__": 2
    }
    assert rows[1] == {
        "name": "catalyst",
        "type": "categorical",
        "unit": "",
        "lower_bound": "",
        "upper_bound": "",
        "__row_number__": 3
    }

def test_parse_empty_content():
    with pytest.raises(CsvHeaderError, match="content is empty"):
        parse_factors_csv_string("")
        
    with pytest.raises(CsvHeaderError, match="content is empty"):
        parse_factors_csv_string("   \n   \n")

def test_missing_required_headers():
    content = "name,unit,lower_bound\ntemp,C,0"
    with pytest.raises(CsvHeaderError, match="Missing required columns.*type"):
        parse_factors_csv_string(content)

    content2 = "type,unit,lower_bound\ncontinuous,C,0"
    with pytest.raises(CsvHeaderError, match="Missing required columns.*name"):
        parse_factors_csv_string(content2)

def test_row_length_mismatch():
    content = """name,type,unit
temp,continuous,C,extra_val
catalyst,categorical"""
    # Line 2 has 4 values instead of 3
    with pytest.raises(CsvFormatError, match="Row 2 has 4 columns, expected 3"):
        parse_factors_csv_string(content)

def test_empty_lines_ignored():
    content = """name,type

temp,continuous

catalyst,categorical
"""
    rows = parse_factors_csv_string(content)
    assert len(rows) == 2
    assert rows[0]["name"] == "temp"
    assert rows[1]["name"] == "catalyst"

def test_file_parsing_integration(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "factors.csv"
    p.write_text("name,type\ntemp,continuous", encoding="utf-8")
    
    rows = parse_factors_csv(str(p))
    assert len(rows) == 1
    assert rows[0] == {"name": "temp", "type": "continuous", "__row_number__": 2}

def test_nonexistent_file():
    with pytest.raises(CsvFormatError, match="does not exist"):
        parse_factors_csv("nonexistent_file_12345.csv")

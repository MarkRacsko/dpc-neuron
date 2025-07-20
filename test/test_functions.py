from functions.validation import validate_config, validate_metadata, validate_treatments
from classes.toml_data import Metadata
from pathlib import Path
from typing import Any
from copy import deepcopy

good_config = {
    "input": {
        "target_folder": Path("./data"),
        "method": "baseline",
        "SD_multiplier": 2,
        "smoothing_range": 5
    },
    "output": {
        "report_name": "report_",
        "summary_name": "summary"
    }
}

good_metadata_dict = {
    "conditions": {
        "ratiometric_dye": "True",
        "group1": "neuron only",
        "group2": "neuron + DPC"
    },
    "treatments": {
        "baseline": {
            "begin": 0,
            "end": 60
        },
        "CIM": {
            "begin": 60,
            "end": 300
        },
        "AITC": {
            "begin": 300,
            "end": 540
        }
    }
}

good_metadata = Metadata(good_metadata_dict)

def test_config_good():
    errors = validate_config(good_config)
    assert not errors

def test_config_missing_keys():
    bad_config: dict[str, Any] = {k: v for k, v in good_config.items()}
    del bad_config["input"]

    errors = validate_config(bad_config)
    assert "key missing" in errors

def test_config_bad_folder():
    bad_config: dict[str, Any] = {k: v for k, v in good_config.items()}
    bad_config["input"]["target_folder"] = Path("./asdasdasd")

    errors = validate_config(bad_config)
    assert "folder not found" in errors

def test_config_bad_method():
    bad_config: dict[str, Any] = {k: v for k, v in good_config.items()}
    bad_config["input"]["method"] = "asdasdasd"

    errors = validate_config(bad_config)
    assert "method value incorrect" in errors

def test_config_bad_SD_mult():
    bad_config: dict[str, Any] = {k: v for k, v in good_config.items()}
    bad_config["input"]["SD_multiplier"] = "asdasdasd"

    errors = validate_config(bad_config)
    assert "SD_multiplier value must be" in errors

def test_config_bad_smoothing_1():
    bad_config: dict[str, Any] = {k: v for k, v in good_config.items()}
    bad_config["input"]["smoothing_range"] = "asdasdasd"

    errors = validate_config(bad_config)
    assert "must be an integer number" in errors

def test_config_bad_smoothing_2():
    bad_config: dict[str, Any] = {k: v for k, v in good_config.items()}
    bad_config["input"]["smoothing_range"] = 6

    errors = validate_config(bad_config)
    assert "must not be an odd number" in errors

def test_config_bad_report():
    bad_config: dict[str, Any] = {k: v for k, v in good_config.items()}
    bad_config["output"]["report_name"] = 0

    errors = validate_config(bad_config)
    assert "must be a string" in errors

def test_config_bad_summary():
    bad_config: dict[str, Any] = {k: v for k, v in good_config.items()}
    bad_config["output"]["summary_name"] = 0

    errors = validate_config(bad_config)
    assert "must be a string" in errors

def test_treatments_good():
    passed_tests = validate_treatments(good_metadata.treatments)
    assert all(passed_tests)

def test_treatments_begin_not_int():
    bad_treatments = deepcopy(good_metadata.treatments)
    bad_treatments["baseline"].begin = "asdasdasd"

    passed_tests = validate_treatments(bad_treatments)
    assert passed_tests[0] is False

def test_treatments_begin_larger_than_end():
    bad_treatments = deepcopy(good_metadata.treatments)
    bad_treatments["baseline"].begin = 900

    passed_tests = validate_treatments(bad_treatments)
    assert passed_tests[1] is False

def test_treatments_begin_smaller_than_previous_end():
    bad_treatments = deepcopy(good_metadata.treatments)
    bad_treatments["AITC"].begin = 200

    passed_tests = validate_treatments(bad_treatments)
    assert passed_tests[2] is False

def test_metadata_missing_key():
    bad_metadata = deepcopy(good_metadata_dict)
    del bad_metadata["conditions"]

    errors = validate_metadata("test", bad_metadata)
    assert "section missing" in errors

def test_metadata_bad_ratiometric():
    bad_metadata = deepcopy(good_metadata_dict)
    bad_metadata["conditions"]["ratiometric_dye"] = "bad"

    errors = validate_metadata("test", bad_metadata)
    assert "ratiometric_dye value incorrect" in errors

def test_metadata_groups_missing():
    bad_metadata = deepcopy(good_metadata_dict)
    del bad_metadata["conditions"]["group1"]

    errors = validate_metadata("test", bad_metadata)
    assert "Group key names changed or missing" in errors

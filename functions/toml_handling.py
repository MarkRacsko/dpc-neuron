from classes.toml_data import Config, Input, Output
from classes.toml_data import Metadata, Conditions, Treatments
from dataclasses import asdict
from typing import Any

def dict_to_config(config: dict[str, dict[str, Any]]) -> Config:
    input_section = config["input"]
    input_obj = Input(input_section["target_folder"],
                      input_section["method"],
                      input_section["SD_multiplier"],
                      input_section["smoothing_range"])
    
    output_section = config["output"]
    output_obj = Output(output_section["report_name"],
                        output_section["summary_name"])
    
    return Config(input_obj, output_obj)

def config_to_dict(config: Config) -> dict[str, dict[str, Any]]:
    result = {}

    result["input"] = asdict(config.input)
    result["output"] = asdict(config.output)

    return result

def dict_to_treatments(treatments_as_dict) -> Treatments:
    treatment_obj = Treatments()

    for key, values in treatments_as_dict.items():
        treatment_obj[key] = (values["begin"], values["end"])
    
    return treatment_obj

def dict_to_metadata(metadata: dict[str, dict[str, Any]]) -> Metadata:
    conditions_section = metadata["conditions"]
    conditions_obj = Conditions(conditions_section["ratiometric_dye"],
                                conditions_section["group1"],
                                conditions_section["group2"])
    
    treatment_section = metadata["treatments"]
    treatment_obj = dict_to_treatments(treatment_section)

    return Metadata(conditions_obj, treatment_obj)

def metadata_to_dict(metadata: Metadata) -> dict[str, dict[str, Any]]:
    result = {}

    result["conditions"] = metadata.conditions
    result["treatments"] = metadata.treatments

    return result
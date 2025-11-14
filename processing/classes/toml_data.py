from __future__ import annotations
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

type TimeValue = int | str
# This is used in the _Treatment class for the begin and end values of agonist treatments. The reason it exists is that
# the way my validation and data processing functions work forces makes it so that these fields cannot be declared as
# just int or just str. (And I don't want to redesign the whole thing at this point.)

@dataclass(init=False)
class Config:
    def __init__(self, config_as_dict: dict[str, dict[str, Any]]) -> None:
        input_section = config_as_dict["input"]
        self.input = Input(Path(input_section["target_folder"]),
                        input_section["method"],
                        input_section["SD_multiplier"],
                        input_section["smoothing_range"],
                        input_section["amp_threshold"],
                        input_section["cv_threshold"],
                        input_section["correction"])
        
        output_section = config_as_dict["output"]
        self.output = Output(output_section["report_name"],
                            output_section["summary_name"])
        
    def to_dict(self) -> dict[str, dict[str, Any]]:
        result = {}

        result["input"] = asdict(self.input)
        path_as_str = str(result["input"]["target_folder"])
        result["input"]["target_folder"] = path_as_str
        result["output"] = asdict(self.output)

        return result

@dataclass
class Input:
    target_folder: Path
    method: str
    SD_multiplier: int
    smoothing_range: int
    amp_threshold: float
    cv_threshold: float
    correction: str

@dataclass
class Output:
    report_name: str
    summary_name: str

@dataclass(init=False)
class Metadata:
    def __init__(self, metadata_as_dict: dict[str, dict[str, Any]]):
        conditions_section = metadata_as_dict["conditions"]
        self.conditions = Conditions(conditions_section["ratiometric_dye"],
                                     conditions_section["framerate"],
                                    conditions_section["group1"],
                                    conditions_section["group2"])
        
        treatments_as_dict = metadata_as_dict["treatments"]
        self.treatments = Treatments()

        for key, values in treatments_as_dict.items():
            self.treatments[key] = (values["begin"], values["end"])

    def to_dict(self) -> dict[str, dict[str, Any]]:
        result = {}

        result["conditions"] = asdict(self.conditions)
        treatments = asdict(self.treatments)
        result["treatments"] = treatments["treatment_dict"]
        # this is so the metadata file will end up with the correct structure

        return result

@dataclass
class Conditions:
    ratiometric_dye: str
    framerate: int
    group1: str
    group2: str

@dataclass
class Treatments:
    treatment_dict: dict[str, _Treatment] = field(default_factory=dict)

    def __iter__(self):
        return iter(self.treatment_dict)
    
    def __len__(self) -> int:
        return len(self.treatment_dict)

    def __getitem__(self, item: str):
        return self.treatment_dict[item]
    
    def __setitem__(self, item: str, values: tuple[str, str]):
        begin, end = values
        self.treatment_dict[item] = _Treatment(begin, end)

    def __delitem__(self, item: str):
        del self.treatment_dict[item]

    def items(self):
        return self.treatment_dict.items()

    def remove_empty_values(self):
        """Checks the treatments dictionary that comes from the table in the GUI metadata editor for empty rows and 
        removes them.

        Args:
            treatments (dict[str, dict[str, int  |  str]]): The treatment dictionary mapping agonist names to a dict of 
            begin and end values.

        Raises:
            ValueError: If there is a treatment where exactly one of the begin and end values is the empty string, ie. the
            user filled only one entry.
        """
        result: dict[str, _Treatment] = {}
        for name, treatment in self.treatment_dict.items():
            begin_value, end_value = treatment.values
            if begin_value == "" and end_value == "":
                # this is an empty row, exclude it
                continue
            elif begin_value == "" or end_value == "":
                # this row has only 1 missing value, this is an error
                raise ValueError
            else:
                # this row is good
                result[name] = _Treatment(begin_value, end_value)

        self.treatment_dict = result

@dataclass
class _Treatment:
    begin: TimeValue
    end: TimeValue

    @property
    def values(self) -> tuple[TimeValue, TimeValue]:
        return (self.begin, self.end)
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class Config:
    input: Input
    output: Output

@dataclass
class Input:
    target_folder: Path
    method: str
    SD_multiplier: int
    smoothing_range: int

@dataclass
class Output:
    report_name: str
    summary_name: str

@dataclass
class Metadata:
    conditions: Conditions
    treatments: Treatments

@dataclass
class Conditions:
    ratiometric_dye: str
    group1: str
    group2: str

@dataclass
class Treatments:
    treatment_dict: dict[str, _Treatment] = field(default_factory=dict)

    def __iter__(self):
        return iter(self.treatment_dict)
    
    @property
    def length(self) -> int:
        return len(self.treatment_dict)

    def __getitem__(self, item: str):
        return self.treatment_dict[item]
    
    def __setitem__(self, item: str, values: tuple[str, str]):
        begin, end = values
        self.treatment_dict[item] = _Treatment(begin, end)

    def __delitem__(self, item: str):
        del self.treatment_dict[item]

    def remove_empty_values(self):
        """Checks the treatments dictionary that comes from the table in the GUI metadata editor for empty rows and 
        removes them.

        Args:
            treatments (dict[str, dict[str, int  |  str]]): The treatment dictionary mapping agonist names to a dict of 
            begin and end values.

        Raises:
            ValueError: If there is a treatment where exactly one of the begin and end values is the empty string, ie. the
            user filled only one entry.

        Returns:
            dict[str, dict[str, int | str]]: The same dictionary but with empty rows removed.
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
    begin: int | str
    end: int | str

    @property
    def values(self) -> tuple[int | str, int | str]:
        return (self.begin, self.end)
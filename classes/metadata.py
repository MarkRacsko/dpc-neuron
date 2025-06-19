import toml
from dataclasses import dataclass
from pathlib import Path

@dataclass
class _Treatment:
    name: str
    begin: int
    end: int

class Editor:
    def __init__(self, folder_path: Path) -> None:
        self.metadata_path = folder_path / "metadata.toml"
        try:
            with open(self.metadata_path, "r") as f:
                self.dict = toml.load(f)
        except FileNotFoundError:
            self.dict = {"conditions": {"ratiometric_dye": 0,
                                        "group1": "",
                                        "group2": ""},
                        "treatments": {}}
        self.treatments: list[_Treatment] = []

    def edit_condition(self, key, value):
        self.dict["conditions"][key] = value

    def add_treatment(self, name: str, begin: int, end: int):
        self.treatments.append(_Treatment(name, begin, end))

    def change_treatment(self, index: int, name: str, begin: int, end: int):
        self.treatments[index] = _Treatment(name, begin, end)
    
    def remove_treatment(self, index: int):
        del self.treatments[index]
    
    def write_file(self):
        for treatment in self.treatments:
            self.dict["treatments"][treatment.name]["begin"] = treatment.begin
            self.dict["treatments"][treatment.name]["end"] = treatment.end

        with open(self.metadata_path, "w") as metadata:
            toml.dump(self.dict, metadata)
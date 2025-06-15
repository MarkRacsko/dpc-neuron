import pandas as pd
from pathlib import Path
from subdir import SubDir
from typing import Any

type ExperimentalCondition = list[str]
type ExperimentalData = tuple[str, pd.Series[int]]

class DataAnalyzer:
    """Orchestrates data processing and presents a simpler interface to main.

    Attributes:
        config (dict[str, dict[str, str]]): The config file as a Python dict.
        repeat (bool): The --repeat command line flag as a bool. Tells the subdirectory level processors to skip already
        processed directories.
    """
    def __init__(self, config: dict[str, dict[str, Any]], repeat: bool) -> None:
        self.config = config
        self._subdirs: list[SubDir] = []
        self.repeat = repeat
        self.experiments: dict[ExperimentalCondition, list[ExperimentalData]]

    def create_subdir_instance(self, subdir_path: Path):
        """Creates a new SubDir object for the given path and appends it to a (private) list.

        Args:
            subdir_path (Path): Path to this subdirectory in the target directory we are processing.
            repeat (bool): The --repeat command line flag as a bool.
        """
        instance = SubDir(subdir_path, self.config["report"])
        instance.preprocessing(self.repeat)
        self._subdirs.append(instance)

    def process_data(self) -> None:
        """Processes all subdirectories in the target directory, using the method set in the config file.
        """
        for subdir in self._subdirs:
            subdir.make_report(method=self.config["input"]["method"],
                               sd_multiplier=self.config["input"]["SD_multiplier"],
                               smoothing_window=self.config["input"]["smoothing_range"])

    def tabulate_data(self):
        sum_conf = self.config["tabulated_report"]
        summary_file_name: Path = self.config["input"]["target_folder"] / f"{sum_conf["name"]}{sum_conf["extension"]}"
        for subdir in self._subdirs:
            
            subdir.load_summary()
            assert isinstance(subdir.report, pd.DataFrame) # will never fail, but Pylance can't see why
            condition: ExperimentalCondition = list(subdir.treatment_col_names)
            subdir_data: ExperimentalData = (subdir.path.name, subdir.report[["cell_type"] + subdir.treatment_col_names].value_counts())
            if condition not in self.experiments.keys():
                self.experiments[condition] = [subdir_data]
            else:
                self.experiments[condition].append(subdir_data)
        
        with pd.ExcelWriter(summary_file_name) as writer:
            for condition, data in self.experiments.items():
                summary = pd.DataFrame(index=data[0][1].index)
                for name, series in data:
                    summary[name] = series
                
                sheet_name = ""
                for agonist in condition:
                    sheet_name += f"{agonist} "
                sheet_name = sheet_name.rstrip()
                
                summary.to_excel(writer, sheet_name=sheet_name)


        

    def graph_data(self):
        """Makes graphs from every measurement in every subdirectory. The graphs will be saved in new folders, each
        named after the measurement file from which the graphs were created.
        """
        for subdir in self._subdirs:
            subdir.make_graphs()
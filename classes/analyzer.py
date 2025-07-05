import pandas as pd
from pathlib import Path
from .subdir import SubDir
from .toml_data import Config
from threading import Thread
from tkinter import IntVar

type ExperimentalCondition = list[str]
type ExperimentalData = tuple[str, pd.Series[int]]

class DataAnalyzer:
    """Orchestrates data processing and presents a simpler interface to main.

    Attributes:
        config (dict[str, dict[str, str]]): The config file as a Python dict.
        repeat (bool): The --repeat command line flag as a bool. Tells the subdirectory level processors to skip already
        processed directories.
    """
    def __init__(self, config: Config, finished_files: IntVar, repeat: bool) -> None:
        self.config = config
        self._subdirs: list[SubDir] = []
        self.repeat = repeat
        self.finished_files = finished_files
        self.experiments: dict[ExperimentalCondition, list[ExperimentalData]]

    def create_subdir_instance(self, subdir_path: Path) -> str | None:
        """Creates a new SubDir object for the given path and appends it to a (private) list.

        Args:
            subdir_path (Path): Path to this subdirectory in the target directory we are processing.
            repeat (bool): The --repeat command line flag as a bool.
        """
        instance = SubDir(subdir_path, self.config.output.report_name)
        error = instance.preprocessing(self.repeat)
        self._subdirs.append(instance)
        
        if error:
            return error

    def process_data(self, errors: list[str]):
        """Processes all subdirectories in the target directory, using the method set in the config file.
        """
        arg_tuple = (self.config.input.method,
                     self.config.input.SD_multiplier,
                     self.config.input.smoothing_range,
                     self.finished_files,
                     errors)
        threads = []
        for subdir in self._subdirs:
            thread = Thread(target=subdir.make_report, args=arg_tuple)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()


    def tabulate_data(self):
        """Creates a summary file from all available measurement reports.
        """
        sum_conf = self.config.output
        summary_file_name: Path = self.config.input.target_folder / f"{sum_conf.summary_name}.xlsx"
        for subdir in self._subdirs:
            
            subdir.load_summary_from_report()
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
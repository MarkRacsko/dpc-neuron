from pathlib import Path
from threading import Thread
from tkinter import IntVar

import pandas as pd

from .converter import Converter
from .processor import DataProcessor
from .toml_data import Config

type ExperimentalCondition = list[str] # list of agonists used in this particular experiment
type ExperimentalData = tuple[str, pd.Series[int]] # the string is the folder name where the experiment's data is;
# the pd.Series is multi-indexed, by the reaction column names and shows how many cells belong to a given combination
# of reactions (such as TRPM3+ TRPA1- TRPV1- neurons)

class AnalysisEngine:
    """Orchestrates data processing and presents a simpler interface to main.

    Attributes:
        config (dict[str, dict[str, str]]): The config file as a Python dict.
        repeat (bool): The --repeat command line flag as a bool. Tells the subdirectory level processors to skip already
        processed directories.
    """
    def __init__(self, config: Config, finished_files: IntVar, repeat: bool) -> None:
        self.config = config
        self._processors: list[DataProcessor] = []
        self.repeat = repeat
        self.finished_files = finished_files
        self.experiments: dict[ExperimentalCondition, list[ExperimentalData]]

    def create_processor_instances(self) -> list[str]:
        """Creates a new SubDir object for the given path and appends it to a (private) list.

        Returns:
            list[str]: A list of error messages produced by the individual subdirectory level processor objects.
            Empty if no errors occured.
        """
        errors = []
        for path in self.config.input.target_folder.iterdir():
            if path.is_dir():
                instance = DataProcessor(path, self.config.output.report_name)
                error = instance.preprocessing(self.repeat)
                if error is not None:
                    errors.append(error)
                self._processors.append(instance)
        
        return errors
    
    def create_caches(self) -> None:
        converter = Converter(self.config.input.target_folder, self.config.output.report_name)
        converter.convert_to_feather(self.finished_files)

    def process_data(self, errors: list[str]):
        """Processes all subdirectories in the target directory, using the method set in the config file.
        """
        arg_tuple = (self.config.input.method,
                     self.config.input.SD_multiplier,
                     self.config.input.smoothing_range,
                     self.config.input.correction,
                     self.finished_files,
                     errors)
        threads = []
        for processor in self._processors:
            thread = Thread(target=processor.make_report, args=arg_tuple)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        
        self.finished_files.set(0)

    def summarize_results(self):
        """Creates a summary file from all available measurement reports.
        """
        name = self.config.output.summary_name
        summary_file_name: Path = self.config.input.target_folder / f"{name}.xlsx"
        threads = []
        for processor in self._processors:
            thread = Thread(target=processor.load_summary_from_report, args=(self.finished_files,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        for processor in self._processors:
            assert isinstance(processor.report, pd.DataFrame) # will never fail, but Pylance can't see why
            condition: ExperimentalCondition = list(processor.treatment_col_names)
            results: ExperimentalData = (processor.path.name, processor.report[["cell_type"] + processor.treatment_col_names].value_counts())
            if condition not in self.experiments.keys():
                self.experiments[condition] = [results]
            else:
                self.experiments[condition].append(results)
        
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

        self.finished_files.set(0)


    def graph_data(self):
        """Makes graphs from every measurement in every subdirectory. The graphs will be saved in new folders, each
        named after the measurement file from which the graphs were created.
        """
        threads = []
        for processor in self._processors:
            thread = Thread(target=processor.make_graphs, args=(self.finished_files,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.finished_files.set(0)

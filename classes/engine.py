import pandas as pd
from pathlib import Path
from .converter import Converter
from .processor import DataProcessor
from .toml_data import Config
from threading import Thread
from tkinter import IntVar

type ExperimentalCondition = list[str]
type ExperimentalData = tuple[str, pd.Series[int]]

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
                error = instance.preprocessing(self.repeat, self.finished_files)
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
                     self.finished_files,
                     errors)
        threads = []
        for processor in self._processors:
            thread = Thread(target=processor.make_report, args=arg_tuple)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()


    def summarize_results(self):
        """Creates a summary file from all available measurement reports.
        """
        sum_conf = self.config.output
        summary_file_name: Path = self.config.input.target_folder / f"{sum_conf.summary_name}.xlsx"
        for processor in self._processors:
            
            processor.load_summary_from_report()
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


    def graph_data(self):
        """Makes graphs from every measurement in every subdirectory. The graphs will be saved in new folders, each
        named after the measurement file from which the graphs were created.
        """
        for processor in self._processors:
            processor.make_graphs()
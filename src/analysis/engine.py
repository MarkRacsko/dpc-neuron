from pathlib import Path
from threading import Thread

import pandas as pd

from utilities.custom_types import ExperimentalCondition, ExperimentalData, ProgressBar
from utilities.toml_data import Config

from .processor import DataProcessor


class AnalysisEngine:
    """Orchestrates data processing and presents a simpler interface to main.

    Attributes:
        config (dict[str, dict[str, str]]): The config file as a Python dict.
        repeat (bool): The --repeat command line flag as a bool. Tells the subdirectory level processors to skip already
        processed directories.
    """
    def __init__(self, config: Config, repeat: bool) -> None:
        self.config = config
        self._processors: list[DataProcessor] = []
        self.repeat = repeat
        self.experiments: dict[ExperimentalCondition, list[ExperimentalData]]
        self.number_of_files: int

    def create_processor_instances(self):
        """Creates a new DataProcessor object for the given path and appends it to a (private) list.

        Returns:
            list[str]: A list of error messages produced by the individual subdirectory level processor objects.
            Empty if no errors occured.
        """
        for path in self.config.input.target_folder.iterdir():
            if path.is_dir():
                instance = DataProcessor(path, self.config)
                self._processors.append(instance)
        self.number_of_files = sum([len(processor.measurement_files) for processor in self._processors])
    

    def process_data(self, progress_bar: ProgressBar) -> list[str]:
        """Processes all subdirectories in the target directory, using the method set in the config file.
        """
        errors: list[str] = []
        arg_tuple = (errors, progress_bar)
        threads = []

        for processor in self._processors:
            error = processor.preprocessing(self.repeat)
            if error is not None:
                errors.append(error)
        
        for processor in self._processors:
            thread = Thread(target=processor.make_report, args=arg_tuple)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return errors

    def summarize_results(self) -> list[str]:
        """Creates a summary file from all available measurement reports.
        """
        name = self.config.output.summary_name
        summary_file_name: Path = self.config.input.target_folder / f"{name}.xlsx"
        threads = []
        errors = []
        arg_tuple = (errors,)
        for processor in self._processors:
            thread = Thread(target=processor.load_summary_from_report, args=arg_tuple)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        if errors:
            return errors # if there were any errors, we don't want to proceed

        for processor in self._processors:
            assert isinstance(processor.report, pd.DataFrame) # will never fail, but Pylance can't see why
            condition: ExperimentalCondition = list(processor.treatment_col_names)
            results: ExperimentalData = (processor.path.name, processor.report[["cell_type"] + processor.treatment_col_names].value_counts())
            if condition not in self.experiments:
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

        return errors
        # if this return is hit, there were no errors, the list is empty
        # technically not necessary, but makes the type checker happy


    def graph_data(self, progress_bar: ProgressBar) -> list[str]:
        """Makes graphs from every measurement in every subdirectory. The graphs will be saved in new folders, each
        named after the measurement file from which the graphs were created.
        """
        errors: list[str] = []
        arg_tuple = (errors, progress_bar)
        threads = []
        for processor in self._processors:
            thread = Thread(target=processor.make_graphs, args=arg_tuple)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return errors

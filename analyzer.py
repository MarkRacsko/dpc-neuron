from pathlib import Path
from subdir import SubDir
from typing import Any

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
            subdir.make_report(self.config["input"]["method"], self.config["input"]["SD_multiplier"])

    def tabulate_data(self):
        pass

    def graph_data(self):
        """Makes graphs from every measurement in every subdirectory. The graphs will be saved in new folders, each
        named after the measurement file from which the graphs were created.
        """
        for subdir in self._subdirs:
            subdir.make_graphs()
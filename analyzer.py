from pathlib import Path
from subdir import SubDir

class DataAnalyzer:
    def __init__(self, config: dict[str, dict[str, str]], repeat: bool) -> None:
        self.config = config
        self.subdirs: list[SubDir] = []
        self.repeat = repeat

    def create_subdir_instance(self, subdir_path: Path):
        self.subdirs.append(SubDir(subdir_path, self.config["report"]))

    def process_data(self):
        for subdir in self.subdirs:
            subdir.make_report(self.config["input"]["method"], self.repeat)

    def tabulate_data(self):
        pass

    def graph_data(self):
        pass
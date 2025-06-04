import numpy as np
import pandas as pd
from pathlib import Path
from utilities import create_event_slices, smooth

class SubDir:
    def __init__(self, path: Path, report_config: dict[str, str]) -> None:
        self.path = path
        self.report_config = report_config
        self.treatment_col_names: list[str]
        self.treatment_windows: dict[str, slice[int]]
        self.report: pd.DataFrame

    def parse_events(self) -> None:
        """Reads in the event file that describes what happened during the measurement in question.

        Args:
            file (Path): The pathlib.Path object representing the event file. Must be csv.

        Returns:
            dict[str, slice[int]: This dictionary maps the names of agonists to the time windows where they were applied.
            list[str]: The list of agonist related column names for the report DataFrame.
        """
        file = self.path / "events.csv"
        events_df = pd.read_csv(file, header=0)

        treatments, start_times, stop_times = events_df["treatment"], events_df["start"], events_df["stop"]
        event_slices = create_event_slices(start_times, stop_times)
        self.treatment_windows: dict[str, slice[int]] = {k: v for k, v in zip(treatments, event_slices)}
        
        self.treatment_col_names = []
        for agonist in treatments:
            if agonist == "baseline":
                continue
            self.treatment_col_names.append(agonist + "_reaction")
            self.treatment_col_names.append(agonist + "_amp")

    def make_report(self, method: str, repeat: bool) -> None:
        """This meant to encapsulate everything currently under the if process: block in process_subdir().
        """
        report_path = self.path / f"{self.report_config["name"]}{self.path.name}{self.report_config["extension"]}"
        if report_path.exists() and not repeat:
            return
                
        measurement_files = [f for f in self.path.glob("*.xlsx") if f != report_path]
        output_columns = ["cell_ID", "condition", "cell_type"] + self.treatment_col_names

        self.report = pd.DataFrame(columns=output_columns)
        cell_ID: int = 0
        for file in measurement_files:
            file_result = pd.DataFrame(columns=output_columns)
            # read in 340 and 380 data separately
            F340_data = pd.read_excel(file, sheet_name="F340")
            F380_data = pd.read_excel(file, sheet_name="F380")
            cell_cols = [c for c in F380_data.columns if c not in {"Time", "Background"}]
            
            # split the data
            x_data, bgr_380, cells_380 = F380_data["Time"].to_numpy(), F380_data["Background"].to_numpy(), F380_data[cell_cols].to_numpy()
            bgr_340, cells_340 = F340_data["Background"].to_numpy(), F340_data[cell_cols].to_numpy()
            
            # turn time and background into 2d arrays with one column each because this shape is needed for linalg.lstsq
            x_data, bgr_340, bgr_380 = x_data[:, np.newaxis], bgr_340[:, np.newaxis], bgr_380[:, np.newaxis]
            
            # substract backgrounds
            cells_340 = cells_340 - bgr_340
            cells_380 = cells_380 - bgr_380
            
            # smoothing should probably go here
            cells_340 = np.apply_along_axis(smooth, 0, cells_340)
            cells_380 = np.apply_along_axis(smooth, 0, cells_380)

            # photobleaching correction
            matrix = np.hstack((np.ones_like(x_data), x_data))
            coeffs_340, _, _, _ = np.linalg.lstsq(matrix, cells_340, rcond=None)
            coeffs_380, _, _, _ = np.linalg.lstsq(matrix, cells_380, rcond=None)
            cells_340 = cells_340 - (x_data * coeffs_340[1])
            cells_380 = cells_380 - (x_data * coeffs_380[1])
            
            # I'm working with Fura2 so the actual data of interest is the ratios between emissions at 340 and 380 nm.
            ratios = np.transpose(cells_340 / cells_380)
            
            # measurements with neurons only will be called "neuron only {number}.xlsx" whereas neuron + DPC is going to
            # be "neuron + DPC {number}.xlsx"
            condition = "N" if "only" in file.name else "N+D"
            
            # determine if cells react to each of the agonists, and how big the response amplitudes are
            # no default case because we already have a guard clause to make sure these 3 are the only options, which we
            # do in main before reading any measurement data from disk, so if the program's gonna crash it does so quickly
            match method:
                case "baseline":
                    baseline_threshold(ratios, agonist_slices, file_result)
                case "previous":
                    previous_threshold(ratios, agonist_slices, file_result)
                case "derivative":
                    derivate_threshold(ratios, agonist_slices, file_result)
            
            number_of_cells = ratios.shape[0]
            file_result["cell_ID"] = [x for x in range(cell_ID, cell_ID + number_of_cells)]
            cell_ID += number_of_cells
            file_result["condition"] = [condition for _ in range(number_of_cells)]

            if graphs:
                graphing_path: Path = subdir / Path(file.stem)
                if not graphing_path.exists():
                    Path.mkdir(graphing_path)

                reaction_cols = [col for col in file_result.columns if "_reaction" in col]
                make_graphs(x_data.flatten(), ratios, cell_cols, agonist_slices, file_result[reaction_cols], graphing_path)
            
            # in the Excel files, columns will be called N1, N2, N3... for neurons and DPC1, DPC2, DPC3... for DPCs
            cell_cols = [c.strip("1234567890") for c in cell_cols]
            file_result["cell_type"] = cell_cols

            self.report = pd.concat([self.report, file_result])
import numpy as np
import pandas as pd
import toml
from pathlib import Path
from functions import normalize, smooth, baseline_threshold, previous_threshold, derivate_threshold, validate_metadata
from matplotlib.figure import Figure
from typing import Optional
from threading import Lock
from tkinter import IntVar
from .converter import Converter

class SubDir:
    _error_lock = Lock()
    _file_count_lock = Lock()

    def __init__(self, path: Path, report_name: str) -> None:
        self.path = path
        self.cache_path = path / ".cache"
        self.report_path = path / f"{report_name}{path.name}.xlsx"
        self.converter = Converter(path, self.cache_path, self.report_path)
        self.treatment_col_names: list[str] = []
        self.treatment_windows: dict[str, slice[int]] = {}
        self.report: Optional[pd.DataFrame] = None
        self.has_report: bool = False
        self.conditions: dict[str, str]
        self.measurement_files = [f for f in self.path.glob("*.xlsx") if f != self.report_path]

    def preprocessing(self, repeat: bool) -> str | None:
        errors = self.parse_metadata()
        if errors:
            return errors
        if not self.cache_path.exists():
            Path.mkdir(self.cache_path)
            self.converter.convert_to_feather()

        if self.report_path.exists() and not repeat:
            self.has_report = True


    def parse_metadata(self) -> str | None:
        try:
            file = self.path / "metadata.toml"
            with open(file, "r") as f:
                metadata = toml.load(f)
        except FileNotFoundError:
            return f"Metadata file missing from {self.path}."

        errors = validate_metadata(self.path.name, metadata)
        if errors:
            return errors
        self.conditions = metadata["conditions"]

        for agonist_name, agonist_dict in metadata["treatments"].items():
            self.treatment_windows[agonist_name] = slice(agonist_dict["begin"], agonist_dict["end"])
            if agonist_name == "baseline":
                continue
            self.treatment_col_names.append(agonist_name + "_reaction")
            self.treatment_col_names.append(agonist_name + "_amp")
    
    def make_report(self, method: str, sd_multiplier: int, smoothing_window: int, finished_files: IntVar, error_list: list[str]) -> str | None:
        """This meant to encapsulate everything currently under the if process: block in process_subdir().
        """
        if self.has_report:
            return
                
        output_columns = ["cell_ID", "condition", "cell_type"] + self.treatment_col_names

        # self.report = pd.DataFrame(columns=output_columns)
        results: list[pd.DataFrame] = []
        cell_ID: int = 0
        bad_groups_files: list[Path] = []
        bad_sheet_files: list[Path] = []
        for file in self.measurement_files:
            file_result = pd.DataFrame(columns=output_columns)
            try:
                if self.conditions["ratiometric_dye"].lower() == "true":
                    cell_cols, data = self.prepare_ratiometric_data(file, smoothing_window)
                else:
                    cell_cols, data = self.prepare_non_ratiometric_data(file, smoothing_window)
            except SyntaxError:
                bad_sheet_files.append(file)
                continue
            # measurements with neurons only will be called "neuron only {number}.xlsx" whereas neuron + DPC is going to
            # be "neuron + DPC {number}.xlsx"
            group1: str = self.conditions["group1"]
            group2: str = self.conditions["group2"]
            
            if group1 in file.name:
                condition = group1
            elif group2 in file.name:
                condition = group2
            else:
                bad_groups_files.append(file)
                continue
            
            # determine if cells react to each of the agonists, and how big the response amplitudes are
            # no default case because we already have a guard clause to make sure these 3 are the only options, which we
            # do in main before reading any measurement data from disk, so if the program's gonna crash it does so quickly
            match method:
                case "baseline":
                    baseline_threshold(data, self.treatment_windows, file_result, sd_multiplier)
                case "previous":
                    previous_threshold(data, self.treatment_windows, file_result, sd_multiplier)
                case "derivative":
                    derivate_threshold(data, self.treatment_windows, file_result, sd_multiplier)
            
            number_of_cells = data.shape[0]
            file_result["cell_ID"] = [x for x in range(cell_ID, cell_ID + number_of_cells)]
            cell_ID += number_of_cells
            file_result["condition"] = [condition for _ in range(number_of_cells)]
            # in the Excel files, columns will be called N1, N2, N3... for neurons and DPC1, DPC2, DPC3... for DPCs
            cell_cols = [c.strip("1234567890") for c in cell_cols]
            file_result["cell_type"] = cell_cols

            results.append(file_result)
            self.update_file_count(finished_files)

        self.report = pd.concat(results)

        self.save_report()

        message = ""
        if bad_groups_files:
            message += "The following files are named incorrectly:"
            for f in bad_groups_files:
                message += f"\n{str(f)}"
            message += "\nPlease consult the appropriate metadata file and rename them."
        if bad_sheet_files:
            message += "\n\nThe following files have incorrectly named sheets:"
            for f in bad_sheet_files:
                message += f"\n{str(f)}"
            message += "\nPlease consult the README and rename the sheet(s) appropriately."
        if message:
            with self._error_lock:
                error_list.append(message)

    def make_graphs(self):
        if self.report is None:
            self.report = pd.read_excel(self.report_path, sheet_name="Cells")
        
        for file in self.measurement_files:
            graphing_path: Path = self.path / Path(file.stem)
            if not graphing_path.exists():
                Path.mkdir(graphing_path)
            sheet_name = "Py_ratios" if self.conditions["ratiometric_dye"] else "Processed"
            ratios = pd.read_excel(file, sheet_name=sheet_name)
            cell_cols = [c for c in ratios.columns if c != "Time"]
            ratios = np.transpose(ratios.to_numpy())
            x_data, ratios = ratios[0], ratios[1:]
            reaction_cols = [col for col in self.report.columns if "_reaction" in col]

            self.graph_data(x_data.flatten(), ratios, cell_cols, self.report[reaction_cols], graphing_path)
    
    def graph_data(self, x_data: np.ndarray, traces: np.ndarray, col_names: list[str], reactions: pd.DataFrame, save_dir: Path) -> None:
        """Creates line graphs for each cell in this particular measurement file. Is called from within make_report()
        because it needs the cell trace data and that funtion only returns the report DataFrame.

        Args:
            x_data (np.ndarray): The time values as a 1d array.
            traces (np.ndarray): The ratio data to be plotted.
            treatments (dict[str, slice[int]]): The dictionary describing what agonist was used between what time points.
            Called agonist_slices elsewhere.
            reactions (pd.DataFrame): Those columns of the file result df that contain the reaction True/False values for
            each agonist used.
            save_dir (Path): The newly created directory where the graphs are supposed to be saved.
        """
        majors = [x for x in range(0, len(x_data) + 1, 60)]
        major_labels = [str(x//60) for x in majors]
        for i, (cell_name, y_data) in enumerate(zip(col_names, traces), start=0):
            fig = Figure(figsize=(10, 5))
            ax = fig.subplots(1, 1)

            ax.plot(x_data, y_data)
            ax.set_xticks(majors, labels=major_labels, minor=False)
            ax.set_xlabel("Time (min)")
            ax.set_ylabel("Ratio")

            ymin, ymax = ax.get_ylim()
            agonist_label_y = ymin - (ymax - ymin) * 0.2
            reaction_label_y = ymin - (ymax - ymin) * 0.25
            for name, time_slice in self.treatment_windows.items():
                if name == "baseline" or name == "END":
                    continue
                ax.axvline(x=time_slice.start, c="black")
                ax.axvline(x=time_slice.stop, c="black")
                ax.text(x=time_slice.start, y=agonist_label_y, s=name)
                # this next line is supposed to print TRUE under a given agonist name if the program thinks that cell reacts
                # to that agonist and FALSE otherwise
                # if name != "baseline":
                ax.text(x=time_slice.start, y=reaction_label_y, s=str(reactions.at[i, f"{name}_reaction"]).upper())

            # Cell numbering is 0 indexed on purpose!
            fig.suptitle(f"{cell_name}")
            fig.tight_layout()
            fig.savefig(save_dir / f"Cell no. {i}.png", dpi=300)
            fig.clf()
            print(f"Done with {cell_name}")

    def load_summary(self) -> None:
            self.report = pd.read_excel(self.report_path, sheet_name="Summary")

    def prepare_ratiometric_data(self, file: Path, smoothing_window: int) -> tuple[list[str], np.ndarray]:
        # read in 340 and 380 data separately
        F340_data = pd.read_feather(self.cache_path / f"{file.name}.F340.feather")
        F380_data = pd.read_feather(self.cache_path / f"{file.name}.F380.feather")
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
        cells_340 = np.apply_along_axis(smooth, 0, cells_340, window_size = smoothing_window)
        cells_380 = np.apply_along_axis(smooth, 0, cells_380, window_size = smoothing_window)

        # photobleaching correction
        matrix = np.hstack((np.ones_like(x_data), x_data))
        coeffs_340, _, _, _ = np.linalg.lstsq(matrix, cells_340, rcond=None)
        coeffs_380, _, _, _ = np.linalg.lstsq(matrix, cells_380, rcond=None)
        coeffs_340, coeffs_380 = coeffs_340[1], coeffs_380[1] # we don't care about the y intercept
        cells_340 = cells_340 - (x_data * coeffs_340)
        cells_380 = cells_380 - (x_data * coeffs_380)
        
        # I'm working with Fura2 so the actual data of interest is the ratios between emissions at 340 and 380 nm.
        ratios = np.transpose(cells_340 / cells_380)
        self.save_processed_data(file, x_data, ratios, cell_cols, np.vstack((coeffs_340, coeffs_380)))

        return cell_cols, ratios
    
    def prepare_non_ratiometric_data(self, file:Path, smoothing_window: int) -> tuple[list[str], np.ndarray]:
        data = pd.read_feather(self.cache_path / f"{file.name}.Raw.feather")
        cell_cols = [c for c in data.columns if c not in {"Time", "Background"}]
        x_data, bgr, cells = data["Time"].to_numpy(), data["Background"].to_numpy(), data[cell_cols].to_numpy()
        x_data, bgr = x_data[:, np.newaxis], bgr[:, np.newaxis]
        
        # normalization and smoothing
        cells = np.apply_along_axis(normalize, 0, cells, baseline=self.treatment_windows["baseline"].stop)
        cells = np.apply_along_axis(smooth, 0, cells, window_size = smoothing_window)
        
        # photobleaching correction
        matrix = np.hstack((np.ones_like(x_data), x_data))
        coeffs, _, _, _ = np.linalg.lstsq(matrix, cells, rcond=None)
        coeffs = coeffs[1] # we don't care about the y intercept
        cells = cells - (x_data * coeffs)

        self.save_processed_data(file, x_data, cells, cell_cols, coeffs)
        return cell_cols, cells.transpose()

    def update_file_count(self, count):
        with self._file_count_lock:
            count.set(count.get() + 1)

    def save_processed_data(self, file: Path, x_data: np.ndarray, cell_data: np.ndarray, col_names: list[str], coeffs: np.ndarray) -> None:
        col_names = ["Time"] + col_names
        data = np.vstack((x_data.flatten(), cell_data))
        data = np.transpose(data)
        ratio: bool = self.conditions["ratiometric_dye"].lower() == "true"
        if ratio:
            sheet_name: str = "Py_ratios"
        else:
            sheet_name: str = "Processed"
        
        df = pd.DataFrame(data, columns=col_names)
        df.to_feather(self.cache_path / f"{file.name}.{sheet_name}.feather")

        if ratio:
            col_names[0] = "Wavelength"
            first_col = np.array([340, 380])
            first_col = first_col[:, np.newaxis]
            coeffs = np.hstack((first_col, coeffs))
            df = pd.DataFrame(coeffs, columns=col_names)
            df.to_feather(self.cache_path / f"{file.name}.Coeffs.feather")
        else:
            df = pd.DataFrame(coeffs, columns=col_names)
            df.to_feather(self.cache_path / f"{file.name}.Coeffs.feather")
        # If we're not using a ratiometric dye, we only have one set of coefficients, but if we are using Fura, then we
        # have two, and we should save which is which.

    def save_report(self) -> None:
        assert self.report is not None # report is guaranteed not to be None by the time this method is called
        with pd.ExcelWriter(self.report_path) as writer:
            self.report.to_excel(writer, sheet_name="Cells", index=False)
            cols = [c for c in self.treatment_col_names if "_reaction" in c]
            stats = self.report[["cell_type", "condition"] + cols].value_counts()
            stats.to_excel(writer, sheet_name="Summary")
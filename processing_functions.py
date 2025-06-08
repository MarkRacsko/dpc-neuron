from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import math
from matplotlib import figure

def process_subdir(subdir: Path, report_path: Path, method: str, process: bool, tabulate: bool, graphs: bool):
    report = None
    if process:
        report = make_report(subdir, report_path, method, graphs)
        report.to_excel(report_path)

    if tabulate:
        _, agonists = parse_events(subdir, tabulate_mode=True)
        if report is None:
            report = pd.read_excel(report_path)
        stats = report[["cell_type"] + agonists].value_counts()
        

def parse_events(subdir: Path, tabulate_mode: bool = False) -> tuple[dict[str, slice[int]], list[str]]:
    """Reads in the event file that describes what happened during the measurement in question.

    Args:
        file (Path): The pathlib.Path object representing the event file. Must be csv.

    Returns:
        dict[str, slice[int]: This dictionary maps the names of agonists to the time windows where they were applied.
        list[str]: The list of agonist related column names for the report DataFrame.
    """
    file = subdir / "events.csv"
    events_df = pd.read_csv(file, header=0)

    treatments, start_times, stop_times = events_df["treatment"], events_df["start"], events_df["stop"]
    event_slices = create_event_slices(start_times, stop_times)
    agonist_slices: dict[str, slice[int]] = {k: v for k, v in zip(treatments, event_slices)}
    
    agonist_cols = []
    for agonist in treatments:
        if agonist == "baseline":
            continue
        agonist_cols.append(agonist + "_reaction")
        if not tabulate_mode:
            agonist_cols.append(agonist + "_amp")
    
    return agonist_slices, agonist_cols


def create_event_slices(starts: pd.Series, stops: pd.Series) -> list[slice[int]]:
    """Translates the list of timepoints when events happened into a list of slice objects that represent this
    information as time windows. The output is intended to be used to access the relevant parts of the calcium trace data.

    Args:
        event_list (list[int]): The events as returned by parse_events().

    Returns:
        list[slice]: A list of slices of the form [agonist_start_time:agonist_end_time] where agonist refers to the
        compound added in this particular time window to the cells being measured.
    """
    slices: list[slice[int]] = []

    for start, stop in zip(starts, stops):
        slices.append(slice(start, stop))

    return slices

def smooth(array: np.ndarray, window_size: int = 5) -> np.ndarray:
    """This function performs a sliding window type smoothing on an array representing a Ca trace.

    Args:
        array (np.ndarray): The array to be smoothed. Must be 1-dimensional.
        window_size (int, optional): The average of this many elements will be taken for the smoothing. Defaults to 5, and it should be an odd number.

    Raises:
        ValueError: If the input array is of the incorrect shape, or the selected window_size is too large or it isn't odd.

    Returns:
        np.ndarray: The smoothed array.
    """
    # Should be compatible with numba. Homogeneous sets of ints are supported.
    if array.ndim != 1:
        raise ValueError("Input array must be 1-dimensional.")
    if window_size % 2 == 0:
        raise ValueError("Window size should be an odd number.")
    length = len(array)
    if window_size > math.sqrt(length):
        raise ValueError(
            "Window size should not be larger than the square root of the length of the array."
        )

    sliding_size, half_size = window_size // 2 + 1, window_size // 2
    sliding_index = 0
    out_array = np.zeros_like(array)
    dont_touch: set[int] = set()  # This is a set for fast membership checking.
    while sliding_size < window_size:
        # This loop handles the edges of the array where we want to take the mean of fewer than window_size number of elements.
        out_array[sliding_index] = array[:sliding_size].mean()
        out_array[-(sliding_index + 1)] = array[-sliding_size:].mean()
        dont_touch.add(sliding_index)
        dont_touch.add(-(sliding_index + 1) % length)
        sliding_index += 1
        sliding_size += 1

    for index in range(len(array)):
        # This loop handles the middle parts where all elements required for a mean-window_size smoothing exist.
        if index in dont_touch:
            continue
        else:
            out_array[index] = array[index - half_size : index + half_size + 1].mean()

    return out_array

def make_report(subdir: Path, report_path: Path, method: str, graphs: bool) -> pd.DataFrame:
    """This meant to encapsulate everything currently under the if process: block in process_subdir().
    """
    
    measurement_files = [f for f in subdir.glob("*.xlsx") if f != report_path]
    
    agonist_slices, agonist_columns = parse_events(subdir)
    output_columns = ["cell_ID", "condition", "cell_type"] + agonist_columns

    report = pd.DataFrame(columns=output_columns)
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

        report = pd.concat([report, file_result])

    return report

def baseline_threshold(ratios: np.ndarray, agonist_slices: dict[str, slice[int]], file_result: pd.DataFrame):
    baseline_means = ratios[agonist_slices["baseline"]].mean(axis=1, keepdims=True)
    baseline_stdevs = ratios[agonist_slices["baseline"]].std(axis=1, mean=baseline_means, keepdims=True)
    thresholds = baseline_means + 2*baseline_stdevs
    
    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        maximums = ratios[time_window].max(axis=1, keepdims=True)
        amplitudes = maximums - baseline_means.flatten()
        reactions = np.where(maximums > thresholds, True, False)
        file_result[agonist + "_reaction"] = reactions
        file_result[agonist + "_amp"] = amplitudes

def previous_threshold(ratios: np.ndarray, agonist_slices: dict[str, slice[int]], file_result: pd.DataFrame):
    baseline_means = ratios[:,agonist_slices["baseline"]].mean(axis=1, keepdims=True)
    baseline_stdevs = ratios[:,agonist_slices["baseline"]].std(axis=1, mean=baseline_means, keepdims=True)

    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        thresholds = ratios[:,time_window.start - 10:time_window.start].mean(axis=1, keepdims=False) + 2*baseline_stdevs.flatten() # hotfix, need to think more
        maximums = ratios[:,time_window].max(axis=1, keepdims=False)
        amplitudes = maximums - baseline_means.flatten()
        # using amplitudes to determine reactions is wrong because of the baseline substraction
        # (only cells where the max is larger than the threshold by at least the value of the baseline mean would be 
        # considered to have reacted)
        reactions = np.where(maximums > thresholds, True, False)
        file_result[agonist + "_reaction"] = reactions.flatten()
        file_result[agonist + "_amp"] = amplitudes.flatten()

def derivate_threshold(ratios: np.ndarray, agonist_slices: dict[str, slice[int]], file_result: pd.DataFrame):
    derivs = np.gradient(ratios, axis=1)
    baseline_deriv_means = derivs[agonist_slices["baseline"]].mean(axis=1, keepdims=True)
    baseline_deriv_stdevs = derivs[agonist_slices["baseline"]].std(axis=1, mean=baseline_deriv_means, keepdims=True)
    thresholds = baseline_deriv_means + 2*baseline_deriv_stdevs.flatten()
    
    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        amplitudes = ratios[time_window].max(axis=1, keepdims=True) - baseline_deriv_means.flatten()
        maximum_derivs = derivs[time_window].max(axis=1, keepdims=False)
        reactions = np.where(maximum_derivs > thresholds, True, False)
        file_result[agonist + "_reaction"] = reactions.flatten()
        file_result[agonist + "_amp"] = amplitudes.flatten()

def make_graphs(x_data: np.ndarray, traces: np.ndarray, col_names: list[str], treatments: dict[str, slice[int]], reactions: pd.DataFrame, 
                save_dir: Path) -> None:
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
        fig = figure.Figure(figsize=(10, 5))
        ax = fig.subplots(1, 1)

        ax.plot(x_data, y_data)
        ax.set_xticks(majors, labels=major_labels, minor=False)
        ax.set_xlabel("Time (min)")
        ax.set_ylabel("Ratio")

        ymin, ymax = ax.get_ylim()
        agonist_label_y = ymin - (ymax - ymin) * 0.2
        reaction_label_y = ymin - (ymax - ymin) * 0.25
        for name, time_slice in treatments.items():
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

# This would be the ugly solution
# baseline_means = ratios[agonist_slices["baseline"]].mean(axis=0, keepdims=True)
# baseline_stdevs = ratios[agonist_slices["baseline"]].std(axis=0, mean=baseline_means, keepdims=True)
# thresholds = baseline_means + 2*baseline_stdevs

# if method == "derivative":
    # derivs = np.gradient(ratios, axis=0)
    # deriv_means = derivs[agonist_slices["baseline"]].mean(axis=0, keepdims=True)
    # deriv_stdevs = derivs[agonist_slices["baseline"]].std(axis=0, mean=deriv_means, keepdims=True)
    # thresholds = deriv_means + 2*deriv_stdevs

# for agonist, time_window in agonist_slices.items():
#     if agonist == "baseline":
#         continue
#     if method == "previous":
#         thresholds = ratios[time_window.start - 1] + 2*baseline_stdevs
#     amplitudes = ratios[time_window].max(axis=0, keepdims=True) - baseline_means
#     if method != "derivative":
#         reactions = np.where(amplitudes > thresholds, True, False)
#     else:
#         reactions = np.where(derivs[time_window] > thresholds, True, False) # type: ignore
#     file_result[agonist + "_reaction"] = reactions
#     file_result[agonist + "_amp"] = amplitudes
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import math

def process_subdir(subdir: Path, config: dict, process: bool, tabulate: bool, repeat: bool):
    report_path = subdir / f"{subdir}{config["report"]["name"]}{config["report"]["extension"]}"
    if report_path.exists() and not repeat:
        return
    
    measurement_files = [f for f in subdir.glob("*.xlsx") if f != report_path]
    event_file = subdir / f"{subdir}_events.csv"
    event_frames, event_names = parse_events(event_file)
    agonist_names = filter_events(event_names)
    event_slices = create_event_slices(event_frames)
    agonist_slices: dict[str, slice] = {k: v for k, v in zip(agonist_names, event_slices)}
    output_columns = ["cell_ID", "condition", "cell_type"]
    for agonist in agonist_names:
        output_columns.append(agonist + "_reaction")
        output_columns.append(agonist + "_amp")

    if process:
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
            
            # photobleaching correction
            matrix = np.hstack((np.ones_like(x_data), x_data))
            coeffs_340, _, _, _ = np.linalg.lstsq(matrix, cells_340, rcond=None)
            coeffs_380, _, _, _ = np.linalg.lstsq(matrix, cells_380, rcond=None)
            cells_340 = cells_340 - (x_data * coeffs_340[1])
            cells_380 = cells_380 - (x_data * coeffs_380[1])
            
            ratios = np.transpose(cells_340 / cells_380)
            
            # measurements with neurons only will be called "neuron only {number}.xlsx" whereas neuron + DPC is going to
            # be "neuron + DPC {number}.xlsx"
            condition = "N" if "only" in file.name else "N+D"
            
            baseline_means = ratios[agonist_slices["baseline"]].mean(axis=0, keepdims=True)
            baseline_stdevs = ratios[agonist_slices["baseline"]].std(axis=0, mean=baseline_means, keepdims=True)
            thresholds = baseline_means + 2*baseline_stdevs
            for agonist, time_window in agonist_slices.items():
                if agonist == "baseline":
                    continue
                amplitudes = ratios[time_window].max(axis=0, keepdims=True)
                reactions = np.where(amplitudes > thresholds, True, False)
                file_result[agonist + "_reaction"] = reactions
                file_result[agonist + "_amp"] = amplitudes
            
            number_of_cells = ratios.shape[0]
            file_result["cell_ID"] = [x for x in range(cell_ID, cell_ID + number_of_cells)]
            cell_ID += number_of_cells
            file_result["condition"] = [condition for _ in range(number_of_cells)]
             # in the Excel files, columns will be called N1, N2, N3... for neurons and DPC1, DPC2, DPC3... for DPCs
            cell_cols = [c.strip("1234567890") for c in cell_cols]
            file_result["cell_type"] = cell_cols

            report = pd.concat([report, file_result])
        report.to_excel(report_path)


def parse_events(file: Path) -> tuple[list[int], list[str]]:
    """Reads in the event file that describes what happened during the measurement in question.

    Args:
        file (Path): The pathlib.Path object representing the event file. Must be csv.

    Returns:
        tuple[list[int], list[str]]: The first list is of frame numbers where events occured and the second is of string
        descriptions of what happened (what agonist was used there).
    """
    events_df = pd.read_csv(file, header=0)

    frames, events = list(events_df["frame"]), list(events_df["agonist"])
    
    return frames, events


def filter_events(events: list[str]) -> list[str]:
    """This is meant to remove event names which should not be included in the report, such as washouts and high 
    potassium, without making the DataFrame creating line an eyesore.

    Args:
        events (list[str]): The event list.

    Returns:
        list[str]: The same list with undesirable elements removed.
    """
    return [s for s in events if s.lower() not in [" ", "wash", "high k+"]]

def create_event_slices(event_list: list[int]) -> list[slice]:
    """Translates the list of timepoints when events happened into a list of slice objects that represent this
    information as time windows. The output is intended to be used to access the relevant parts of the calcium trace data.

    Args:
        event_list (list[int]): The events as returned by parse_events().

    Returns:
        list[slice]: A list of slices of the form [agonist_start_time:agonist_end_time] where agonist refers to the
        compound added in this particular time window to the cells being measured.
    """
    slices: list[slice] = []

    for i in range(1, len(event_list)):
        slices.append(slice(event_list[i-1], event_list[i]))

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

def make_report():
    """This meant to encapsulate everything currently under the if process: block in process_subdir().
    """
    pass
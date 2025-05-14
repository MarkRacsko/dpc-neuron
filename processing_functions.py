from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import math

def process_subdir(subdir: Path, config: dict, process: bool, tabulate: bool, repeat: bool):
    report_path = subdir / f"{subdir}_report.xlsx"
    if report_path.exists() and not repeat:
        return
    
    measurement_files = [f for f in subdir.glob("*.xlsx") if f != report_path]
    event_file = subdir / f"{subdir}_events.csv"
    event_frames, event_names = parse_events(event_file)
    agonist_names = filter_events(event_names)
    event_slices = create_event_slices(event_frames)
    agonist_slices: dict[str, slice] = {k: v for k, v in zip(agonist_names, event_slices)}
    output_columns = ["cell_ID", "condition"]
    for agonist in agonist_names:
        output_columns.append(agonist + "_reaction")
        output_columns.append(agonist + "_amp")

    if process:
        report = pd.DataFrame(columns=output_columns)
        for file in measurement_files:
            data = pd.read_excel(file, sheet_name="ratio").to_numpy()
            data = np.transpose(data)
            x_data, cell_data = data[0], data[1:]
            cell_ID: int = 0
            condition = 0 # this is intended to represent the experimental condition for this file
            # to be implemented...
            output_df = pd.DataFrame(columns=output_columns)
            for index, trace in enumerate(cell_data):
                # I want to vectorize all of this but let's just get it working for now
                cell_ID += 1
                baseline = trace[:60].mean()
                std = trace[:60].std()
                threshold = baseline + std * 2 # this is idea A from my plan, probably not the best
                result = [cell_ID, condition]
                for agonist, time_window in agonist_slices.items():
                    reaction = bool(np.any(trace[time_window] > threshold)) # the bool conversion may not be necessary
                    amplitude = trace[time_window].max() - baseline
                    result.append(reaction)
                    result.append(amplitude)
                output_df.loc[len(output_df)] = result # appending one row at a time to the end of the df. pd.concat()
                # would require the creation of a new df jjust to hold this one row, which I feel would be pointless




        report.to_excel(report_path)


def process_file(file: Path, event_slices: list[slice], events: list[str]) -> pd.DataFrame:
    # To be finished. For now I just want the thing to work, making it prettier can wait.
    data = pd.read_excel(file, sheet_name="ratio").to_numpy()
    data = np.transpose(data)
    x_data, cell_data = data[0], data[1:]
    result = pd.DataFrame()
    ... # additional steps go here
    return result


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

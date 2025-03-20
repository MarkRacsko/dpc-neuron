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
    event_frames, events = parse_events(event_file)

    if process:
        report = pd.DataFrame(columns=filter_events(events))
        for file in measurement_files:
            result = process_file(file, event_frames, events)
            report = pd.concat([report, result])
        report.to_excel(report_path)


def process_file(file: Path, event_frames: list[int], events: list[str]) -> pd.DataFrame:
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

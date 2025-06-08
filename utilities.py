import math
import pandas as pd
import numpy as np

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
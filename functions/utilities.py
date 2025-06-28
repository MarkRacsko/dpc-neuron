from __future__ import annotations
import math
import pandas as pd
import numpy as np
from typing import Any
from numbers import Rational


def normalize(array: np.ndarray, baseline) -> np.ndarray:
    return array / array[0:baseline].mean()

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

def baseline_threshold(ratios: np.ndarray, agonist_slices: dict[str, slice[int]], file_result: pd.DataFrame, sd_mult: int):
    baseline_means = ratios[agonist_slices["baseline"]].mean(axis=1, keepdims=True)
    baseline_stdevs = ratios[agonist_slices["baseline"]].std(axis=1, mean=baseline_means, keepdims=True)
    thresholds = baseline_means + sd_mult*baseline_stdevs
    
    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        maximums = ratios[time_window].max(axis=1, keepdims=True)
        amplitudes = maximums - baseline_means.flatten()
        reactions = np.where(maximums > thresholds, True, False)
        file_result[agonist + "_reaction"] = reactions
        file_result[agonist + "_amp"] = amplitudes

def previous_threshold(ratios: np.ndarray, agonist_slices: dict[str, slice[int]], file_result: pd.DataFrame, sd_mult: int):
    baseline_means = ratios[:,agonist_slices["baseline"]].mean(axis=1, keepdims=True)
    baseline_stdevs = ratios[:,agonist_slices["baseline"]].std(axis=1, mean=baseline_means, keepdims=True)

    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        thresholds = ratios[:,time_window.start - 10:time_window.start].mean(axis=1, keepdims=False) + sd_mult*baseline_stdevs.flatten()
        maximums = ratios[:,time_window].max(axis=1, keepdims=False)
        amplitudes = maximums - baseline_means.flatten()
        # using amplitudes to determine reactions is wrong because of the baseline substraction
        # (only cells where the max is larger than the threshold by at least the value of the baseline mean would be 
        # considered to have reacted)
        reactions = np.where(maximums > thresholds, True, False)
        file_result[agonist + "_reaction"] = reactions.flatten()
        file_result[agonist + "_amp"] = amplitudes.flatten()

def derivate_threshold(ratios: np.ndarray, agonist_slices: dict[str, slice[int]], file_result: pd.DataFrame, sd_mult: int):
    derivs = np.gradient(ratios, axis=1)
    baseline_deriv_means = derivs[agonist_slices["baseline"]].mean(axis=1, keepdims=True)
    baseline_deriv_stdevs = derivs[agonist_slices["baseline"]].std(axis=1, mean=baseline_deriv_means, keepdims=True)
    thresholds = baseline_deriv_means + sd_mult*baseline_deriv_stdevs.flatten()
    
    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        amplitudes = ratios[time_window].max(axis=1, keepdims=True) - baseline_deriv_means.flatten()
        maximum_derivs = derivs[time_window].max(axis=1, keepdims=False)
        reactions = np.where(maximum_derivs > thresholds, True, False)
        file_result[agonist + "_reaction"] = reactions.flatten()
        file_result[agonist + "_amp"] = amplitudes.flatten()


def validate_config(config: dict[str, dict[str, Any]]) -> str | None:
    message: str = "Errors encountered:"
    starting_len = len(message)
    data_path = config["input"]["target_folder"]
    if not data_path.exists():
        message += "Target not found."
    elif not data_path.is_dir():
        message += "Target isn't a folder."

    method = config["input"]["method"]
    if method not in ["baseline", "previous", "derivative"]:
        message += "The only reaction testing methods implemented are \"baseline\", \"previous\", "
        "and \"derivative\"."
    
    if not isinstance(config["input"]["SD_multiplier"], Rational):
        message += "SD_multiplier must be an integer or floating point number."
    
    if not isinstance(config["input"]["smoothing_range"], int):
        message += "smoothing_range must be an integer number."
    
    if len(message) > starting_len:
        message += "\nExiting."
        return message

def validate_treatments(treatments: dict[str, dict[str, int]]) -> list[bool]:

    previous_end: int = 0
    passed_tests: list[bool] = [True, True, True]
    for agonist in treatments:
        begin = treatments[agonist]["begin"]
        end = treatments[agonist]["end"]

        try:
            begin = int(begin)
        except ValueError:
            passed_tests[0] = False

        try:
            end = int(end)
        except ValueError:
            passed_tests[0] = False

        if begin >= end:
            passed_tests[1] = False

        if begin < previous_end:
            passed_tests[2] = False

        previous_end = end

    return passed_tests

def validate_metadata(folder: str, metadata: dict[str, dict[str, Any]]) -> str:
    errors: str = f"Metadata for folder {folder} has the following errors:"
    starting_len: int = len(errors)
    try:
        conditions = metadata["conditions"]
        try:
            if conditions["ratiometric_dye"].lower() not in {"true", "false"}:
                errors += '\nratiometric_dye value incorrect. Supported values are "true" and "false".'
        except KeyError:
            errors += "\nratiometric_dye key missing or renamed."
        if "group1" not in conditions or "group2" not in conditions:
            errors += '\nGroup key names changed or missing. Correct values are "group1" and "group2".'
    except KeyError:
        errors += "\nConditions section missing or incorrectly named."
    try:
        treatments = metadata["treatments"]
        treatment_errors = validate_treatments(treatments)
        if not treatment_errors[0]:
            errors += "\nAll begin and end values must be integers."
        if not treatment_errors[1]:
            errors += "\nAll agonists must have smaller begin values than end values."
        if not treatment_errors[2]:
            errors += "\nAll begin values must be greater than or equal to the previous row's end value."
    except KeyError:
        errors += "\nTreatments section missing or incorrectly named."


    if len(errors) > starting_len:
        return errors
    else:
        return ""
    

    

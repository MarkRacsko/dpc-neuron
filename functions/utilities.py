from __future__ import annotations
import math
import pandas as pd
import numpy as np
from typing import Any
from numbers import Rational
from pathlib import Path
from numba import njit


def normalize(array: np.ndarray, baseline) -> np.ndarray:
    return array / array[0:baseline].mean()

@njit
def smooth(array: np.ndarray, window_size: int = 5) -> np.ndarray:
    """This function performs a sliding window type smoothing on an array representing a Ca trace.

    Args:
        array (np.ndarray): The array to be smoothed. Must be 1-dimensional.
        window_size (int, optional): The average of this many elements will be taken for the smoothing. Defaults to 5,
        and it should be an odd number.

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

def baseline_threshold(cell_data: np.ndarray, agonist_slices: dict[str, slice[int]], file_result: pd.DataFrame, sd_mult: int):
    """Determines which agonists cells reacted to and measures the response amplitudes. Reaction state is determined by
    comparing the response amplitude with the mean of the baseline + sd_mult * baseline standard deviation.

    Args:
        cell_data (np.ndarray): The 2d numpy array representing data from all cells in the given measurement.
        agonist_slices (dict[str, slice[int]]): A dictionary mapping agonist names to the indices where each agonist was
        applied.
        file_result (pd.DataFrame): The DataFrame storing all output for this measurement file.
        sd_mult (int): Determines by how many standard deviations must a cell's response exceed the baseline mean to be
        considered positive for any given agonist.
    """
    baseline_means = cell_data[agonist_slices["baseline"]].mean(axis=1, keepdims=True)
    baseline_stdevs = cell_data[agonist_slices["baseline"]].std(axis=1, mean=baseline_means, keepdims=True)
    thresholds = baseline_means + sd_mult*baseline_stdevs
    
    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        maximums = cell_data[time_window].max(axis=1, keepdims=True)
        amplitudes = maximums - baseline_means.flatten()
        reactions = np.where(maximums > thresholds, True, False)
        file_result[agonist + "_reaction"] = reactions
        file_result[agonist + "_amp"] = amplitudes

def previous_threshold(cell_data: np.ndarray, agonist_slices: dict[str, slice[int]], file_result: pd.DataFrame, sd_mult: int):
    """Determines which agonists cells reacted to and measures the response amplitudes. Reaction state is determined by
    comparing the response amplitude with the mean of the last 10 values in the previous agonist's time window + 
    sd_mult * baseline standard deviation.

    Args:
        cell_data (np.ndarray): The 2d numpy array representing data from all cells in the given measurement.
        agonist_slices (dict[str, slice[int]]): A dictionary mapping agonist names to the indices where each agonist was
        applied.
        file_result (pd.DataFrame): The DataFrame storing all output for this measurement file.
        sd_mult (int): Determines by how many standard deviations must a cell's response exceed the mean of the last 10
        values in the previous agonist's time window to be considered positive for any given agonist.
    """
    baseline_means = cell_data[:,agonist_slices["baseline"]].mean(axis=1, keepdims=True)
    baseline_stdevs = cell_data[:,agonist_slices["baseline"]].std(axis=1, mean=baseline_means, keepdims=True)

    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        thresholds = cell_data[:,time_window.start - 10:time_window.start].mean(axis=1, keepdims=False) + sd_mult*baseline_stdevs.flatten()
        maximums = cell_data[:,time_window].max(axis=1, keepdims=False)
        amplitudes = maximums - baseline_means.flatten()
        # using amplitudes to determine reactions is wrong because of the baseline substraction
        # (only cells where the max is larger than the threshold by at least the value of the baseline mean would be 
        # considered to have reacted)
        reactions = np.where(maximums > thresholds, True, False)
        file_result[agonist + "_reaction"] = reactions.flatten()
        file_result[agonist + "_amp"] = amplitudes.flatten()

def derivate_threshold(cell_data: np.ndarray, agonist_slices: dict[str, slice[int]], file_result: pd.DataFrame, sd_mult: int):
    """Determines which agonists cells reacted to and measures the response amplitudes. Reaction state is determined by
    comparing the response amplitude with the mean of the baseline's first derivative + sd_mult * standard deviation of
    the baseline's first derivative.

    Args:
        cell_data (np.ndarray): The 2d numpy array representing data from all cells in the given measurement.
        agonist_slices (dict[str, slice[int]]): A dictionary mapping agonist names to the indices where each agonist was
        applied.
        file_result (pd.DataFrame): The DataFrame storing all output for this measurement file.
        sd_mult (int): Determines by how many standard deviations must a cell's response exceed the mean of the
        baseline's first derivative to be considered positive for any given agonist.
    """
    derivs = np.gradient(cell_data, axis=1)
    baseline_deriv_means = derivs[agonist_slices["baseline"]].mean(axis=1, keepdims=True)
    baseline_deriv_stdevs = derivs[agonist_slices["baseline"]].std(axis=1, mean=baseline_deriv_means, keepdims=True)
    thresholds = baseline_deriv_means + sd_mult*baseline_deriv_stdevs.flatten()
    
    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        amplitudes = cell_data[time_window].max(axis=1, keepdims=True) - baseline_deriv_means.flatten()
        maximum_derivs = derivs[time_window].max(axis=1, keepdims=False)
        reactions = np.where(maximum_derivs > thresholds, True, False)
        file_result[agonist + "_reaction"] = reactions.flatten()
        file_result[agonist + "_amp"] = amplitudes.flatten()


def remove_empty_values(treatments: dict[str, dict[str, int | str]]) -> dict[str, dict[str, int | str]]:
    """Checks the treatments dictionary that comes from the table in the GUI metadata editor for empty rows and 
    removes them.

    Args:
        treatments (dict[str, dict[str, int  |  str]]): The treatment dictionary mapping agonist names to a dict of 
        begin and end values.

    Raises:
        ValueError: If there is a treatment where exactly one of the begin and end values is the empty string, ie. the
        user filled only one entry.

    Returns:
        dict[str, dict[str, int | str]]: The same dictionary but with empty rows removed.
    """
    result: dict[str, dict[str, int | str]] = {}
    for treatment, data in treatments.items():
        begin_value = data["begin"]
        end_value = data["end"]
        if begin_value == "" and end_value == "":
            # this is an empty row, exclude it
            continue
        elif begin_value == "" or end_value == "":
            # this row has only 1 missing value, this is an error
            raise ValueError
        else:
            # this row is good
            result[treatment] = data
    return result

def validate_config(config: dict[str, dict[str, Any]]) -> str:
    """Checks the values of the config dictionary, called before we save it to disk.

    Args:
        config (dict[str, dict[str, Any]]): The Python dict representation of our config.toml.

    Returns:
        str: An error message describing the problems encountered, or an empty string if there are no problems.
    """
    message: str = "Errors encountered:"
    starting_len = len(message)
    try:
        data_path = Path(config["input"]["target_folder"])
        if not data_path.exists():
            message += "\n- target folder not found."
        elif not data_path.is_dir():
            message += "\n- target isn't a folder."
    except KeyError:
        message += "\n- target_folder key missing from input section"

    try:
        method = config["input"]["method"]
        if method not in ["baseline", "previous", "derivative"]:
            message += "\n- method value incorrect; only \"baseline\", \"previous\", and \"derivative\" are accepted"
    except KeyError:
        message += "\n- method key missing from input section"
    
    try:
        if not isinstance(config["input"]["SD_multiplier"], Rational):
            message += "\n- SD_multiplier value must be an integer or floating point number"
    except KeyError:
        message += "\n- SD_multiplier key missing from input section"
    
    try:
        if not isinstance(config["input"]["smoothing_range"], int):
            message += "\n- smoothing_range value must be an integer number."
        elif config["input"]["smoothing_range"] %2 == 0:
            message += "\n- smoothing_range value must not be an odd number"
    except KeyError:
        message += "\n- smoothing_range key missing from input section"

    try:
        if not isinstance(config["output"]["report_name"], str):
            message += "\n- report_name value must be a string"
    except KeyError:
        message += "\n- report_name key missing from output section"

    try:
        if not isinstance(config["output"]["summary_name"], str):
            message += "\n- summary_name value must be a string"
    except KeyError:
        message += "\n- summary_name key missing from output section"
    
    if len(message) > starting_len:
        message += ".\nExiting."
        return message
    else:
        return ""

def validate_treatments(treatments: dict[str, dict[str, int | str]]) -> list[bool]:
    """Checks values in the treatment dictionary for correctness. Returns a list of booleans that represent which tests
    were passed and which failed.

    Args:
        treatments (dict[str, dict[str, int  |  str]]): The treatments section of the metadata file being edited as a
        Python dict. The int | str type hint is to make the type checker happy, in reality the input will always be str.

    Returns:
        list[bool]: Booleans representing the success or failure of each test. Is a list because tuples are immutable.
    """

    previous_end: int = 0
    # we start by assuming that the tests pass, and set a value to False whenever the corresponding test fails
    passed_tests: list[bool] = [True, True, True]
    for agonist in treatments:
        begin = treatments[agonist]["begin"]
        end = treatments[agonist]["end"]

        try:
            begin = int(begin)
            end = int(end)
            if begin >= end:
                passed_tests[1] = False

            if begin < previous_end:
                passed_tests[2] = False
            
            previous_end = end 
        except ValueError: # one or both of the values could not be converted to an int
            passed_tests[0] = False # first (0th) test logically, since the others cannot be carried out if it fails

    return passed_tests

def validate_metadata(folder: str, metadata: dict[str, dict[str, Any]]) -> str:
    """Checks the metadata dictionary before we save it to disk, called by the Save Metadata button's command.

    Args:
        folder (str): The selected folder. Is here to help provide feedback because the editor does not display what
        folder was selected.
        metadata (dict[str, dict[str, Any]]): The folder's metadata.toml as a Python dict.

    Returns:
        str: An error message describing the problems encountered, or an empty string if there are no problems.
    """
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

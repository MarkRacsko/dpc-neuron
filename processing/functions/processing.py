from __future__ import annotations
import math

from numba import njit
import numpy as np
import pandas as pd


def normalize(array: np.ndarray, baseline: int) -> np.ndarray:
    """Normalizes values in a Ca trace to the mean of the baseline time period.

    Args:
        array (np.ndarray): The Ca trace to normalize.
        baseline (int): Length of the baseline in number of frames.

    Returns:
        np.ndarray: The normalized array.
    """
    return array / array[0:baseline].mean()

@njit # because this is by far the slowest of my analysis functions
def smooth(array: np.ndarray, window_size: int = 5) -> np.ndarray:
    """This function performs a sliding window type smoothing on an array representing an individual Ca trace.

    Args:
        array (np.ndarray): The array to be smoothed. Must be 1-dimensional.
        window_size (int, optional): The average of this many elements will be taken for the smoothing. Defaults to 5,
        it should be an odd number, and not larger than the square root of the array's length (ie. the length of the
        measurement in frames).

    Raises:
        ValueError: If the input array is of the incorrect shape, or the selected window_size is too large or it isn't odd.

    Returns:
        np.ndarray: The smoothed array.
    """
    # these checks are strictly speaking not necessary in this project, but their performance impact should be minimal
    # so I'm keeping them as a reminder (the user has no control over the array dimensions, and the window_size is also
    # validated elsewhere)
    if array.ndim != 1:
        raise ValueError("Input array must be 1-dimensional.")
    if window_size % 2 == 0:
        raise ValueError("Window size should be an odd number.")
    length = len(array)
    if window_size > math.sqrt(length):
        raise ValueError("Window size should not be larger than the square root of the length of the array.")

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
    baseline_means = cell_data[:,agonist_slices["baseline"]].mean(axis=1, keepdims=True)
    baseline_stdevs = cell_data[:,agonist_slices["baseline"]].std(axis=1, mean=baseline_means, keepdims=False)
    thresholds = baseline_means.flatten() + sd_mult*baseline_stdevs
    
    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        maximums = cell_data[:,time_window].max(axis=1, keepdims=False)
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
    baseline_stdevs = cell_data[:,agonist_slices["baseline"]].std(axis=1, mean=baseline_means, keepdims=False)

    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        prev_means = cell_data[:,time_window.start - 10:time_window.start].mean(axis=1, keepdims=False)
        thresholds = prev_means + sd_mult*baseline_stdevs
        maximums = cell_data[:,time_window].max(axis=1, keepdims=False)
        amplitudes = maximums - prev_means.flatten()
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
    baseline_deriv_means = derivs[:,agonist_slices["baseline"]].mean(axis=1, keepdims=True)
    baseline_deriv_stdevs = derivs[:,agonist_slices["baseline"]].std(axis=1, mean=baseline_deriv_means, keepdims=False)
    thresholds = baseline_deriv_means.flatten() + sd_mult*baseline_deriv_stdevs
    
    for agonist, time_window in agonist_slices.items():
        if agonist == "baseline":
            continue
        amplitudes = cell_data[:,time_window].max(axis=1, keepdims=False) - baseline_deriv_means.flatten()
        maximum_derivs = derivs[:,time_window].max(axis=1, keepdims=False)
        reactions = np.where(maximum_derivs > thresholds, True, False)
        file_result[agonist + "_reaction"] = reactions.flatten()
        file_result[agonist + "_amp"] = amplitudes.flatten()

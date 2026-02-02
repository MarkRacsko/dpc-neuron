from __future__ import annotations

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
    derivs = np.gradient(f=cell_data, axis=1)
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

def neuron_filter(cell_data: np.ndarray, agonist_slices: dict[str, slice[int]], file_result: pd.DataFrame, 
                  amp_threshold: float, cv_threshold: float):
    baseline, potassium = cell_data[:, agonist_slices["baseline"]], cell_data[:, agonist_slices["KCl"]]
    baseline_means = np.mean(baseline, axis=1)
    potassium_cv = np.std(potassium, axis=1) / np.mean(potassium, axis=1)
    potassium_amp = np.max(potassium - baseline_means[:, np.newaxis], axis=1)

    amp_mask = potassium_amp > amp_threshold
    cv_mask = potassium_cv > cv_threshold

    file_result["KCl amp filter"] = amp_mask
    file_result["KCl cv filter"] = cv_mask

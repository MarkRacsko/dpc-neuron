from numbers import Rational
from pathlib import Path
from typing import Any


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
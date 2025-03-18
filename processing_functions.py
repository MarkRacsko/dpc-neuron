from pathlib import Path
import pandas as pd
import numpy as np

def process_target(target: str, process_flag: bool, tab_flag: bool, re_flag: bool) -> None:
    data_path = Path(target)
    if not data_path.is_dir():
        print("Target not found or isn't a folder. Exiting.")

    for subdir in data_path.iterdir():
        if not subdir.is_dir():
            continue

        report_path = subdir / f"{subdir}_report.xlsx"
        if report_path.exists() and not re_flag:
            continue

        measurement_files = [f for f in subdir.glob("*.xlsx") if f != report_path]
        for file in measurement_files:
            input_df = pd.read_excel(file, sheet_name="ratio")
            # actual processing work goes here...

from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

def process_subdir(subdir: Path, config: dict, process: bool, tabulate: bool, repeat: bool):
    report_path = subdir / f"{subdir}_report.xlsx"
    if report_path.exists() and not repeat:
        return
    
    measurement_files = [f for f in subdir.glob("*.xlsx") if f != report_path]
    event_file = subdir / f"{subdir}_events.csv"
    event_frames, events = parse_events(event_file)

    if process:
        report = pd.DataFrame(columns=config["input"]["agonists"])
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
    events_df = pd.read_csv(file, header=0)

    frames, events = list(events_df["frame"]), list(events_df["agonist"])
    
    return frames, events
        

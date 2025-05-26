import argparse
import toml
from pathlib import Path
from processing_functions import process_subdir


def main():

    with open("./config.toml", "r") as f:
        config = toml.load(f)
    
    target_help = "Path to the folder you want to process. Individual measurement results must be in subfolders of this folder, files in the same subfolder will be interpreted as belonging to the same experiment/day."
    r_help = "If set, process (and/or tabulate) every measurment found in the target folder. Defaults to False, in which case measurements that already have a report associated with them are ignored."
    group_help = "The following are mutually exclusive flags that govern the program's behaviour. One must be chosen."
    p_help = "Process measurements and make reports for each subfolder that collects results from measurements found there."
    t_help = "Go through subfolders and compile an overall report from any report files found."
    pt_help = "Perform both of the above functions, processing individual measurements and compiling the overall report at the same time."
    g_help = "Make line plots for every cell in the measured dataset. Resultant files will be placed in newly created subdirectories for each measurement Excel file."

    parser = argparse.ArgumentParser()
    parser.add_argument("TARGET", nargs="?", default="./data", help=target_help)
    parser.add_argument("-r", "--repeat", action="store_true", default=False, help=r_help)
    group = parser.add_argument_group(title="processing options", description=group_help)
    excl_group = group.add_mutually_exclusive_group(required=True)
    excl_group.add_argument("-p", "--process", action="store_true", help=p_help)
    excl_group.add_argument("-t", "--tabulate", action="store_true", help=t_help)
    excl_group.add_argument("-pt", action="store_true", help=pt_help)
    parser.add_argument("-g", "--graph", action="store_true", default=False, help=g_help)
    args = parser.parse_args()

    processing: bool = False
    tabulating: bool = False
    if args.process or args.pt:
        processing = True
    if args.tabulate or args.pt:
        tabulating = True

    data_path = Path(args.TARGET)
    if not data_path.is_dir():
        print("Target not found or isn't a folder. Exiting.")
        exit()

    method = config["input"]["method"]
    if method not in ["baseline", "previous", "derivative"]:
        raise ValueError("The only reaction testing methods implemented are \"baseline\", \"previous\", "
        "and \"derivative\". See README.md")
    
    for subdir in data_path.iterdir():
        if not subdir.is_dir():
            continue
        
        report_path = subdir / f"{config["report"]["name"]}{subdir.name}{config["report"]["extension"]}"
        if report_path.exists() and not args.repeat:
            continue
        
        process_subdir(subdir, report_path, method, processing, tabulating, args.graph)


if __name__ == "__main__":
    main()
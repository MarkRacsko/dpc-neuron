import argparse
import toml
from pathlib import Path
from classes.analyzer import DataAnalyzer
from classes.toml_data import Config
from functions.validation import validate_config, validate_data_path
from tkinter import IntVar


def main():
    try:
        with open("./config.toml", "r") as f:
            config = toml.load(f)
            errors = validate_config(config)
            if errors:
                print(errors)
                exit()           
            config = Config(config)
    except FileNotFoundError:
        print("Config file needed. Should not have deleted or renamed it.")
        exit()
    
    default_target = config.input.target_folder
    target_help = "Path to the folder you want to process. Individual measurement results must be in subfolders of this folder, files in the same subfolder will be interpreted as belonging to the same experiment/day."
    r_help = "If set, process (and/or tabulate) every measurment found in the target folder. Defaults to False, in which case measurements that already have a report associated with them are ignored."
    group_help = "The following are mutually exclusive flags that govern the program's behaviour. One must be chosen."
    p_help = "Process measurements and make reports for each subfolder that collects results from measurements found there."
    t_help = "Go through subfolders and compile an overall report from any report files found."
    pt_help = "Perform both of the above functions, processing individual measurements and compiling the overall report at the same time."
    g_help = "Make line plots for every cell in the measured dataset. Resultant files will be placed in newly created subdirectories for each measurement Excel file."

    parser = argparse.ArgumentParser()
    parser.add_argument("TARGET", nargs="?", default=default_target, help=target_help)
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
    # this is so the analyzer object will have access to the target path for saving the tabulated summary
    # (this value is not the same as what the config started with if the user provided the TARGET command line arg)
    config.input.target_folder = data_path

    errors = validate_data_path(data_path)
    if errors:
        print("Error:")
        print(errors)
        print("Exiting.")
        exit()
    
    data_analyzer = DataAnalyzer(config, IntVar(), args.repeat)     
    data_analyzer.create_caches() 
    error_list = data_analyzer.create_subdir_instances()
    for error in error_list:
        print(error) # if the list is empty, ie. nothing went wrong, nothing will be printed
    
    error_list = [] # reset the errors to be empty
    if processing:
        data_analyzer.process_data(error_list)
        for error in error_list:
            print(error) # if the list is empty, ie. nothing went wrong, nothing will be printed
    if tabulating:
        data_analyzer.summarize_results()
    if args.graph:
        data_analyzer.graph_data()


if __name__ == "__main__":
    main()
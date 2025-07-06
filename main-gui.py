import toml
from pathlib import Path
from tkinter import messagebox
from classes.gui import MainWindow
from functions.validation import validate_config
from functions.toml_handling import dict_to_config

def main():
    config_path = Path("./config.toml")
    try:
        with open(config_path, "r") as f:
            config = toml.load(f)
    except FileNotFoundError:
        messagebox.showerror(message="Config file needed. Should not have deleted or renamed it.")
        exit()
    errors = validate_config(config)
    if errors:
        messagebox.showerror(message=errors)
        exit()
    config = dict_to_config(config)
    MainWindow(config)

if __name__ == "__main__":
    main()
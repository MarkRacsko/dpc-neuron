import toml
from classes import MainWindow
from pathlib import Path
from tkinter import messagebox

def main():
    config_path = Path("./config.toml")
    try:
        with open(config_path, "r") as f:
            config = toml.load(f)
    except FileNotFoundError:
        messagebox.showerror(message="Config file needed. Should not have deleted or renamed it.")
        exit()
    
    MainWindow(config)

if __name__ == "__main__":
    main()
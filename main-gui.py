import toml
from classes import MainWindow
from pathlib import Path

def main():
    config_path = Path("./config.toml")
    try:
        with open(config_path, "r") as f:
            config = toml.load(f)
            config["input"]["interface"] = "GUI"
            # This is done because errors need to be printed if we are running the CLI version but raised if
            # we're in the GUI. We hand this config dict over to the DataAnalyzer anyway, so might as well store
            # this information in it.
    except FileNotFoundError:
        # better error system to be implemented
        print("Config file needed. Should not have deleted it...")
        exit()
    
    MainWindow(config)

if __name__ == "__main__":
    main()
import toml
from classes import MainWindow
from pathlib import Path

def main():
    config_path = Path("./config.toml")
    try:
        with open(config_path, "r") as f:
            config = toml.load(f)
    except FileNotFoundError:
        # better error system to be implemented
        print("Config file needed. Should not have deleted it...")
        exit()
    
    MainWindow(config)

if __name__ == "__main__":
    main()
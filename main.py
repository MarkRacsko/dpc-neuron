import toml
import sys
from pathlib import Path
from tkinter import messagebox
from interface.gui_main import MainWindow
from interface.gui_constants import CONFIG_TEMPLATE
from processing.classes.toml_data import Config
from processing.functions.validation import validate_config

def main():
    standalone_mode = getattr(sys, "frozen", False)

    if standalone_mode:
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent

    config_path = base_path / "config.toml"

    if config_path.exists():
        with open(config_path, "r") as f:
            config = toml.load(f)
        errors = validate_config(config)
        if errors:
            messagebox.showerror(message=errors)
            exit()
        config = Config(config)

    else:
        config = Config(CONFIG_TEMPLATE)
        with open(config_path, "w") as f:
            toml.dump(config.to_dict(), f)
    
    MainWindow(config)

if __name__ == "__main__":
    main()
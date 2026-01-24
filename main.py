import toml
import sys
from pathlib import Path
from tkinter import messagebox
from interface.gui_main import MainWindow
from interface.gui_constants import CONFIG_TEMPLATE
from processing.classes.toml_data import Config
from processing.functions.validation import validate_config

def main() -> int:
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
            return 1
        config = Config(config)

    else:
        config = Config(CONFIG_TEMPLATE)
        with open(config_path, "w") as f:
            toml.dump(config.to_dict(), f)
    
    MainWindow(config)
    return 0

if __name__ == "__main__":
    exit_status: int = main()
    raise SystemExit(exit_status)
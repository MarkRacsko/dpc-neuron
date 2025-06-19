import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from typing import Any

FONT_L = ("Arial", 18)
FONT_S = ("Arial", 16)

BASE_X = 20
BASE_Y = 20
PADDING_Y = 40
PADDING_X = 120

DISPLAY_MODES: dict[str, str] = {
    "default": "460x250",
    "config": "460x400",
    "metadata": "460x400"
}

class GUI:
    def __init__(self, config: dict[str, dict[str, Any]]) -> None:
        self.config = config
        self.root = tk.Tk()
        self.root.title("Ca Measurement Analyzer")
        
        self.current_mode = tk.StringVar(value="default")
        self.current_mode.trace_add("write", self.resize_window)
        
        self.root.geometry(DISPLAY_MODES[self.current_mode.get()])
        self.root.resizable(False, False)

        # Browse target folder
        self.target_label = tk.Label(self.root, text="Data folder:", font=FONT_S)
        self.target_label.place(x=BASE_X, y=BASE_Y)
        self.path_label = tk.Label(self.root, text="Selected: not yet", font=FONT_S)
        self.path_label.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y)
        self.target_path = tk.StringVar(value="./data")
        self.target_button = tk.Button(self.root, text="Browse...", font=FONT_S, command=self.select_folder)
        self.target_button.place(x=BASE_X + PADDING_X, y=BASE_Y, width=100, height=30)
        
        # Processing checkbox
        self.check_p_state = tk.IntVar()
        self.check_p = tk.Checkbutton(self.root, text="Process", font=FONT_S, variable=self.check_p_state)
        self.check_p.place(x=BASE_X, y=BASE_Y + PADDING_Y)

        # Tabulation checkbox
        self.check_t_state = tk.IntVar()
        self.check_t = tk.Checkbutton(self.root, text="Tabulate", font=FONT_S, variable=self.check_t_state)
        self.check_t.place(x=BASE_X, y=BASE_Y + 2* PADDING_Y)

        # Graphing checkbox
        self.check_g_state = tk.IntVar()
        self.check_g = tk.Checkbutton(self.root, text="Make graphs", font=FONT_S, variable=self.check_g_state)
        self.check_g.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y + PADDING_Y)

        # Repeat checkbox
        self.check_r_state = tk.IntVar()
        self.check_r = tk.Checkbutton(self.root, text="Repeat", font=FONT_S, variable=self.check_r_state)
        self.check_r.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y + 2 * PADDING_Y)
        
        # Analyze button
        self.analyze_button = tk.Button(self.root, text="Analyze", font=FONT_L, command=self.analyze_button_press)
        self.analyze_button.place(x=BASE_X, y=4 * PADDING_Y, width=120, height=60)

        # Config button
        self.config_button = tk.Button(self.root, text="Edit\nconfig", font=FONT_S, command=self.config_button_press)
        self.config_button.place(x=BASE_X + 1.2 * PADDING_X, y=4 * PADDING_Y, width=120, height=60)

        # Metadata button
        self.metadata_button = tk.Button(self.root, text="Edit\nmetadata", font=FONT_S, command=self.metadata_button_press)
        self.metadata_button.place(x=BASE_X + 2.4 * PADDING_X, y=4 * PADDING_Y, width=120, height=60)

        # Config editor section
        if self.current_mode.get() == "config":
            pass

        # Metadata editor section
        if self.current_mode.get() == "metadata":
            pass

        self.root.protocol("WM_DELETE_WINDOW", exit) # Regression but I'm willing to accept that for now.
        self.root.mainloop()
    
    def resize_window(self, *args):
        self.root.geometry(DISPLAY_MODES[self.current_mode.get()])

    def select_folder(self) -> None:
        """Called when pressing the button to select the output folder where results will be saved.
        """
        path = filedialog.askdirectory(title="Select a folfer")
        if path:
            self.target_path = path
            self.target_label.config(text="Selected: yes")

    def analyze_button_press(self) -> None:
        print("To be implemented!")

    def config_button_press(self) -> None:
        self.current_mode.set("config")

    def metadata_button_press(self) -> None:
        self.current_mode.set("metadata")
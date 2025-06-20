import tkinter as tk
import toml
from tkinter import messagebox
from tkinter import filedialog
from typing import Any
from pathlib import Path
from .analyzer import DataAnalyzer
from collections import namedtuple

FONT_L = ("Arial", 18)
FONT_M = ("Arial", 16)
FONT_S = ("Arial", 12)

BASE_X = 20
BASE_Y = 20
PADDING_Y = 30
PADDING_X = 120
PANEL_Y = 160
SECTION_1_BASE_Y = 20 #180
SECTION_2_BASE_Y = 180 #340
EDITOR_PADDING_X = 200
OFFSCREEN_X = 500
BOTTOM_BUTTONS_Y = 310
BOTTOM_BUTTONS_X = 35
BOTTOM_BUTTONS_PADDING_X =100

DISPLAY_MODES: dict[str, str] = {
    "config": "460x480",
    "metadata": "460x800"
}

Treatment = namedtuple("Treatment", ["name", "begin", "end"])

class MainWindow:
    def __init__(self, config: dict[str, dict[str, Any]]) -> None:
        self.config = config
        self.metadata = {}
        self.root = tk.Tk()
        self.root.title("Ca Measurement Analyzer")
        
        self.current_mode = tk.StringVar(value="config")
        self.current_mode.trace_add("write", self.resize_window)
        
        
        self.root.resizable(False, True)

        # Browse target folder
        self.target_label = tk.Label(self.root, text="Data folder:", font=FONT_M)
        self.target_path = tk.StringVar(value="./data")
        
        # Processing checkbox
        self.check_p_state = tk.IntVar()
        self.check_p = tk.Checkbutton(self.root, text="Process", font=FONT_M, variable=self.check_p_state)
        self.check_p.place(x=BASE_X, y=BASE_Y)

        # Tabulation checkbox
        self.check_t_state = tk.IntVar()
        self.check_t = tk.Checkbutton(self.root, text="Tabulate", font=FONT_M, variable=self.check_t_state)
        self.check_t.place(x=BASE_X, y=BASE_Y + PADDING_Y)

        # Graphing checkbox
        self.check_g_state = tk.IntVar()
        self.check_g = tk.Checkbutton(self.root, text="Make graphs", font=FONT_M, variable=self.check_g_state)
        self.check_g.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y)

        # Repeat checkbox
        self.check_r_state = tk.IntVar()
        self.check_r = tk.Checkbutton(self.root, text="Repeat", font=FONT_M, variable=self.check_r_state)
        self.check_r.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y + PADDING_Y)
        
        # Analyze button
        self.analyze_button = tk.Button(self.root, width=8, text="Analyze", font=FONT_L, command=self.analyze_button_press)
        self.analyze_button.place(x=BASE_X, y=3 * PADDING_Y, width=120, height=60)

        # Config button
        self.config_button = tk.Button(self.root, width=8, text="Edit\nconfig", font=FONT_M, command=self.config_button_press)
        self.config_button.place(x=BASE_X + 1.2 * PADDING_X, y=3 * PADDING_Y, width=120, height=60)

        # Metadata button
        self.metadata_button = tk.Button(self.root, width=8, text="Edit\nmetadata", font=FONT_M, command=self.metadata_button_press)
        self.metadata_button.place(x=BASE_X + 2.4 * PADDING_X, y=3 * PADDING_Y, width=120, height=60)

        self.root.update_idletasks()
        # Config editor panel
        self.config_panel = ConfigFrame(self.root, self.config, self.config_button.winfo_width(), width=460, height=320)

        # Metadata editor panel
        self.metadata_panel = MetadataFrame(self.root, width=460, height=640)
        # Folder selector button that only appears in metadata mode
        self.metadata_path = tk.StringVar()
        self.metabata_browse_button = tk.Button(self.root, text="Select\nfolder", font=FONT_M, command=self.select_measurement_folder_and_load_metadata)
        

        self.root.update_idletasks()
        # this line is here and not at the beginning so that the window won't jump around:
        self.root.geometry(DISPLAY_MODES[self.current_mode.get()])
        self.config_button_press() # this is here so the program can start in the config layout
        self.root.protocol("WM_DELETE_WINDOW", exit) # Regression but I'm willing to accept that for now.
        self.root.mainloop()
    
    def resize_window(self, *args):
        self.root.geometry(DISPLAY_MODES[self.current_mode.get()])

    def analyze_button_press(self) -> None:
        data_path = Path(self.target_path.get())
        if not data_path.exists():
            # better error handling needed, for now I will leave it as-is
            print("Target not found. Exiting.")
            exit()
        if not data_path.is_dir():
            print("Target isn't a folder. Exiting.")
            exit()

        method = self.config["input"]["method"]
        if method not in ["baseline", "previous", "derivative"]:
            # this is here and not where the check is actually relevant in order to avoid unnecessary IO and processing
            # operations if the user made a mistake and the program would crash anyway
            print("The only reaction testing methods implemented are \"baseline\", \"previous\", "
            "and \"derivative\". See README.md")
            exit()
        
        # this is so the analyzer object will have access to the target path for saving the tabulated summary
        # (this value is not the same as what the config started with if the user provided the TARGET command line arg)
        self.config["input"]["target_folder"] = data_path
        
        data_analyzer = DataAnalyzer(self.config, bool(self.check_r_state.get()))
        for subdir_path in data_path.iterdir():
            if subdir_path.is_dir():        
                data_analyzer.create_subdir_instance(subdir_path)
            
        if self.check_p_state.get():
            data_analyzer.process_data()
        if self.check_t_state.get():
            data_analyzer.tabulate_data()
        if self.check_g_state.get():
            data_analyzer.graph_data()

    def config_button_press(self) -> None:
        """
        Sets the mode (which determines window size) to config and changes the editor section's labels, textboxes,
        and buttons appropriately.
        """
        self.current_mode.set("config")
        self.config_panel.place(x=0, y=PANEL_Y)
        self.metadata_panel.place(x=OFFSCREEN_X)    
        self.metabata_browse_button.place(x=OFFSCREEN_X)

    def metadata_button_press(self) -> None:
        """
        Sets the mode (which determines window size) to metadata and changes the editor section's labels, textboxes,
        and buttons appropriately.
        """
        if not self.metadata_path.get():
            self.select_measurement_folder_and_load_metadata()

        self.current_mode.set("metadata")
        self.metadata_panel.metadata = self.metadata
        self.metadata_panel.update_frame()
        self.config_panel.place(x=OFFSCREEN_X)
        self.metadata_panel.place(x=0, y=PANEL_Y)
        self.metabata_browse_button.place(x=BASE_X + 2.4 * PADDING_X, y=180, width=self.metadata_button.winfo_width(), height=self.metadata_button.winfo_height())
    
    def select_measurement_folder_and_load_metadata(self) -> None:
        path = filedialog.askdirectory(title="Select measurement folder")
        if path:
            self.metadata_path.set(path)
        
            with open(Path(self.metadata_path.get()) / "metadata.toml", "r") as f:
                self.metadata = toml.load(f)


class ConfigFrame(tk.Frame):
    def __init__(self, parent, config: dict[str, dict[str, Any]], save_button_size: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.target_path = tk.StringVar(value="./data")
        self.config = config
        # Input section
        self.sec_1_label = tk.Label(self, text="Input section", font=FONT_L)
        self.sec_1_label.place(x=BASE_X, y=SECTION_1_BASE_Y)

        # Target folder selection
        self.sec_1_key_1_label = tk.Label(self, text="Target folder:", font=FONT_M)
        self.sec_1_key_1_label.place(x=BASE_X, y=SECTION_1_BASE_Y + PADDING_Y)
        self.sec_1_value_1_button = tk.Button(self, text="Browse...",font=FONT_M, command=self.select_folder)
        self.sec_1_value_1_button.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + PADDING_Y)

        # Method
        self.sec_1_key_2_label = tk.Label(self, text="Method:", font=FONT_M)
        self.sec_1_key_2_label.place(x=BASE_X, y=SECTION_1_BASE_Y + 2 * PADDING_Y)
        self.selected_method = tk.StringVar()
        self.selected_method.set(self.config["input"]["method"])
        self.method_options: list[str] = ["baseline", "previous", "derivative"]
        self.sec_1_value_2_menu = tk.OptionMenu(self, self.selected_method, *self.method_options)
        self.sec_1_value_2_menu.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + 10 + 2 * PADDING_Y, width=120)

        # SD multiplier
        self.sec_1_key_3_label = tk.Label(self, text="SD multiplier:", font=FONT_M)
        self.sec_1_key_3_label.place(x=BASE_X, y=SECTION_1_BASE_Y + 3 * PADDING_Y)
        self.sec_1_value_3_box = tk.Text(self, width=10, height=1, font=FONT_M)
        self.sec_1_value_3_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + 10 + 3 * PADDING_Y)
        self.sec_1_value_3_box.delete("1.0", "end")
        self.sec_1_value_3_box.insert("1.0", self.config["input"]["SD_multiplier"])

        # Smoothing range
        self.sec_1_key_4_label = tk.Label(self, text="Smoothing range:", font=FONT_M)
        self.sec_1_key_4_label.place(x=BASE_X, y=SECTION_1_BASE_Y + 4 * PADDING_Y)
        self.sec_1_value_4_box = tk.Text(self, width=10, height=1, font=FONT_M)
        self.sec_1_value_4_box.delete("1.0", "end")
        self.sec_1_value_4_box.insert("1.0", self.config["input"]["smoothing_range"])
        self.sec_1_value_4_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + 10 + 4 * PADDING_Y)

        # Output section
        self.sec_2_label = tk.Label(self, text="Output section", font=FONT_L)
        self.sec_2_label.place(x=BASE_X, y=SECTION_2_BASE_Y)

        # Report name
        self.sec_2_key_1_label = tk.Label(self, text="Report name:", font=FONT_M)
        self.sec_2_key_1_label.place(x=BASE_X, y=SECTION_2_BASE_Y + PADDING_Y)
        self.sec_2_value_1_box = tk.Text(self, width=10, height=1, font=FONT_M)
        self.sec_2_value_1_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_2_BASE_Y + PADDING_Y)
        self.sec_2_value_1_box.delete("1.0", "end")
        self.sec_2_value_1_box.insert("1.0", self.config["output"]["report_name"])

        # Summary name
        self.sec_2_key_2_label = tk.Label(self, text="Summary name:", font=FONT_M)
        self.sec_2_key_2_label.place(x=BASE_X, y=SECTION_2_BASE_Y + 2 * PADDING_Y)
        self.sec_2_value_2_box = tk.Text(self, width=10, height=1, font=FONT_M)
        self.sec_2_value_2_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_2_BASE_Y + 2 * PADDING_Y)
        self.sec_2_value_2_box.delete("1.0", "end")
        self.sec_2_value_2_box.insert("1.0", self.config["output"]["summary_name"])
        
        # Save button for config file
        self.save_config_button = tk.Button(self, text="Save", font=FONT_L, command=self.save_config)
        self.save_config_button.place(x=BASE_X + 1.2 * PADDING_X, y=SECTION_2_BASE_Y + 10 + 3 * PADDING_Y, width=save_button_size, height=30)

    def select_folder(self) -> None:
        """Called when pressing the button to select the output folder where results will be saved.
        """
        path = filedialog.askdirectory(title="Select a folfer")
        if path:
            self.target_path.set(path)

    def save_config(self) -> None:
        self.config["input"]["target_folder"] = self.target_path.get()
        self.config["input"]["method"] = self.selected_method.get()
        try:
            self.config["input"]["SD_multiplier"] = int(self.sec_1_value_3_box.get("1.0", "end-1c"))
            self.config["input"]["smoothing_range"] = int(self.sec_1_value_4_box.get("1.0", "end-1c"))
        except ValueError:
            # error message to be implemented
            pass
        self.config["output"]["report_name"] = self.sec_2_value_1_box.get("1.0", "end-1c")
        self.config["output"]["summary_name"] = self.sec_2_value_2_box.get("1.0", "end-1c")

        with open(Path("./config.toml"), "w") as f:
            toml.dump(self.config, f)


class MetadataFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.target_path = tk.StringVar(value="./data")
        # The metadata dictionary needs to be initialized with the correct keys in order to avoid KeyErrors
        self.metadata = {
            "conditions": {
                "ratiometric_dye": 1,
                "group1": "",
                "group2": ""
            },
            "treatments": {}
            }

    def update_frame(self):
        """
        Updates this Frame with the correct metadata information. The reason these things are here and not in __init__
        is that this is how we can update the displayed information after the object is instantiated with dummy values.
        """
        # Conditions section
        self.sec_1_label = tk.Label(self, text="Conditions section", font=FONT_L)
        self.sec_1_label.place(x=BASE_X, y=SECTION_1_BASE_Y)

        # Ratiometric dye
        self.sec_1_key_1_label = tk.Label(self, text="Ratiometric dye:", font=FONT_M)
        self.sec_1_key_1_label.place(x=BASE_X, y=SECTION_1_BASE_Y + PADDING_Y)
        self.sec_1_value_1_button = tk.Button(self, text=f"{self.metadata["conditions"]["ratiometric_dye"]}", font=FONT_M, command=self.ratiometric_switch)
        self.sec_1_value_1_button.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + PADDING_Y)

        # Group1
        self.sec_1_key_2_label = tk.Label(self, text="Group 1:", font=FONT_M)
        self.sec_1_key_2_label.place(x=BASE_X, y=SECTION_1_BASE_Y + 2 * PADDING_Y)
        self.sec_1_value_2_box = tk.Text(self, width=15, height=1, font=FONT_M)
        self.sec_1_value_2_box.delete("1.0", "end")
        self.sec_1_value_2_box.insert("1.0", self.metadata["conditions"]["group1"])
        self.sec_1_value_2_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + 10 + 2 * PADDING_Y)

        # Group2
        self.sec_1_key_3_label = tk.Label(self, text="Group 2:", font=FONT_M)
        self.sec_1_key_3_label.place(x=BASE_X, y=SECTION_1_BASE_Y + 3 * PADDING_Y)
        self.sec_1_value_3_box = tk.Text(self, width=15, height=1, font=FONT_M)
        self.sec_1_value_3_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + 10 + 3 * PADDING_Y)
        self.sec_1_value_3_box.delete("1.0", "end")
        self.sec_1_value_3_box.insert("1.0", self.metadata["conditions"]["group2"])

        # Treatment section
        self.sec_2_label = tk.Label(self, text="Treatment section", font=FONT_L)
        self.sec_2_label.place(x=BASE_X, y=SECTION_2_BASE_Y)

        # Agonist
        self.sec_2_key_1_label = tk.Label(self, text="Agonist:", font=FONT_M)
        self.sec_2_key_1_label.place(x=BASE_X, y=SECTION_2_BASE_Y + PADDING_Y)
        self.sec_2_value_1_box = tk.Text(self, width=10, height=1, font=FONT_M)
        self.sec_2_value_1_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_2_BASE_Y + PADDING_Y)

        # Begin
        self.sec_2_key_2_label = tk.Label(self, text="Begin:", font=FONT_M)
        self.sec_2_key_2_label.place(x=BASE_X, y=SECTION_2_BASE_Y + 2 * PADDING_Y)
        self.sec_2_value_2_box = tk.Text(self, width=10, height=1, font=FONT_M)
        self.sec_2_value_2_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_2_BASE_Y + 2 * PADDING_Y)

        # End
        self.sec_2_key_3_label = tk.Label(self, text="End:", font=FONT_M)
        self.sec_2_key_3_label.place(x=BASE_X, y=SECTION_2_BASE_Y + 3 * PADDING_Y)
        self.sec_2_value_3_box = tk.Text(self, width=10, height=1, font=FONT_M)
        self.sec_2_value_3_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_2_BASE_Y + 3 * PADDING_Y)
        
        treatments = self.metadata["treatments"]
        self.metadata_add_button = tk.Button(self, text="Add", font=FONT_M)
        self.metadata_edit_button = tk.Button(self, text="Edit", font=FONT_M)
        self.metadata_delete_button = tk.Button(self, text="Delete", font=FONT_M)
        self.metadata_save_button = tk.Button(self, text="Save", font=FONT_M)
        self.metadata_buttons = [self.metadata_add_button, self.metadata_edit_button, self.metadata_delete_button, self.metadata_save_button]

        for i, button in enumerate(self.metadata_buttons):
            button.place(x=BOTTOM_BUTTONS_X + i * BOTTOM_BUTTONS_PADDING_X, y=BOTTOM_BUTTONS_Y, width=90, height=30)       
        self.update_idletasks()
        self.display_treatments(treatments)

    def ratiometric_switch(self) -> None:
        current_state = self.sec_1_value_1_button["text"]

        if current_state == "1":
            self.sec_1_value_1_button.config(text="0")
        else:
            self.sec_1_value_1_button.config(text="1")

    def display_treatments(self, treatments: dict[str, dict[str, int]]) -> None:
        labels = []
        for name in treatments.keys():
            labels.append(tk.Label(self, text=name, font=FONT_S))
            for key in treatments[name].keys():
                labels.append(tk.Label(self, text=key, font=FONT_S))
        
        def x_gen():
            while True:
                yield 0
                yield 100
                yield 200

        x_vals = x_gen()
        y_increment = 0
        for i, label in enumerate(labels):
            if i % 3 == 0 and i != 0:
                y_increment += 1
            label.place(x=BASE_X + next(x_vals), y=BOTTOM_BUTTONS_Y + 40 + y_increment * PADDING_Y)

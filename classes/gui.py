import tkinter as tk
import toml
from tkinter import messagebox
from tkinter import filedialog
from threading import Thread
from pathlib import Path
from itertools import cycle
from functions.gui_utilities import int_entry, str_entry
from functions.validation import validate_config, validate_treatments
from functions.toml_handling import config_to_dict, dict_to_metadata, metadata_to_dict
from .analyzer import DataAnalyzer
from .converter import Converter
from .toml_data import Config, Metadata, Treatments

FONT_L = ("Arial", 18)
FONT_M = ("Arial", 16)
FONT_S = ("Arial", 12)

BASE_X = 20
BASE_Y = 20
PADDING_Y = 30
PADDING_X = 120
CONVERT_Y = 170
CONVERT_PADDING_X = 218
PANEL_Y = 210
SECTION_1_BASE_Y = 20 #180
SECTION_2_BASE_Y = 180 #340
EDITOR_PADDING_X = 200
OFFSCREEN_X = 500
BOTTOM_BUTTONS_Y = 220
BOTTOM_BUTTONS_X = 35
BOTTOM_BUTTONS_PADDING_X =100

# this defines different screen sizes, resizing is done by a callback funtion that triggers when the value of
# the StringVar storing the current mode changes.
DISPLAY_MODES: dict[str, str] = {
    "analysis": "460x230",
    "config": "460x540",
    "metadata": "460x760"
}

# this is used for selecting what message we want to display when the program is finished its work
MESSAGES: dict[tuple[int, int, int], str] = {
    (0, 0, 0): "Please select at least one action to perform.",
    (1, 0, 0): "Finished processing data.",
    (0, 1, 0): "Finished tabulating results.",
    (0, 0, 1): "Finished making graphs.",
    (1, 1, 0): "Finished processing data and tabulating results.",
    (1, 0, 1): "Finished processing data and making graphs.",
    (0, 1, 1): "Finished tabulating results and making graphs.",
    (1, 1, 1): "Finished processing data, tabulating results, and making graphs."
}

# this is used to create new metadata if the user selects a folder without a metadata.toml file
METADATA_TEMPLATE = {
    "conditions": {
        "ratiometric_dye": "true",
        "group1": "",
        "group2": ""
    },
    "treatments": {
        "baseline": {
            "begin": 0,
            "end": 60
        }
    }
}

class MainWindow:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.root = tk.Tk()
        self.root.title("Ca Measurement Analyzer")
        
        self.current_mode = tk.StringVar(value="config")
        self.current_mode.trace_add("write", self.resize_window)
        self.root.resizable(False, True)

        self.analyzer: DataAnalyzer

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
        self.check_g_state = tk.IntVar(value=0)
        self.check_g = tk.Checkbutton(self.root, text="Make graphs", font=FONT_M, variable=self.check_g_state)
        self.check_g.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y)

        # Repeat checkbox
        self.check_r_state = tk.IntVar()
        self.check_r = tk.Checkbutton(self.root, text="Repeat", font=FONT_M, variable=self.check_r_state)
        self.check_r.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y + PADDING_Y)
        
        # Progress tracker
        self.in_progress_label = tk.Label(self.root, text="Analysis in progress...", font=FONT_M)
        self.finished_file_counter = tk.IntVar()
        self.finished_file_counter.trace_add("write", self.update_counter)
        self.finished_files_label = tk.Label(self.root, text="Files finished:", font=FONT_M)
        self.finished_number_label = tk.Label(self.root, text="0", font=FONT_M)

        # Analyze button
        self.analyze_button = tk.Button(self.root, width=8, text="Analyze", font=FONT_L, command=self.analyze_button_press)
        self.analyze_button.place(x=BASE_X, y=3 * PADDING_Y, width=120, height=60)

        # Config button
        self.config_button = tk.Button(self.root, width=8, text="Edit\nconfig", font=FONT_M, command=self.config_button_press)
        self.config_button.place(x=BASE_X + 1.2 * PADDING_X, y=3 * PADDING_Y, width=120, height=60)

        # Metadata button
        self.metadata_button = tk.Button(self.root, width=8, text="Edit\nmetadata", font=FONT_M, command=self.metadata_button_press)
        self.metadata_button.place(x=BASE_X + 2.4 * PADDING_X, y=3 * PADDING_Y, width=120, height=60)

        # Convert to cache button
        self.convert_to_button = tk.Button(self.root, text="Convert files to cache", font=FONT_S, command=self.to_cache_button_press)
        self.convert_to_button.place(x=BASE_X, y=CONVERT_Y, width=190, height=40)

        # Convert back to Excel button
        self.convert_back_button = tk.Button(self.root, text="Convert back to Excel", font=FONT_S, command=self.to_excel_button_press)
        self.convert_back_button.place(x=BASE_X + CONVERT_PADDING_X, y=CONVERT_Y, width=190, height=40)

        self.root.update_idletasks()
        # Config editor panel
        self.config_panel = ConfigFrame(self.root, self.config, self.config_button.winfo_width(), width=460, height=320)

        # Metadata editor panel
        self.metadata_panel = MetadataFrame(self.root, self.metadata_button.winfo_width(), self.metadata_button.winfo_height(), width=460, height=640)
    
        self.root.update_idletasks()
        # this line is here and not at the beginning so that the window won't jump around:
        self.root.geometry(DISPLAY_MODES[self.current_mode.get()])
        self.config_button_press() # this is here so the program can start in the config layout
        self.root.protocol("WM_DELETE_WINDOW", exit)
        self.root.mainloop()
    
    def resize_window(self, *args) -> None:
        """Called whenever the current_mode StringVar is written to.
        """
        self.root.geometry(DISPLAY_MODES[self.current_mode.get()])

    def analyze_button_press(self) -> None:
        data_path = Path(self.target_path.get())
        if not data_path.exists():
            messagebox.showerror(message="Target folder not found.")
            return
        if not data_path.is_dir():
            messagebox.showerror(message="Target isn't a folder.")
            return

        method = self.config.input.method
        if method not in ["baseline", "previous", "derivative"]:
            # this is here and not where the check is actually relevant in order to avoid unnecessary IO and processing
            # operations if the user made a mistake and the program would crash anyway
            messagebox.showerror(message="Implemented reaction testing methods are:\n\"baseline\",\n\"previous\", "
            "\nand \"derivative\".\n\nSee README.md")
            return
        
        previous_mode = self.current_mode.get()
        self.current_mode.set("analysis")
        # this is so the analyzer object will have access to the target path for saving the tabulated summary
        # (this value is not the same as what the config started with if the user provided the TARGET command line arg)
        self.config.input.target_folder = data_path
        
        self.analyzer = DataAnalyzer(self.config, self.finished_file_counter, bool(self.check_r_state.get()))
        error_list = self.analyzer.create_subdir_instances()
        for error_message in error_list:
            messagebox.showerror(message=error_message)

        proc, tab, graph = self.check_p_state.get(), self.check_t_state.get(), self.check_g_state.get()
        worker_thread = Thread(target=self.analysis_work, args=(proc, tab, graph, previous_mode))
        worker_thread.start()

        self.analyze_button.place(x=OFFSCREEN_X)
        self.config_button.place(x=OFFSCREEN_X)
        self.metadata_button.place(x=OFFSCREEN_X)

        self.in_progress_label.place(x=BASE_X, y=3 * PADDING_Y)
        self.finished_files_label.place(x=BASE_X, y=4 * PADDING_Y)
        self.finished_number_label.place(x=BASE_X + 140, y=4 * PADDING_Y)


    def update_counter(self, *args) -> None:
        """Called whenever the value of the finished_file_counter IntVar is written to (by a SubDir instance, indicating
         it finished processing a file).
        """
        self.finished_number_label.config(text=str(self.finished_file_counter.get()))
        self.root.update_idletasks()

    def config_button_press(self) -> None:
        """
        Sets the mode (which determines window size) to config and changes the editor section's labels, textboxes,
        and buttons appropriately.
        """
        self.current_mode.set("config")
        self.config_panel.place(x=0, y=PANEL_Y)
        self.metadata_panel.place(x=OFFSCREEN_X)    

    def metadata_button_press(self) -> None:
        """
        Sets the mode (which determines window size) to metadata and changes the editor section's labels, textboxes,
        and buttons appropriately.
        """
        self.current_mode.set("metadata")
        self.metadata_panel.update_frame()
        self.config_panel.place(x=OFFSCREEN_X)
        self.metadata_panel.place(x=0, y=PANEL_Y)

    def analysis_work(self, proc, tab, graph, mode) -> None:
        """Encapsulates all the data processing work that needs to run in a separate thread. (So that we can update and
         display the progress indicator.)

        Args:
            proc (_type_): The value of the "Process" checkbox.
            tab (_type_): The value of the "Tabulate" checkbox.
            graph (_type_): The value of the "Make graphs" checkbox.
        """
        error_list = []
        if proc:
            self.analyzer.process_data(error_list)
            for error in error_list:
                messagebox.showerror(message=error) # if the list is empty, nothing will happen
        if tab:
            self.analyzer.tabulate_data()
        if graph:
            self.analyzer.graph_data()

        messagebox.showinfo(message=MESSAGES[(proc, tab, graph)])

        self.current_mode.set(mode)
        self.finished_file_counter.set(0)
        self.in_progress_label.place(x=OFFSCREEN_X)
        self.finished_files_label.place(x=OFFSCREEN_X)
        self.finished_number_label.place(x=OFFSCREEN_X)

        self.analyze_button.place(x=BASE_X, y=3 * PADDING_Y, width=120, height=60)
        self.config_button.place(x=BASE_X + 1.2 * PADDING_X, y=3 * PADDING_Y, width=120, height=60)
        self.metadata_button.place(x=BASE_X + 2.4 * PADDING_X, y=3 * PADDING_Y, width=120, height=60)
    
    def to_cache_button_press(self) -> None:
        previous_mode = self.current_mode.get()
        self.current_mode.set("analysis")
        self.root.update_idletasks()
        self.conversion("feather")
        self.current_mode.set(previous_mode)

    def to_excel_button_press(self) -> None:
        previous_mode = self.current_mode.get()
        self.current_mode.set("analysis")
        self.root.update_idletasks()
        self.conversion("excel")
        self.current_mode.set(previous_mode)

    def conversion(self, target: str) -> None:
        assert target in {"feather", "excel"} # should never fail
        path = self.config.input.target_folder
        report_name = self.config.output.report_name
        
        converters = []
        for folder in path.iterdir():
            if folder.is_dir():
                cache_path = folder / ".cache"
                report_path = folder / f"{report_name}{folder.name}.xlsx"
                converters.append(Converter(folder, cache_path, report_path))

        if target == "feather":
            threads = [Thread(target=conv.convert_to_feather) for conv in converters]
        else:
            threads = [Thread(target=conv.convert_to_excel) for conv in converters]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        messagebox.showinfo(message="Conversion finished!")


class ConfigFrame(tk.Frame):
    """Displayed in Config Editor mode. Will be moved offscreen when the program switches to a different mode.
    """
    def __init__(self, parent, config: Config, save_button_size: int, **kwargs):
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
        self.sec_1_value_1_button.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + PADDING_Y, width=103, height=30)

        # Method
        self.sec_1_key_2_label = tk.Label(self, text="Method:", font=FONT_M)
        self.sec_1_key_2_label.place(x=BASE_X, y=SECTION_1_BASE_Y + 2 * PADDING_Y)
        self.selected_method = tk.StringVar()
        self.selected_method.set(self.config.input.method)
        self.method_options: list[str] = ["baseline", "previous", "derivative"]
        self.sec_1_value_2_menu = tk.OptionMenu(self, self.selected_method, *self.method_options)
        self.sec_1_value_2_menu.place(x=BASE_X + EDITOR_PADDING_X - 1, y=SECTION_1_BASE_Y + 2 * PADDING_Y, width=105, height=30)

        # SD multiplier
        self.sec_1_key_3_label = tk.Label(self, text="SD multiplier:", font=FONT_M)
        self.sec_1_key_3_label.place(x=BASE_X, y=SECTION_1_BASE_Y + 3 * PADDING_Y)
        self.sec_1_value_3_entry = int_entry(self)
        self.sec_1_value_3_entry.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + 3 * PADDING_Y)
        self.sec_1_value_3_entry.delete(0, tk.END)
        self.sec_1_value_3_entry.insert(0, str(self.config.input.SD_multiplier))

        # Smoothing range
        self.sec_1_key_4_label = tk.Label(self, text="Smoothing range:", font=FONT_M)
        self.sec_1_key_4_label.place(x=BASE_X, y=SECTION_1_BASE_Y + 4 * PADDING_Y)
        self.sec_1_value_4_entry = int_entry(self)
        self.sec_1_value_4_entry.delete(0, tk.END)
        self.sec_1_value_4_entry.insert(0, str(self.config.input.smoothing_range))
        self.sec_1_value_4_entry.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + 4 * PADDING_Y)

        # Output section
        self.sec_2_label = tk.Label(self, text="Output section", font=FONT_L)
        self.sec_2_label.place(x=BASE_X, y=SECTION_2_BASE_Y)

        # Report name
        self.sec_2_key_1_label = tk.Label(self, text="Report name:", font=FONT_M)
        self.sec_2_key_1_label.place(x=BASE_X, y=SECTION_2_BASE_Y + PADDING_Y)
        self.sec_2_value_1_entry = str_entry(self)
        self.sec_2_value_1_entry.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_2_BASE_Y + PADDING_Y)
        self.sec_2_value_1_entry.delete(0, tk.END)
        self.sec_2_value_1_entry.insert(0, self.config.output.report_name)

        # Summary name
        self.sec_2_key_2_label = tk.Label(self, text="Summary name:", font=FONT_M)
        self.sec_2_key_2_label.place(x=BASE_X, y=SECTION_2_BASE_Y + 2 * PADDING_Y)
        self.sec_2_value_2_box = str_entry(self)
        self.sec_2_value_2_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_2_BASE_Y + 2 * PADDING_Y)
        self.sec_2_value_2_box.delete(0, tk.END)
        self.sec_2_value_2_box.insert(0, self.config.output.summary_name)
        
        # Save button for config file
        self.save_config_button = tk.Button(self, text="Save", font=FONT_L, command=self.save_config)
        self.save_config_button.place(x=BASE_X + 1.2 * PADDING_X, y=SECTION_2_BASE_Y + 10 + 3 * PADDING_Y, width=save_button_size, height=30)

    def select_folder(self) -> None:
        """Called when pressing the button to select the target folder.
        """
        path = filedialog.askdirectory(title="Select a folfer")
        if path:
            self.target_path.set(path)

    def save_config(self) -> None:
        """Called by the Save button to write the config file to disk.
        """
        self.config.input.target_folder = Path(self.target_path.get())
        self.config.input.method = self.selected_method.get()
        self.config.input.SD_multiplier = int(self.sec_1_value_3_entry.get())
        self.config.input.smoothing_range = int(self.sec_1_value_4_entry.get())
        self.config.output.report_name = self.sec_2_value_1_entry.get()
        self.config.output.summary_name = self.sec_2_value_2_box.get()

        config_as_dict = config_to_dict(self.config)
        errors = validate_config(config_as_dict)
        if errors:
            messagebox.showerror(errors)
            return

        with open(Path("./config.toml"), "w") as f:
            toml.dump(config_as_dict, f)


class MetadataFrame(tk.Frame):
    """Displayed in Metadata Editor mode. Will be moved offscreen when the program switches to a different mode.
    """
    def __init__(self, parent, button_width: int, button_height: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.browse_button_width = button_width
        self.browse_button_height = button_height
        self.selected_folder = tk.StringVar()
        self.metadata: Metadata

    def update_frame(self):
        """
        Updates this Frame with the correct metadata information. The reason these things are here and not in __init__
        is that this is how we can update the displayed information after the object is instantiated with dummy values.
        """
        # Folder selector button
        self.metabata_browse_button = tk.Button(self, text="Select\nfolder", font=FONT_M, command=self.select_measurement_folder_and_load_metadata)
        self.metabata_browse_button.place(x=BASE_X + 2.4 * PADDING_X, y=BASE_Y, width=self.browse_button_width, height=self.browse_button_height)
        if not self.selected_folder.get():
            self.select_measurement_folder_and_load_metadata()
        
        # Conditions section
        self.sec_1_label = tk.Label(self, text="Conditions section", font=FONT_L)
        self.sec_1_label.place(x=BASE_X, y=SECTION_1_BASE_Y)

        # Ratiometric dye
        self.sec_1_key_1_label = tk.Label(self, text="Ratiometric dye:", font=FONT_M)
        self.sec_1_key_1_label.place(x=BASE_X, y=SECTION_1_BASE_Y + PADDING_Y)
        self.sec_1_value_1_button = tk.Button(self, text=f"{self.metadata.conditions.ratiometric_dye}", font=FONT_M, command=self.ratiometric_switch)
        self.sec_1_value_1_button.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + PADDING_Y)

        # Group1
        self.sec_1_key_2_label = tk.Label(self, text="Group 1:", font=FONT_M)
        self.sec_1_key_2_label.place(x=BASE_X, y=SECTION_1_BASE_Y + 2 * PADDING_Y)
        self.sec_1_value_2_box = str_entry(self)
        self.sec_1_value_2_box.delete(0, tk.END)
        self.sec_1_value_2_box.insert(0, self.metadata.conditions.group1)
        self.sec_1_value_2_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + 10 + 2 * PADDING_Y)

        # Group2
        self.sec_1_key_3_label = tk.Label(self, text="Group 2:", font=FONT_M)
        self.sec_1_key_3_label.place(x=BASE_X, y=SECTION_1_BASE_Y + 3 * PADDING_Y)
        self.sec_1_value_3_box = str_entry(self)
        self.sec_1_value_3_box.place(x=BASE_X + EDITOR_PADDING_X, y=SECTION_1_BASE_Y + 10 + 3 * PADDING_Y)
        self.sec_1_value_3_box.delete(0, tk.END)
        self.sec_1_value_3_box.insert(0, self.metadata.conditions.group2)

        # Treatment section
        self.sec_2_label = tk.Label(self, text="Treatment section", font=FONT_L)
        self.sec_2_label.place(x=BASE_X, y=SECTION_2_BASE_Y)

        treatments = self.metadata.treatments  
        self.update_idletasks()
        self.treatment_table = TreatmentTable(self, treatments, width=440, height=490)
        self.treatment_table.place(x=BASE_X + 40, y=BOTTOM_BUTTONS_Y)
        
        self.save_metadata_button = tk.Button(self, text="Save Metadata", font=FONT_M, command=self.save_metadata)
        self.save_metadata_button.place(x=230, y=SECTION_2_BASE_Y + 40)

    def ratiometric_switch(self) -> None:
        """Toggles what to display on the button for the ratiometric dye value.
        """
        current_state = self.sec_1_value_1_button["text"]

        if current_state == "True":
            self.sec_1_value_1_button.config(text="False")
        else:
            self.sec_1_value_1_button.config(text="True")

    def select_measurement_folder_and_load_metadata(self) -> None:
        """Called when the user first selects the Metadata Editor mode, and by its Select Folder button afterwards. If
        no metadata file is found, sets the metadata template as the metadata.
        """
        path = filedialog.askdirectory(title="Select measurement folder")
        if path:
            self.selected_folder.set(path)

            try:
                with open(Path(self.selected_folder.get()) / "metadata.toml", "r") as f:
                    metadata = toml.load(f)
                    self.metadata = dict_to_metadata(metadata)
            except FileNotFoundError:
                self.metadata = dict_to_metadata(METADATA_TEMPLATE)

    def save_metadata(self) -> None:
        """Called by the Save Metadata button. Updates the metadata object with values entered by the user, then
        validates that these values are correct, displaying an error message if any mistakes are found. If not mistakes
        are found, it saves the metadata as metadata.toml in the selected folder.
        """
        self.metadata.conditions.ratiometric_dye = self.sec_1_value_1_button["text"]
        self.metadata.conditions.group1 = self.sec_1_value_2_box.get()
        self.metadata.conditions.group2 = self.sec_1_value_3_box.get()
        self.treatment_table.save_values()
        self.metadata.treatments = self.treatment_table.treatments

        try:
            self.metadata.treatments.remove_empty_values()
        except ValueError:
            messagebox.showerror(message="Please make sure all intended begin and end fields are filled.")
            return

        passed_tests: list[bool] = validate_treatments(self.metadata.treatments)
        error_message = "Please make sure that:"
        if all(passed_tests):
            for agonist in self.metadata.treatments:
                self.metadata.treatments[agonist].begin = int(self.metadata.treatments[agonist].begin)
                self.metadata.treatments[agonist].end = int(self.metadata.treatments[agonist].end)
            with open(Path(self.selected_folder.get()) / "metadata.toml", "w") as metadata:
                metadata_as_dict = metadata_to_dict(self.metadata)
                toml.dump(metadata_as_dict, metadata)
                messagebox.showinfo(message="Metadata saved!")
                return # so that the error message is not displayed when there is no error
        if not passed_tests[0]:
            error_message += "\nAll begin and end values are integers."
        if not passed_tests[1]:
            error_message += "\nAll agonists have smaller begin values than end values."
        if not passed_tests[2]:
            error_message += "\nAll begin values are greater than or equal to the previous row's end value."
                
        messagebox.showerror(message=error_message)


class TreatmentTable(tk.Frame):
    """Encapsulates the logic and methods required to display the treatments section correctly.
    """
    LABEL_ROW_Y = 40
    COL_1_X = 0
    COL_2_X = 120
    COL_3_X = 240
    def __init__(self, parent, treatments: Treatments, **kwargs):
        super().__init__(parent, **kwargs)
        self.treatments = treatments
        self.add_row_button = tk.Button(self, text="Add row", font=FONT_M, command=self.add_row)
        self.add_row_button.place(x=0, y=0)
        self.name_label = tk.Label(self, text="Agonist", font=FONT_M)
        self.name_label.place(x=self.COL_1_X, y=self.LABEL_ROW_Y)
        self.begin_label = tk.Label(self, text="Beginning", font=FONT_M)
        self.begin_label.place(x=self.COL_2_X, y=self.LABEL_ROW_Y)
        self.end_label = tk.Label(self, text="End", font=FONT_M)
        self.end_label.place(x=self.COL_3_X, y=self.LABEL_ROW_Y)
        self.rows: list[list[tk.Entry]] = []
        
        for _ in range(max(len(self.treatments), 5)):
            # we want at least 5 rows
            self.rows.append([str_entry(self), int_entry(self), int_entry(self)])

        self.fill_values()
        self.update_display()

    def add_row(self) -> None:
        """Called by the Add row button.
        """
        self.rows.append([str_entry(self), int_entry(self), int_entry(self)])
        self.update_display()

    def update_display(self) -> None:
        """Updates the screen so that the correct number of entry boxes are displayed. There's no logic for removing
        excess boxes, which is why there is no Remove row button. Empty rows are instead handled later when we save the
        metadata file in MetadataFrame.save_metadata().
        """
        x_pos = cycle([self.COL_1_X, self.COL_2_X, self.COL_3_X])
        y_pos = 70
        for row in self.rows:
            for entry in row:
                entry.place(x=next(x_pos), y=y_pos)
            y_pos += 30

    def save_values(self) -> None:
        """Updates the treatments dictionary with values entered by the user.
        """
        treatments = Treatments()
        for row in self.rows:
            treatments[row[0].get()] = (row[1].get(), row[2].get())

        self.treatments = treatments


    def fill_values(self) -> None:
        """Loads values found in the selected folder's metadata file into the entry fields.
        """
        for i, name in enumerate(self.treatments):
            self.rows[i][0].delete(0, tk.END)
            self.rows[i][0].insert(0, name)
            for j, value in enumerate(self.treatments[name].values, start=1):
                self.rows[i][j].delete(0, tk.END)
                self.rows[i][j].insert(0, str(value))

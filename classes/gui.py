import toml
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

from itertools import cycle
from pathlib import Path
from threading import Thread

from .engine import AnalysisEngine
from .converter import Converter
from .toml_data import Config, Metadata, Treatments

from functions.gui_utilities import int_entry, str_entry
from functions.validation import validate_config, validate_treatments

FONT_L = ("Arial", 18)
FONT_M = ("Arial", 16)
FONT_S = ("Arial", 12)

BASE_X = 20
BASE_Y = 20
PADDING_Y = 30
PADDING_X = 120
MAIN_BUTTON_Y = 90 # used for placing the frame containing the main 6 buttons and alternatively the progress tracker
PANEL_Y = 220 # used for placing the config and metadata editor panels
CONF_SECTION_1_BASE_Y = 20 # first section of the config editor panel
CONF_SECTION_2_BASE_Y = 180 # second section of the config editor panel
META_SECTION_1_BASE_Y = 70 # first section of the metadata editor panel
META_SECTION_2_BASE_Y = 200 # second second of the metadata editor panel
EDITOR_PADDING_X = 200 # BASE_X + this is the x coord for items in the second column of the editor panels
OFFSCREEN_X = 500 # this is used to move unwanted items offscreen
BOTTOM_TABLE_Y = 240 # y coord for the treatment table on the metadata panel

# this defines different screen sizes, resizing is done by a callback function that triggers when the value of
# the StringVar storing the current mode changes.
DISPLAY_MODES: dict[str, str] = {
    "analysis": "460x180",
    "config": "460x550",
    "metadata": "460x800"
}

# this is used for selecting what message we want to display when the program has finished its work
# 1st number: processing y/n, 2nd: summary y/n, 3rd: graphing y/n
MESSAGES: dict[tuple[int, int, int], str] = {
    (0, 0, 0): "Please select at least one action to perform.",
    (1, 0, 0): "Finished processing data.",
    (0, 1, 0): "Finished summarizing results.",
    (0, 0, 1): "Finished making graphs.",
    (1, 1, 0): "Finished processing data and summarizing results.",
    (1, 0, 1): "Finished processing data and making graphs.",
    (0, 1, 1): "Finished summarizing results and making graphs.",
    (1, 1, 1): "Finished processing data, summarizing results, and making graphs."
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

        self.analyzer: AnalysisEngine # to be instantiated later
        self.converter = Converter(self.config.input.target_folder, self.config.output.report_name)
        
        self.checkbox_frame = tk.Frame()
        self.checkbox_frame.place(x=0, y=0, width=460, height=90)

        # Processing checkbox
        self.check_p_state = tk.IntVar()
        self.check_p = tk.Checkbutton(self.checkbox_frame, text="Process", font=FONT_M, variable=self.check_p_state)
        self.check_p.place(x=BASE_X, y=BASE_Y)

        # Summary checkbox
        self.check_t_state = tk.IntVar()
        self.check_t = tk.Checkbutton(self.checkbox_frame, text="Summarize", font=FONT_M, variable=self.check_t_state)
        self.check_t.place(x=BASE_X, y=BASE_Y + PADDING_Y)

        # Graphing checkbox
        self.check_g_state = tk.IntVar(value=0)
        self.check_g = tk.Checkbutton(self.checkbox_frame, text="Make graphs", font=FONT_M, variable=self.check_g_state)
        self.check_g.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y)

        # Repeat checkbox
        self.check_r_state = tk.IntVar()
        self.check_r = tk.Checkbutton(self.checkbox_frame, text="Repeat", font=FONT_M, variable=self.check_r_state)
        self.check_r.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y + PADDING_Y)

        # Progress tracker
        self.tracker_frame = tk.Frame()

        self.in_progress_label = tk.Label(self.tracker_frame, text="Work in progress...", font=FONT_M)
        self.in_progress_label.place(x=BASE_X, y=0)

        self.finished_file_counter = tk.IntVar()
        self.finished_file_counter.trace_add("write", self.update_counter)

        self.finished_files_label = tk.Label(self.tracker_frame, text="Files finished:", font=FONT_M)
        self.finished_files_label.place(x=BASE_X, y=PADDING_Y)

        self.finished_number_label = tk.Label(self.tracker_frame, text="0", font=FONT_M)
        self.finished_number_label.place(x=BASE_X + 140, y=PADDING_Y)

        # Frame for the buttons
        self.button_frame = tk.Frame()
        self.button_frame.place(x=BASE_X, y=MAIN_BUTTON_Y)
        BW = 9 # button width in screen units
        BH = 2 # button height in screen units

        # template for the 6 main buttons
        def main_button(**kwargs): return tk.Button(self.button_frame, width=BW, height=BH, font=FONT_M, **kwargs)

        ## Analyze button
        self.analyze_button = main_button(text="Analyze", command=self.analyze_button_press)
        self.analyze_button.grid(row=0, column=0, sticky="news")

        ## Config button
        self.config_button = main_button(text="Edit\nconfig", command=self.config_button_press)
        self.config_button.grid(row=0, column=1, sticky="news")

        ## Metadata button
        self.metadata_button = main_button(text="Edit\nmetadata", command=self.metadata_button_press)
        self.metadata_button.grid(row=0, column=2, sticky="news")

        ## Convert to cache button
        self.convert_to_button = main_button(text="Convert\nto cache", command=self.to_cache_button_press)
        self.convert_to_button.grid(row=1, column=0, sticky="news")

        ## Convert back to Excel button
        self.convert_back_button = main_button(text="Convert\nto Excel", command=self.to_excel_button_press)
        self.convert_back_button.grid(row=1, column=1, sticky="news")

        ## Delete cache button
        self.delete_cache_button = main_button(text="Empty\ncache", command=self.delete_cache_button_press)
        self.delete_cache_button.grid(row=1, column=2, sticky="news")

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
        """Called when the analyze button is pressed, it checks if the input values are correct then calls the
        analysis_work method in a new thread, which is responsible for creating and using the AnalysisEngine object,
        calling the engine's relevant methods as dictated by the checkboxes in the GUI. The new thread is needed to keep
        the GUI responsive, prevent a deadlock, and so that the progress tracker can be updated.
        """
        data_path = self.config.input.target_folder
        if not data_path.exists():
            messagebox.showerror(message="Target folder not found.")
            return
        if not data_path.is_dir():
            messagebox.showerror(message="Target isn't a folder.")
            return # these errors should not happen in the GUI version but I will leave this here just in case

        method = self.config.input.method
        if method not in ["baseline", "previous", "derivative"]:
            # this is here and not where the check is actually relevant in order to avoid unnecessary IO and processing
            # operations if the user made a mistake and the program would crash anyway
            messagebox.showerror(message="Implemented reaction testing methods are:\n\"baseline\",\n\"previous\", "
            "\nand \"derivative\".\n\nSee README.md")
            return
        
        previous_mode = self.current_mode.get()
        self.current_mode.set("analysis")
        self.button_frame.place(x=OFFSCREEN_X)
        self.tracker_frame.place(x=0, y=MAIN_BUTTON_Y, width=460, height=90)

        worker_thread = Thread(target=self.analysis_work, args=(previous_mode,))
        worker_thread.start()
        # the processing work is put in a new thread so that the progress counter can be updated and displayed

    def update_counter(self, *args) -> None:
        """Called whenever the value of the finished_file_counter IntVar is written to (by a SubDir instance, indicating
         it finished processing a file).
        """
        self.finished_number_label.config(text=str(self.finished_file_counter.get()))

    def config_button_press(self) -> None:
        """
        Sets the mode (which determines window size) to config and changes the editor section's labels, entry fields,
        and buttons appropriately.
        """
        self.current_mode.set("config")
        self.config_panel.place(x=0, y=PANEL_Y)
        self.metadata_panel.place(x=OFFSCREEN_X)    

    def metadata_button_press(self) -> None:
        """
        Sets the mode (which determines window size) to metadata and changes the editor section's labels, entry fields,
        and buttons appropriately.
        """
        self.current_mode.set("metadata")
        self.metadata_panel.update_frame()
        self.config_panel.place(x=OFFSCREEN_X)
        self.metadata_panel.place(x=0, y=PANEL_Y)

    def analysis_work(self, mode: str) -> None:
        """Encapsulates all the data processing work that needs to run in a separate thread. (So that we can update and
         display the progress indicator.)
        """
        self.in_progress_label.config(text="Converting files...")
        self.analyzer = AnalysisEngine(self.config, self.finished_file_counter, bool(self.check_r_state.get()))
        self.analyzer.create_caches()

        error_list = self.analyzer.create_processor_instances()
        for error_message in error_list: # if there was no error, nothing happens
            messagebox.showerror(message=error_message)
        
        proc, tab, graph = self.check_p_state.get(), self.check_t_state.get(), self.check_g_state.get()

        error_list = []
        if proc:
            self.in_progress_label.config(text="Analyzing...")
            self.analyzer.process_data(error_list)
            for error in error_list:
                messagebox.showerror(message=error) # if the list is empty, nothing will happen
        if tab:
            self.in_progress_label.config(text="Working on summary...")
            self.analyzer.summarize_results()
        if graph:
            self.in_progress_label.config(text="Drawing graphs...")
            self.analyzer.graph_data()

        messagebox.showinfo(message=MESSAGES[(proc, tab, graph)])

        self.current_mode.set(mode)
        self.tracker_frame.place(x=OFFSCREEN_X)
        self.button_frame.place(x=BASE_X, y=MAIN_BUTTON_Y)
    
    def to_cache_button_press(self) -> None:
        """Changes the window size to indicate work is in progress then calls the conversion method to convert all
        measurement files from Excel to the cached format.
        """
        worker_thread = Thread(target=self.conversion, args=("feather",))
        worker_thread.start() # conversion is in a new thread so we can update and display the progress tracker

    def to_excel_button_press(self) -> None:
        """Changes the window size to indicate work is in progress then calls the conversion method to convert all
       cached files from the cached format back to Excel.
        """
        worker_thread = Thread(target=self.conversion, args=("excel",))
        worker_thread.start() # conversion is in a new thread so we can update and display the progress tracker

    def conversion(self, target: str) -> None:
        """Performs the actual conversion work between Excel files and the cached .feather format.

        Args:
            target (str): "feather" or "excel", indicates the direction of conversion
        """
        assert target in {"feather", "excel"} # should never fail
        previous_mode = self.current_mode.get()
        self.current_mode.set("analysis")
        self.button_frame.place(x=OFFSCREEN_X)
        self.tracker_frame.place(x=0, y=MAIN_BUTTON_Y, width=460, height=230)

        if target == "feather":
            self.converter.convert_to_feather(self.finished_file_counter)
        else:
            self.converter.convert_to_excel(self.finished_file_counter)

        messagebox.showinfo(message="Conversion finished!")

        self.current_mode.set(previous_mode)
        self.button_frame.place(x=BASE_X, y=MAIN_BUTTON_Y)
        self.tracker_frame.place(x=OFFSCREEN_X)
        self.finished_file_counter.set(0)
    
    def delete_cache_button_press(self) -> None:
        self.converter.purge_cache()
        messagebox.showinfo(message="All cached files removed!")


class ConfigFrame(tk.Frame):
    """Displayed in Config Editor mode. Will be moved offscreen when the program switches to a different mode.
    """
    def __init__(self, parent, config: Config, save_button_size: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.config = config

        # Input section
        self.input_label = tk.Label(self, text="Input section", font=FONT_L)
        self.input_label.place(x=BASE_X, y=CONF_SECTION_1_BASE_Y)

        ## Target folder selection
        self.target_folder_label = tk.Label(self, text="Target folder:", font=FONT_M)
        self.target_folder_label.place(x=BASE_X, y=CONF_SECTION_1_BASE_Y + PADDING_Y)
        self.target_folder_button = tk.Button(self, text="Browse...",font=FONT_M, command=self.select_folder)
        self.target_folder_button.place(x=BASE_X + EDITOR_PADDING_X, y=CONF_SECTION_1_BASE_Y + PADDING_Y, width=103, height=30)

        ## Method
        self.method_label = tk.Label(self, text="Method:", font=FONT_M)
        self.method_label.place(x=BASE_X, y=CONF_SECTION_1_BASE_Y + 2 * PADDING_Y)
        self.selected_method = tk.StringVar()
        self.selected_method.set(self.config.input.method)
        self.method_options: list[str] = ["baseline", "previous", "derivative"]
        self.method_menu = tk.OptionMenu(self, self.selected_method, *self.method_options)
        self.method_menu.place(x=BASE_X + EDITOR_PADDING_X - 1, y=CONF_SECTION_1_BASE_Y + 2 * PADDING_Y, width=105, height=30)

        ## SD multiplier
        self.SD_multiplier_label = tk.Label(self, text="SD multiplier:", font=FONT_M)
        self.SD_multiplier_label.place(x=BASE_X, y=CONF_SECTION_1_BASE_Y + 3 * PADDING_Y)
        self.SD_multiplier_entry = int_entry(self)
        self.SD_multiplier_entry.place(x=BASE_X + EDITOR_PADDING_X, y=CONF_SECTION_1_BASE_Y + 3 * PADDING_Y)
        self.SD_multiplier_entry.delete(0, tk.END)
        self.SD_multiplier_entry.insert(0, str(self.config.input.SD_multiplier))

        ## Smoothing range
        self.smoothing_label = tk.Label(self, text="Smoothing range:", font=FONT_M)
        self.smoothing_label.place(x=BASE_X, y=CONF_SECTION_1_BASE_Y + 4 * PADDING_Y)
        self.smoothing_entry = int_entry(self)
        self.smoothing_entry.delete(0, tk.END)
        self.smoothing_entry.insert(0, str(self.config.input.smoothing_range))
        self.smoothing_entry.place(x=BASE_X + EDITOR_PADDING_X, y=CONF_SECTION_1_BASE_Y + 4 * PADDING_Y)

        # Output section
        self.output_label = tk.Label(self, text="Output section", font=FONT_L)
        self.output_label.place(x=BASE_X, y=CONF_SECTION_2_BASE_Y)

        ## Report name
        self.report_label = tk.Label(self, text="Report name:", font=FONT_M)
        self.report_label.place(x=BASE_X, y=CONF_SECTION_2_BASE_Y + PADDING_Y)
        self.report_entry = str_entry(self)
        self.report_entry.place(x=BASE_X + EDITOR_PADDING_X, y=CONF_SECTION_2_BASE_Y + PADDING_Y)
        self.report_entry.delete(0, tk.END)
        self.report_entry.insert(0, self.config.output.report_name)

        ## Summary name
        self.summary_label = tk.Label(self, text="Summary name:", font=FONT_M)
        self.summary_label.place(x=BASE_X, y=CONF_SECTION_2_BASE_Y + 2 * PADDING_Y)
        self.summary_entry = str_entry(self)
        self.summary_entry.place(x=BASE_X + EDITOR_PADDING_X, y=CONF_SECTION_2_BASE_Y + 2 * PADDING_Y)
        self.summary_entry.delete(0, tk.END)
        self.summary_entry.insert(0, self.config.output.summary_name)
        
        # Save button for config file
        self.save_config_button = tk.Button(self, text="Save", font=FONT_L, command=self.save_config)
        self.save_config_button.place(x=BASE_X + 1.2 * PADDING_X, y=CONF_SECTION_2_BASE_Y + 10 + 3 * PADDING_Y, width=save_button_size, height=30)

    def select_folder(self) -> None:
        """Called when pressing the button to select the target folder.
        """
        path = filedialog.askdirectory(title="Select a folfer")
        if path:
            self.config.input.target_folder = Path(path)

    def save_config(self) -> None:
        """Called by the Save button to write the config file to disk.
        """
        # self.config.input.target_folder already had its value set by select_folder, or it wasn't changed
        self.config.input.method = self.selected_method.get()
        self.config.input.SD_multiplier = int(self.SD_multiplier_entry.get())
        self.config.input.smoothing_range = int(self.smoothing_entry.get())
        self.config.output.report_name = self.report_entry.get()
        self.config.output.summary_name = self.summary_entry.get()

        config_as_dict = self.config.to_dict()
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
        self.metabata_browse_button = tk.Button(self, text="Select folder", font=FONT_M, command=self.select_measurement_folder_and_load_metadata)
        self.metabata_browse_button.place(x=BASE_X, y=10, width=3*self.browse_button_width, height=self.browse_button_height/1.5)
        if not self.selected_folder.get():
            self.select_measurement_folder_and_load_metadata()
        
        # Conditions section
        self.conditions_label = tk.Label(self, text="Conditions section", font=FONT_L)
        self.conditions_label.place(x=BASE_X, y=META_SECTION_1_BASE_Y - 10)

        # Ratiometric dye
        self.dye_label = tk.Label(self, text="Ratiometric dye:", font=FONT_M)
        self.dye_label.place(x=BASE_X, y=META_SECTION_1_BASE_Y + PADDING_Y)
        self.dye_button = tk.Button(self, text=f"{self.metadata.conditions.ratiometric_dye.capitalize()}", font=FONT_M, command=self.ratiometric_switch)
        self.dye_button.place(x=BASE_X + EDITOR_PADDING_X, y=META_SECTION_1_BASE_Y + PADDING_Y, width=102, height=35)

        # Group1
        self.group1_label = tk.Label(self, text="Group 1:", font=FONT_M)
        self.group1_label.place(x=BASE_X, y=META_SECTION_1_BASE_Y + 2 * PADDING_Y)
        self.group1_entry = str_entry(self)
        self.group1_entry.delete(0, tk.END)
        self.group1_entry.insert(0, self.metadata.conditions.group1)
        self.group1_entry.place(x=BASE_X + EDITOR_PADDING_X, y=META_SECTION_1_BASE_Y + 10 + 2 * PADDING_Y)

        # Group2
        self.group2_label = tk.Label(self, text="Group 2:", font=FONT_M)
        self.group2_label.place(x=BASE_X, y=META_SECTION_1_BASE_Y + 3 * PADDING_Y)
        self.group2_entry = str_entry(self)
        self.group2_entry.place(x=BASE_X + EDITOR_PADDING_X, y=META_SECTION_1_BASE_Y + 10 + 3 * PADDING_Y)
        self.group2_entry.delete(0, tk.END)
        self.group2_entry.insert(0, self.metadata.conditions.group2)

        # Treatment section
        self.treatment_label = tk.Label(self, text="Treatment section", font=FONT_L)
        self.treatment_label.place(x=BASE_X, y=META_SECTION_2_BASE_Y)

        self.update_idletasks()
        self.treatment_table = TreatmentTable(self, self.metadata.treatments, width=440, height=490)
        self.treatment_table.place(x=BASE_X + 40, y=BOTTOM_TABLE_Y)
        
        self.save_metadata_button = tk.Button(self, text="Save Metadata", font=FONT_M, command=self.save_metadata)
        self.save_metadata_button.place(x=230, y=META_SECTION_2_BASE_Y + 40)

    def ratiometric_switch(self) -> None:
        """Toggles what to display on the button for the ratiometric dye value.
        """
        current_state = self.dye_button["text"]

        if current_state == "True":
            self.dye_button.config(text="False")
        else:
            self.dye_button.config(text="True")

    def select_measurement_folder_and_load_metadata(self) -> None:
        """Called when the user first selects the Metadata Editor mode, and by its Select Folder button afterwards. If
        no metadata file is found, creates new metadata from the template.
        """
        path = filedialog.askdirectory(title="Select measurement folder")
        if path:
            self.selected_folder.set(path)

            try:
                with open(Path(self.selected_folder.get()) / "metadata.toml", "r") as f:
                    metadata = toml.load(f)
                    self.metadata = Metadata(metadata)
            except FileNotFoundError:
                self.metadata = Metadata(METADATA_TEMPLATE) # there isn't a metadata file, we'll be making a new one

    def save_metadata(self) -> None:
        """Called by the Save Metadata button. Updates the metadata object with values entered by the user, then
        validates that these values are correct, displaying an error message if any mistakes are found. If not mistakes
        are found, it saves the metadata as metadata.toml in the selected folder.
        """
        self.metadata.conditions.ratiometric_dye = self.dye_button["text"]
        self.metadata.conditions.group1 = self.group1_entry.get()
        self.metadata.conditions.group2 = self.group2_entry.get()
        self.treatment_table.save_values()
        self.metadata.treatments = self.treatment_table.treatments

        try:
            self.metadata.treatments.remove_empty_values()
        except ValueError:
            messagebox.showerror(message="Please make sure all intended begin and end fields are filled.")
            return # this error partially overlaps with what validate_treatments check for, but I think it is different
                   # enough to deserve to be handled separately

        passed_tests: list[bool] = validate_treatments(self.metadata.treatments)
        error_message = "Please make sure that:"
        if all(passed_tests):
            for agonist in self.metadata.treatments:
                self.metadata.treatments[agonist].begin = int(self.metadata.treatments[agonist].begin)
                self.metadata.treatments[agonist].end = int(self.metadata.treatments[agonist].end)
            with open(Path(self.selected_folder.get()) / "metadata.toml", "w") as metadata:
                metadata_as_dict = self.metadata.to_dict()
                toml.dump(metadata_as_dict, metadata)
                messagebox.showinfo(message="Metadata saved!")

        else:
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
            # treatments[name] = (begin, end)

        self.treatments = treatments


    def fill_values(self) -> None:
        """Loads values found in the selected folder's metadata file into the entry fields.
        """
        for i, name in enumerate(self.treatments):
            self.rows[i][0].delete(0, tk.END)
            self.rows[i][0].insert(0, name) # name entry in the ith row
            for j, value in enumerate(self.treatments[name].values, start=1):
                self.rows[i][j].delete(0, tk.END)
                self.rows[i][j].insert(0, str(value)) # begin (j=1) and end (j=2) entries in the ith row

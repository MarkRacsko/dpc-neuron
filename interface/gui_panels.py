from itertools import cycle
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import toml

from interface.gui_constants import FONT_M, FONT_L
from interface.gui_constants import BASE_X, PADDING_X, PADDING_Y, EDITOR_PADDING_X
from interface.gui_constants import CONF_SECTION_1_BASE_Y, CONF_SECTION_2_BASE_Y
from interface.gui_constants import META_SECTION_1_BASE_Y, META_SECTION_2_BASE_Y, BOTTOM_TABLE_Y
from interface.gui_constants import METADATA_TEMPLATE

from interface.gui_utilities import int_entry, str_entry
from processing.classes.toml_data import Config, Metadata, Treatments
from processing.functions.validation import validate_config, validate_treatments


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

        ## Photobleaching correction
        self.correction_label = tk.Label(self, text="Photobleach corr.:", font=FONT_M)
        self.correction_label.place(x=BASE_X, y=CONF_SECTION_1_BASE_Y + 5 * PADDING_Y)
        self.correction_button = tk.Button(self, text=f"{self.config.input.correction.capitalize()}", font=FONT_M, command=self.correction_switch)
        self.correction_button.place(x=BASE_X + EDITOR_PADDING_X, y=CONF_SECTION_1_BASE_Y + 5 * PADDING_Y, width=103, height=30)

        ## Potassium response amplitude threshold
        self.amp_threshold_label = tk.Label(self, text="KCl amp. threshold:", font=FONT_M)
        self.amp_threshold_label.place(x=BASE_X, y=CONF_SECTION_1_BASE_Y + 6 * PADDING_Y)
        self.amp_threshold_entry = int_entry(self)
        self.amp_threshold_entry.delete(0, tk.END)
        self.amp_threshold_entry.insert(0, str(self.config.input.amp_threshold))
        self.amp_threshold_entry.place(x=BASE_X + EDITOR_PADDING_X, y=CONF_SECTION_1_BASE_Y + 6 * PADDING_Y)

        ## Potassium response CV threshold
        self.cv_threshold_label = tk.Label(self, text="KCl CV threshold:", font=FONT_M)
        self.cv_threshold_label.place(x=BASE_X, y=CONF_SECTION_1_BASE_Y + 7 * PADDING_Y)
        self.cv_threshold_entry = int_entry(self)
        self.cv_threshold_entry.delete(0, tk.END)
        self.cv_threshold_entry.insert(0, str(self.config.input.cv_threshold))
        self.cv_threshold_entry.place(x=BASE_X + EDITOR_PADDING_X, y=CONF_SECTION_1_BASE_Y + 7 * PADDING_Y)

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

    def correction_switch(self) -> None:
        """Toggles what to display on the button for the ratiometric dye value.
        """
        current_state = self.correction_button["text"]

        if current_state == "True":
            self.correction_button.config(text="False")
        else:
            self.correction_button.config(text="True")        

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
        self.config.input.amp_threshold = int(self.amp_threshold_entry.get())
        self.config.input.cv_threshold = int(self.cv_threshold_entry.get())
        self.config.input.correction = self.correction_button["text"]
        self.config.output.report_name = self.report_entry.get()
        self.config.output.summary_name = self.summary_entry.get()

        config_as_dict = self.config.to_dict()
        errors = validate_config(config_as_dict)
        if errors:
            messagebox.showerror(errors)
            return

        with open(Path("./config.toml"), "w") as f:
            toml.dump(config_as_dict, f)

        messagebox.showinfo(message="Configuration saved!")


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
        # Folder selector button 3*self.browse_button_width + 40
        self.button_frame = tk.Frame(master=self)
        self.button_frame.place(x=BASE_X + 70, y=10)

        def panel_button(**kwargs): return tk.Button(self.button_frame, width=9, height=1, font=FONT_M, **kwargs)

        self.metabata_browse_button = panel_button(text="Select folder", command=self.select_measurement_folder_and_load_metadata)
        self.metabata_browse_button.grid(row=0, column=0, sticky="news")

        self.metadata_clear_button = panel_button(text="Clear data", command=self.clear_button_press)
        self.metadata_clear_button.grid(row=0, column=1, sticky="news")

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

        # Framerate
        self.framerate_label = tk.Label(self, text="Frames/min", font=FONT_M)
        self.framerate_label.place(x=BASE_X, y=META_SECTION_1_BASE_Y + 2 * PADDING_Y)
        self.framerate_entry = int_entry(self)
        self.framerate_entry.delete(0, tk.END)
        self.framerate_entry.insert(0, str(self.metadata.conditions.framerate))
        self.framerate_entry.place(x=BASE_X + EDITOR_PADDING_X, y=META_SECTION_1_BASE_Y + 10 + 2 * PADDING_Y)

        # Group1
        self.group1_label = tk.Label(self, text="Group 1:", font=FONT_M)
        self.group1_label.place(x=BASE_X, y=META_SECTION_1_BASE_Y + 3 * PADDING_Y)
        self.group1_entry = str_entry(self)
        self.group1_entry.delete(0, tk.END)
        self.group1_entry.insert(0, self.metadata.conditions.group1)
        self.group1_entry.place(x=BASE_X + EDITOR_PADDING_X, y=META_SECTION_1_BASE_Y + 10 + 3 * PADDING_Y)

        # Group2
        self.group2_label = tk.Label(self, text="Group 2:", font=FONT_M)
        self.group2_label.place(x=BASE_X, y=META_SECTION_1_BASE_Y + 4 * PADDING_Y)
        self.group2_entry = str_entry(self)
        self.group2_entry.place(x=BASE_X + EDITOR_PADDING_X, y=META_SECTION_1_BASE_Y + 10 + 4 * PADDING_Y)
        self.group2_entry.delete(0, tk.END)
        self.group2_entry.insert(0, self.metadata.conditions.group2)

        # Treatment section
        self.treatment_label = tk.Label(self, text="Treatment section", font=FONT_L)
        self.treatment_label.place(x=BASE_X, y=META_SECTION_2_BASE_Y)

        self.update_idletasks()
        self.treatment_table = TreatmentTable(self, self.metadata.treatments, width=440, height=490)
        self.treatment_table.place(x=BASE_X + 60, y=BOTTOM_TABLE_Y)

        self.save_metadata_button = tk.Button(self, text="Save Metadata", font=FONT_M, command=self.save_metadata)
        self.save_metadata_button.place(x=230, y=META_SECTION_2_BASE_Y + 40)

    def clear_button_press(self) -> None:
        self.metadata = Metadata(METADATA_TEMPLATE)

        self.dye_button.config(text=f"{self.metadata.conditions.ratiometric_dye.capitalize()}")
        self.framerate_entry.delete(0, tk.END)
        self.framerate_entry.insert(0, str(self.metadata.conditions.framerate))
        self.group1_entry.delete(0, tk.END)
        self.group1_entry.insert(0, self.metadata.conditions.group1)
        self.group2_entry.delete(0, tk.END)
        self.group2_entry.insert(0, self.metadata.conditions.group2)

        self.treatment_table = TreatmentTable(self, self.metadata.treatments, width=440, height=490)
        self.treatment_table.place(x=BASE_X + 60, y=BOTTOM_TABLE_Y)

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

        self.treatment_table.save_values() # this needs to happen first so that the correct treatments are used later

        error_message = ""
        try:
            FPM = int(self.framerate_entry.get())
        except ValueError:
            error_message += "Frames/min must be an integer number.\n"
        self.metadata.treatments = self.treatment_table.treatments
        try:
            self.metadata.treatments.remove_empty_values()
        except ValueError:
            error_message += "Please make sure all intended begin and end fields are filled."
        # this error partially overlaps with what validate_treatments check for, but I think it is different
        # enough to deserve to be handled separately

        if error_message:
            messagebox.showerror(message=error_message)
            return

        self.metadata.conditions.ratiometric_dye = self.dye_button["text"]
        self.metadata.conditions.framerate = FPM # type: ignore
        self.metadata.conditions.group1 = self.group1_entry.get()
        self.metadata.conditions.group2 = self.group2_entry.get()

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
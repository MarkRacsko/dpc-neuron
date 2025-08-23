from threading import Thread
import tkinter as tk
from tkinter import messagebox


from interface.gui_panels import ConfigFrame, MetadataFrame
from interface.gui_constants import FONT_M
from interface.gui_constants import BASE_X, BASE_Y, PADDING_X, PADDING_Y, OFFSCREEN_X
from interface.gui_constants import MAIN_BUTTON_Y, PANEL_W, PANEL_Y
from interface.gui_constants import DISPLAY_MODES, MESSAGES

from processing.classes.engine import AnalysisEngine
from processing.classes.converter import Converter
from processing.classes.toml_data import Config


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
        self.config_panel = ConfigFrame(self.root, self.config, self.config_button.winfo_width(), width=PANEL_W, height=320)

        # Metadata editor panel
        self.metadata_panel = MetadataFrame(self.root, self.metadata_button.winfo_width(), self.metadata_button.winfo_height(), width=PANEL_W, height=640)
    
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

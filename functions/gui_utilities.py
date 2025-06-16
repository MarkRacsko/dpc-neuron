import tkinter as tk
from tkinter import filedialog


def select_folder(label: tk.Label, variable: tk.StringVar) -> None:
    """Called when pressing the button to select the output folder where results will be saved.
    """
    path = filedialog.askdirectory(title="Select a folfer")
    label.config(text="Selected: yes")
    variable.set(path)

def analyze_button_press(target: tk.StringVar, p: tk.IntVar, t: tk.IntVar, g: tk.IntVar, r: tk.IntVar) -> None:
    pass

def config_button_press(mode: tk.StringVar) -> None:
    mode.set("config")

def metadata_button_press(mode: tk.StringVar) -> None:
    mode.set("metadata")
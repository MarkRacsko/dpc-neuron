import tkinter as tk
from tkinter import messagebox
from gui_utilities import select_folder, analyze_button_press, config_button_press, metadata_button_press
from functools import partial


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

def main():
    root = tk.Tk()
    root.title("Ca Measurement Analyzer")
    current_mode = tk.StringVar(value="default")
    root.geometry(DISPLAY_MODES[current_mode.get()])
    root.resizable(False, False)

    def resize_window(*args):
        root.geometry(DISPLAY_MODES[current_mode.get()])

    current_mode.trace_add("write", resize_window)

    # Browse target folder
    target_label = tk.Label(root, text="Data folder:", font=FONT_S)
    target_label.place(x=BASE_X, y=BASE_Y)
    path_label = tk.Label(root, text="Selected: not yet", font=FONT_S)
    path_label.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y)
    target_path = tk.StringVar(value="./data")
    target_command = partial(select_folder, path_label, target_path)
    target_button = tk.Button(root, text="Browse...", font=FONT_S, command=target_command)
    target_button.place(x=BASE_X + PADDING_X, y=BASE_Y, width=100, height=30)
    
    # Processing checkbox
    check_p_state = tk.IntVar()
    check_p = tk.Checkbutton(root, text="Process", font=FONT_S, variable=check_p_state)
    check_p.place(x=BASE_X, y=BASE_Y + PADDING_Y)

    # Tabulation checkbox
    check_t_state = tk.IntVar()
    check_t = tk.Checkbutton(root, text="Tabulate", font=FONT_S, variable=check_t_state)
    check_t.place(x=BASE_X, y=BASE_Y + 2* PADDING_Y)

    # Graphing checkbox
    check_g_state = tk.IntVar()
    check_g = tk.Checkbutton(root, text="Make graphs", font=FONT_S, variable=check_g_state)
    check_g.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y + PADDING_Y)

    # Repeat checkbox
    check_r_state = tk.IntVar()
    check_r = tk.Checkbutton(root, text="Repeat", font=FONT_S, variable=check_r_state)
    check_r.place(x=BASE_X + 2 * PADDING_X, y=BASE_Y + 2 * PADDING_Y)
    
    # Analyze button
    analyze_args = [target_path, check_p_state, check_t_state, check_g_state, check_r_state]
    analyze_button = tk.Button(root, text="Analyze", font=FONT_L, command=partial(analyze_button_press, *analyze_args))
    analyze_button.place(x=BASE_X, y=4 * PADDING_Y, width=120, height=60)

    # Config button
    config_button = tk.Button(root, text="Edit\nconfig", font=FONT_S, command=partial(config_button_press, current_mode))
    config_button.place(x=BASE_X + 1.2 * PADDING_X, y=4 * PADDING_Y, width=120, height=60)

    # Metadata button
    metadata_button = tk.Button(root, text="Edit\nmetadata", font=FONT_S, command=partial(metadata_button_press, current_mode))
    metadata_button.place(x=BASE_X + 2.4 * PADDING_X, y=4 * PADDING_Y, width=120, height=60)

    root.protocol("WM_DELETE_WINDOW", exit) # Regression but I'm willing to accept that for now.
    root.mainloop()

if __name__ == "__main__":
    main()
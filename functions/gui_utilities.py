import tkinter as tk


def int_entry(parent, **kwargs) -> tk.Entry:
    """Serves the dubious purpose of saving me a bit of typing in the GUI class and to make sure all entry fields are
    uniform.
    """
    return tk.Entry(parent, justify="right", width=12, **kwargs)

def str_entry(parent, **kwargs) -> tk.Entry:
    """Serves the dubious purpose of saving me a bit of typing in the GUI class and to make sure all entry fields are
    uniform.
    """
    return tk.Entry(parent, width=12, **kwargs)
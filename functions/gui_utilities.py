import tkinter as tk


def int_entry(parent, **kwargs) -> tk.Entry:
    return tk.Entry(parent, justify="right", width=12, **kwargs)

def str_entry(parent, **kwargs) -> tk.Entry:
    return tk.Entry(parent, width=12, **kwargs)
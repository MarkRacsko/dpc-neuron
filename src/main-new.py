import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _(tabs):
    tabs
    return


@app.cell
def _(mo):
    get_rows, set_rows = mo.state([
        {"name": "baseline", "range": (0, 100)}
    ])

    def add_row(_):
        current_rows = get_rows()
        set_rows(current_rows + [{"name": "New", "range": (0, 50)}])

    add_btn = mo.ui.button(label="Add Row", on_click=add_row)
    return add_btn, get_rows, set_rows


@app.cell
def _(add_btn, get_rows, mo, set_rows):
    ui_container = mo.ui.array([
        mo.ui.dictionary({
            "name": mo.ui.text(value=row["name"]),
            "range": mo.ui.range_slider(0, 200, value=row["range"])
        })
        for row in get_rows()
    ], on_change=set_rows)

    rows_layout = mo.vstack([
        mo.hstack([row["name"], row["range"]], justify="start")
        for row in ui_container
    ])

    treatment_stack = mo.vstack([rows_layout, add_btn])
    return (treatment_stack,)


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(
    SD_mult,
    actions_explanation,
    analysis,
    clear_cache,
    convert_from_cache,
    convert_to_cache,
    frame_number,
    framerate,
    group_1,
    group_2,
    metadata_file,
    method,
    mo,
    photo_corr,
    ratiometric,
    smoothing_range,
    target_folder,
    treatment_stack,
):
    tab0 = mo.vstack([
        mo.md(text="##Instructions"),
        mo.md(text=actions_explanation),
        mo.hstack([analysis, convert_to_cache], justify="start"),
        mo.hstack([clear_cache, convert_from_cache], justify="start")
    ])

    tab1 = mo.vstack([
        mo.md(text="##Input"),
        target_folder,
        method,
        SD_mult,
        smoothing_range,
        mo.hstack([mo.md(text="Photobleaching correction:"), photo_corr], justify="start"),
    ])

    tab2 = mo.vstack([
        mo.md(text="##Placeholder..."),
        metadata_file,
        mo.md(text="##Conditions"),
        ratiometric,
        framerate,
        frame_number,
        group_1,
        group_2,
        mo.md(text="##Treatments"),
        treatment_stack
    ])

    tabs = mo.ui.tabs({"Actions": tab0, "Config": tab1, "Metadata": tab2})
    return (tabs,)


@app.cell
def _(mo):
    # UI element definitions
    actions_explanation = """
    To inspect or change global config settings that apply to all measurements, go to the Config tab. You can save these settings to a file, from which they will be re-loaded next time. Individual measurement parameters are read from files as well, each measurement's folder is supposed to contain a metadata.toml file. You can use the Metadata tab to create, edit, and save these. If no metadata file exists in the selected folder, the default settings are loaded from a template, but file saving is **not** automatic. You need to save each metadata file manually.

    To speed up analysis work, a caching mechanism is used. The point is that reading and writing Excel files is slow, but if we save our data in a better file format, we will be able to perform repeated analyses with different settings without having to read the Excel data again, and this benefit will persist after the app is closed. (As opposed to just keeping the data in memory.) Each measurement's Excel file is read, and the data is saved in a different format which is significantly faster to read, but cannot be used for other work. If you want to inspect the results or load the data into a different program, you will need to convert back to Excel.
    """

    analysis = mo.ui.button(label="Analyze", full_width=True, tooltip="Perform data analysis with the current settings.")
    convert_to_cache = mo.ui.button(label="Convert to cache", full_width=True, tooltip="Convert Excel data to the cached format.")
    convert_from_cache = mo.ui.button(label="Convert to Excel", full_width=True, tooltip="Convert data back to Excel files. Overwrites originals.")
    clear_cache = mo.ui.button(label="Clear cache", full_width=True, tooltip="Delete all cached files. Excel data remains untouched.")


    target_folder = mo.ui.file_browser(label="Data folder:", selection_mode="directory", multiple=False)
    method = mo.ui.dropdown(label="Method:", options=["baseline", "previous", "derivative"])
    SD_mult = mo.ui.number(label="SD multiplier:", start=1, stop=5, step=1, value=3)
    smoothing_range = mo.ui.number(label="Smoothing range:", start=1, stop=15, step=2, value=5)
    photo_corr = mo.ui.switch()

    metadata_file = mo.ui.file_browser(label="Measurement folder:", selection_mode="directory", multiple=False)
    ratiometric = mo.ui.switch(label="Ratiometric dye")
    framerate = mo.ui.number(label="Framerate", start=1, stop=1000, value=60)
    frame_number = mo.ui.number(label="Number of frames", start=1, stop=1000000, step=1, value=300)
    group_1 = mo.ui.text(label="Group 1:")
    group_2 = mo.ui.text(label="Group 2:")
    return (
        SD_mult,
        actions_explanation,
        analysis,
        clear_cache,
        convert_from_cache,
        convert_to_cache,
        frame_number,
        framerate,
        group_1,
        group_2,
        metadata_file,
        method,
        photo_corr,
        ratiometric,
        smoothing_range,
        target_folder,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # TODO

    1. Implement reading config from file
    2. remove_row button
    3. Add folder selection to the metadata tab, build a blank metadata file from template, if no metadata file exists.
    4. Setting the initial state by reading the contents of the metadata.toml file
    5. Implement saving the file.
    6. Figure out how to make the metadata file selector's initial path be the folder selected by target_folder
    7. ~~Build the main panel with the 4 buttons~~, hook them up to the data processing backend
    8. Add a progress bar to provide feedback on data analysis and file conversions.
    9. Reconsider the program's architecture and general behavior. It may be better for repeated analysis with different settings to keep all input data in memory, instead of re-reading cached files. I don't remember exactly why I chose this design, and it may well be the correct one, but I will need to think about this more.
    """)
    return


if __name__ == "__main__":
    app.run()

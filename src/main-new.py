import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # TODO

    1. Implement reading config from file
    2. Get a metadata.toml file from home
    3. remove_row button
    4. Add folder selection to the metadata tab, build a blank metadata file from template, if no metadata file exists.
    5. Setting the initial state by reading the contents of the metadata.toml file
    6. Implement saving the file.
    7. Figure out how to make the metadata file selector's initial path be the folder selected by target_folder
    8. Build the main panel with the 6 buttons, hook them up to the data processing backend
    """)
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
def _(tabs):
    tabs
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Ideas

    - 6 main buttons as before
    - under them, the two editor panels using mo.ui.tabs

    ## Config panel
    - target folder: mo.ui.file_browser
    - method: mo.ui.dropdown
    - sd multiplier: mo.ui.number
    - smoothing range: mo.ui.number
    - photobleaching correction: mo.ui.switch (True/False)
    - settings for filters such as potassium amp threshold, sd, baseline amp threshold, etc...

    ## Metadata editor
    - ratiometric dye: mo.ui.switch
    - framerate: mo.ui.number or slider?
    - group1: mo.ui.text
    - group2: mo.ui.text
    - Treatments: a vertical stack of range_sliders? + some entry field to set the total time, and a button to add a new row
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(
    SD_mult,
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

    tabs = mo.ui.tabs({"Config": tab1, "Metadata": tab2})
    return (tabs,)


@app.cell
def _(mo):
    # UI element definitions
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


if __name__ == "__main__":
    app.run()

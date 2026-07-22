import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


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
        photo_corr,
    ])

    tab2 = mo.vstack([
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
    target_folder = mo.ui.file_browser(label="Target folder:", selection_mode="directory", multiple=False)
    method = mo.ui.dropdown(label="Method", options=["baseline", "previous", "derivative"])
    SD_mult = mo.ui.number(label="SD multiplier", start=1, stop=5, step=1, value=3)
    smoothing_range = mo.ui.number(label="Smoothing range", start=1, stop=15, step=2, value=5)
    photo_corr = mo.ui.switch(label="Photobleaching correction")

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
        method,
        photo_corr,
        ratiometric,
        smoothing_range,
        target_folder,
    )


@app.cell
def _(frame_number, mo):
    treatment_stack = mo.vstack([
        mo.ui.range_slider(label="baseline", start=1, stop=frame_number.value)
    ])
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


if __name__ == "__main__":
    app.run()

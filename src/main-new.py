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
        {"name": "baseline", "range": [0, 60]}
    ])
    # What this state is:
    # A list of dictionaries, where each dict stores the following:
    # name: the string entered into the text box
    # range: the current settings of the range selector -- max value is frame_number.value
    # range is a list not a tuple because that's what range_slider.value returns

    def add_row(_):
        current_rows = get_rows()
        set_rows(current_rows + [{"name": "New", "range": (0, 50)}])

    def remove_row(_):
        current_rows = get_rows()
        current_rows.pop() # remove last element
        set_rows(current_rows)

    add_btn = mo.ui.button(label="Add new row", on_click=add_row)
    remove_btn = mo.ui.button(label="Remove last row", on_click=remove_row)
    return add_btn, get_rows, remove_btn, set_rows


@app.cell
def _(add_btn, get_rows, mo, remove_btn, set_rows):
    ui_container = mo.ui.array([
        mo.ui.dictionary({
            "name": mo.ui.text(value=row["name"]),
            "range": mo.ui.range_slider(0, 200, value=row["range"], full_width=True)
        })
        for row in get_rows()
    ], on_change=set_rows)

    rows_layout = mo.vstack([
        mo.hstack([row["name"], row["range"]], justify="start")
        for row in ui_container
    ])

    treatment_stack = mo.vstack([rows_layout, mo.hstack([add_btn, remove_btn], justify="start")])
    return (treatment_stack,)


@app.cell
def _():
    import marimo as mo
    import yaml
    from interface.gui_constants import CONFIG_TEMPLATE, METADATA_TEMPLATE
    from analysis.toml_data import Config, Metadata, Treatments
    from pathlib import Path

    return Config, METADATA_TEMPLATE, Metadata, Path, mo, yaml


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
    report_name,
    save_config_btn,
    smoothing_range,
    summary_name,
    target_folder,
    treatment_stack,
):
    # Actions tab
    tab0 = mo.vstack([
        mo.md(text="##Instructions"),
        mo.md(text=actions_explanation),
        mo.hstack([analysis, convert_to_cache], justify="start"),
        mo.hstack([clear_cache, convert_from_cache], justify="start")
    ])

    # Config tab
    tab1 = mo.vstack([
        save_config_btn,
        mo.md(text="##Input"),
        target_folder,
        method,
        SD_mult,
        smoothing_range,
        mo.hstack([mo.md(text="Photobleaching correction:"), photo_corr], justify="start"),
        mo.md(text="##Output"),
        report_name,
        summary_name
    ])

    # Metadata tab
    tab2 = mo.vstack([
        mo.md(text="##Placeholder..."),
        metadata_file,
        mo.md(text="##Conditions"),
        mo.hstack([mo.md(text="Ratiometric dye:"), ratiometric], justify="start"),
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
def _(
    Metadata,
    config: "Config",
    get_metadata,
    load_metadata,
    mo,
    save_config,
):
    # UI element definitions
    actions_explanation = """
    To inspect or change global config settings that apply to all measurements, go to the Config tab. You can save these settings to a file, from which they will be re-loaded next time. Individual measurement parameters are read from files as well, each measurement's folder is supposed to contain a metadata.toml file. You can use the Metadata tab to create, edit, and save these. If no metadata file exists in the selected folder, the default settings are loaded from a template, but file saving is **not** automatic. You need to save each metadata file manually.

    To speed up analysis work, a caching mechanism is used. The point is that reading and writing Excel files is slow, but if we save our data in a better file format, we will be able to perform repeated analyses with different settings without having to read the Excel data again, and this benefit will persist after the app is closed. (As opposed to just keeping the data in memory.) Each measurement's Excel file is read, and the data is saved in a different format which is significantly faster to read, but cannot be used for other work. If you want to inspect the results or load the data into a different program, you will need to convert back to Excel.
    """

    # BUTTONS
    analysis = mo.ui.button(label="Analyze", full_width=True, tooltip="Perform data analysis with the current settings.")
    convert_to_cache = mo.ui.button(label="Convert to cache", full_width=True, tooltip="Convert Excel data to the cached format.")
    convert_from_cache = mo.ui.button(label="Convert to Excel", full_width=True, tooltip="Convert data back to Excel files. Overwrites originals.")
    clear_cache = mo.ui.button(label="Clear cache", full_width=True, tooltip="Delete all cached files. Excel data remains untouched.")

    save_config_btn = mo.ui.button(label="Save settings", on_click=save_config)

    # CONFIG
    target_folder = mo.ui.file_browser(label="Data folder:",
                                       selection_mode="directory",
                                       multiple=False,
                                       initial_path=config.input.target_folder)
    method = mo.ui.dropdown(label="Method:",
                            options=["baseline", "previous", "derivative"],
                           value=config.input.method)
    SD_mult = mo.ui.number(label="SD multiplier:",
                           start=1, stop=5, step=1,
                           value=config.input.SD_multiplier)
    smoothing_range = mo.ui.number(label="Smoothing range:",
                                   start=1, stop=15, step=2,
                                   value=config.input.smoothing_range)
    photo_corr = mo.ui.switch(value=config.input.correction)

    report_name = mo.ui.text(label="Report filename:", value=config.output.report_name)
    summary_name = mo.ui.text(label="Summary filename:", value=config.output.summary_name)

    # METADATA
    metadata: Metadata = get_metadata()

    metadata_file = mo.ui.file_browser(label="Measurement folder:", selection_mode="directory", multiple=False, on_change=load_metadata)
    ratiometric = mo.ui.switch(value=metadata.conditions.ratiometric_dye)
    framerate = mo.ui.number(label="Framerate", start=1, stop=1000, value=metadata.conditions.framerate)
    frame_number = mo.ui.number(label="Number of frames", start=1, stop=1000000, step=1, value=metadata.conditions.frame_number)
    group_1 = mo.ui.text(label="Group 1:", value=metadata.conditions.group1)
    group_2 = mo.ui.text(label="Group 2:", value=metadata.conditions.group2)
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
        report_name,
        save_config_btn,
        smoothing_range,
        summary_name,
        target_folder,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # TODO

    - Setting the initial state by reading the contents of the metadata.toml file
    - Implement saving the file.
    - Figure out how to make the metadata file selector's initial path be the folder selected by target_folder
    - ~~Build the main panel with the 4 buttons~~, hook them up to the data processing backend
    - Add a progress bar to provide feedback on data analysis and file conversions.
    - Reconsider the program's architecture and general behavior. It may be better for repeated analysis with different settings to keep all input data in memory, instead of re-reading cached files. I don't remember exactly why I chose this design, and it may well be the correct one, but I will need to think about this more.
    """)
    return


@app.cell
def _(Config, METADATA_TEMPLATE, Metadata, mo, yaml):
    def load_config() -> Config:
        with open("config.yaml", "r") as f:
            config_dict = yaml.safe_load(f)

        config = Config(False, config_dict)
        return config

    def save_config(_) -> None:
        with open("config.yaml", "w") as f:
            yaml.dump(config.to_dict(), f)

    config: Config = load_config()

    get_metadata, set_metadata = mo.state(Metadata(METADATA_TEMPLATE))
    # this is necessary because we need to update the loaded values whenever a new folder is selected
    return config, get_metadata, save_config, set_metadata


@app.cell
def _(METADATA_TEMPLATE, Metadata, Path, set_metadata, yaml):
    def load_metadata(path):
        # path is a Sequence of paths, because that's how the mo.ui.file_browser object works
        selected_folder = Path(path[0])
        metadata_path = selected_folder / "metadata.yaml"

        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                loaded_metadata = yaml.safe_load(f)
                set_metadata(Metadata(loaded_metadata))
        else:
            set_metadata(Metadata(METADATA_TEMPLATE))

    return (load_metadata,)


if __name__ == "__main__":
    app.run()

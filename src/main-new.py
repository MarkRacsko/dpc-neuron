import marimo

__generated_with = "0.23.15"
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
        set_rows(current_rows + [{"name": "New", "range": [0, 50]}])

    def remove_row(_):
        current_rows = get_rows()
        current_rows.pop() # remove last element
        set_rows(current_rows)

    add_btn = mo.ui.button(label="Add new row", on_click=add_row)
    remove_btn = mo.ui.button(label="Remove last row", on_click=remove_row)
    return add_btn, get_rows, remove_btn, set_rows


@app.cell
def _(
    add_btn,
    get_rows,
    metadata: "Metadata",
    mo,
    remove_btn,
    save_metadata_btn,
    set_rows,
):
    ui_container = mo.ui.array([
        mo.ui.dictionary({
            "name": mo.ui.text(value=row["name"]),
            "range": mo.ui.range_slider(0, metadata.conditions.frame_number, value=row["range"], full_width=True)
        })
        for row in get_rows()
    ], on_change=set_rows)

    rows_layout = mo.vstack([
        mo.hstack([row["name"], row["range"]], justify="start")
        for row in ui_container
    ])

    treatment_stack = mo.vstack([rows_layout, mo.hstack([add_btn, remove_btn, save_metadata_btn], justify="start")])
    return (treatment_stack,)


@app.cell
def _():
    import marimo as mo
    import yaml
    from interface.gui_constants import CONFIG_TEMPLATE, METADATA_TEMPLATE
    from analysis.toml_data import Config, Metadata, Treatments
    from pathlib import Path

    return Config, METADATA_TEMPLATE, Metadata, Path, Treatments, mo, yaml


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
        mo.md(text="##Measurement folder:"),
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
    mo,
    save_config,
    update_frame_number,
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

    ratiometric = mo.ui.switch(value=metadata.conditions.ratiometric_dye)
    framerate = mo.ui.number(label="Framerate", start=1, stop=1000, value=metadata.conditions.framerate)
    frame_number = mo.ui.number(label="Number of frames", start=1, stop=1000000, step=1, value=metadata.conditions.frame_number, on_change=update_frame_number)
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
        metadata,
        method,
        photo_corr,
        ratiometric,
        report_name,
        save_config_btn,
        smoothing_range,
        summary_name,
        target_folder,
    )


@app.cell
def _(load_metadata, mo):
    file_browser_label = "Click on a name to enter that folder, click on a folder icon to select it. You can only select one at a time. "
    metadata_file = mo.ui.file_browser(label=file_browser_label, selection_mode="directory", multiple=False, on_change=load_metadata)
    return (metadata_file,)


@app.cell
def _(get_metadata, set_metadata):
    def update_frame_number(n):
        current_metadata = get_metadata()
        current_metadata.conditions.frame_number = n
        set_metadata(current_metadata)

    return (update_frame_number,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # TODO

    ## Port existing functionality to marimo:
    - Disentangle the DAG so the metadata file browser is not constantly re-rendered and re-run
    - ~~Implement saving the file.~~ make it work
    - Figure out how to make the metadata file selector's initial path be the folder selected by target_folder
    - ~~Build the main panel with the 4 buttons~~, hook them up to the data processing backend
    - Add a progress bar to provide feedback on data analysis and file conversions.
    - Reconsider the program's architecture and general behavior. It may be better for repeated analysis with different settings to keep all input data in memory, instead of re-reading cached files. I don't remember exactly why I chose this design, and it may well be the correct one, but I will need to think about this more.

    ## New functionality to implement:
    - Use mo.ui.dataframe and/or mo.ui.data_explorer widget(s) to let the user inspect results
    - Architectural change: let the user decide which folders to include in the analysis, instead of using all subfolders in the selected folder
    - Make the metadata editor clearly indicate which folder's data we're looking at
    - Add more filters to exclude bad cells
    - Maybe let the user choose which fitlers to use
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
def _(
    METADATA_TEMPLATE,
    Metadata,
    Path,
    Treatments,
    get_metadata,
    get_rows,
    set_metadata,
    set_rows,
    yaml,
):
    def load_metadata(tuple_of_selected_paths):
        # mo.ui.file_browser passes a tuple of FileBrowserFileInfo objects to its callback function
        selected_folder = Path(tuple_of_selected_paths[0].path)
        metadata_path = selected_folder / "metadata.yaml"

        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                loaded_metadata = yaml.safe_load(f)
                set_metadata(Metadata(loaded_metadata))
        else:
            set_metadata(Metadata(METADATA_TEMPLATE))

        translate_treatments_to_rows()

    def translate_rows_to_treatments():
        rows = get_rows()
        current_metadata = get_metadata()
        new_treatments_obj = Treatments()

        for row in rows:
            begin, end = row["range"] # we are unpacking a 2 item list, so this is fine
            new_treatments_obj[row["name"]] = (begin, end)

        current_metadata.treatments = new_treatments_obj
        set_metadata(current_metadata)

    def translate_treatments_to_rows():
        current_metadata = get_metadata()
        rows = []
        for name, treatment in current_metadata.treatments.items():
            rows.append({"name": name, "range": [*treatment.values]})
            # treatment.values returns a tuple of the begin and end value, and I'm unpacking those into the range list
        set_rows(rows)

    return load_metadata, translate_rows_to_treatments


@app.cell
def _(get_metadata, metadata_file, mo, translate_rows_to_treatments, yaml):
    def save_metadata(_):
        metadata_path = metadata_file.value[0].path / "metadata.yaml"
        translate_rows_to_treatments()

        current_metadata = get_metadata()
        metadata_dict = current_metadata.to_dict()

        with open(metadata_path, "w") as f:
            yaml.dump(metadata_dict, f)

    save_metadata_btn = mo.ui.button(label="Save metadata", on_click=save_metadata)
    return (save_metadata_btn,)


if __name__ == "__main__":
    app.run()

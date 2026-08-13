import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")


@app.cell
def _(analysis, clear_cache, convert_from_cache, convert_to_cache, mo):
    actions_explanation = """
    To inspect or change global config settings that apply to all measurements, go to the Config tab. You can save these settings to a file, from which they will be re-loaded next time. Individual measurement parameters are read from files as well, each measurement's folder is supposed to contain a metadata.toml file. You can use the Metadata tab to create, edit, and save these. If no metadata file exists in the selected folder, the default settings are loaded from a template, but file saving is **not** automatic. You need to save each metadata file manually.

    To speed up analysis work, a caching mechanism is used. The point is that reading and writing Excel files is slow, but if we save our data in a better file format, we will be able to perform repeated analyses with different settings without having to read the Excel data again, and this benefit will persist after the app is closed. (As opposed to just keeping the data in memory.) Each measurement's Excel file is read, and the data is saved in a different format which is significantly faster to read, but cannot be used for other work. If you want to inspect the results or load the data into a different program, you will need to convert back to Excel.
    """

    process_check = mo.ui.checkbox(label="Process")
    graph_check = mo.ui.checkbox(label="Make graphs")
    sum_check = mo.ui.checkbox(label="Summarize")
    repeat_check = mo.ui.checkbox(label="Repeat")

    top_section_1 = mo.vstack([
        mo.md(text="#Instructions"),
        mo.md(text=actions_explanation),
    ], align="center")

    top_section_2 = mo.vstack([
        mo.hstack([process_check, graph_check, sum_check, repeat_check], justify="center"),
        mo.hstack([analysis, convert_to_cache], justify="start"),
        mo.hstack([clear_cache, convert_from_cache], justify="start"),
    ])

    mo.vstack([top_section_1, top_section_2], gap=1.5)
    return


@app.cell(disabled=True)
def _(AnalysisEngine, Converter):
     # these wont work just yet
    analysis_engine = AnalysisEngine()
    converter = Converter()
    return


@app.cell
def _(analysis, clear_cache, convert_from_cache, convert_to_cache):
    # FUNCTIONALITY
    # Analysis
    if analysis.value:
        pass

    # Conversion to cache
    if convert_to_cache.value:
        pass

    # Clear the cache
    if clear_cache.value:
        pass

    # Conversion from cache to Excel
    if convert_from_cache.value:
        pass

    return


@app.cell
def _(
    SD_mult,
    method,
    mo,
    photo_corr,
    report_name,
    save_config_btn,
    smoothing_range,
    summary_name,
    target_folder,
):
    config_section_header = """
    #Global configuration"""

    config_section_1 = mo.vstack([
        mo.md(text=config_section_header),
    ], align="center")

    config_section_2 = mo.vstack([
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
    mo.vstack([config_section_1, config_section_2, save_config_btn])
    return


@app.cell
def _(metadata_file, mo):
    metadata_header = mo.vstack([
        mo.md(text="#Experiment details")
    ], align="center")

    metadata_section_1 = mo.vstack([
        mo.md(text="##Measurement folder:"),
        metadata_file,
    ])
    mo.vstack([metadata_header, metadata_section_1])
    return


@app.cell
def _(
    frame_number,
    framerate,
    group_1,
    group_2,
    mo,
    ratiometric,
    treatment_stack,
):
    metadata_section_2 = mo.vstack([
        mo.md(text="##Conditions"),
        mo.hstack([mo.md(text="Ratiometric dye:"), ratiometric], justify="start"),
        framerate,
        frame_number,
        group_1,
        group_2,
        mo.md(text="##Treatments"),
        treatment_stack
    ])
    metadata_section_2
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
    return get_rows, set_rows


@app.cell
def _(get_rows, mo, set_rows, ui_container):
    def add_row(_):
        set_rows(ui_container.value + [{"name": "New", "range": [0, 50]}])

    def remove_row(_):
        current_rows = get_rows()
        current_rows.pop() # remove last element
        set_rows(current_rows)

    add_btn = mo.ui.button(label="Add new row", on_click=add_row)
    remove_btn = mo.ui.button(label="Remove last row", on_click=remove_row)
    return add_btn, remove_btn


@app.cell
def _(frame_number, get_rows, mo):
    ui_container = mo.ui.array([
        mo.ui.dictionary({
            "name": mo.ui.text(value=row["name"]),
            "range": mo.ui.range_slider(0, frame_number.value, value=row["range"], full_width=True)
        })
        for row in get_rows()
    ])

    rows_layout = mo.vstack([
        mo.hstack([row["name"], row["range"]], justify="start")
        for row in ui_container
    ])
    return rows_layout, ui_container


@app.cell
def _(add_btn, mo, remove_btn, rows_layout, save_metadata_btn):
    treatment_stack = mo.vstack([rows_layout, mo.hstack([add_btn, remove_btn, save_metadata_btn], justify="start")])
    return (treatment_stack,)


@app.cell
def _(config: "Config", metadata, mo, save_config):
    # UI element definitions

    # BUTTONS
    analysis = mo.ui.run_button(label="Analyze", full_width=True, tooltip="Perform data analysis with the current settings.")
    convert_to_cache = mo.ui.run_button(label="Convert to cache", full_width=True, tooltip="Convert Excel data to the cached format.")
    convert_from_cache = mo.ui.run_button(label="Convert to Excel", full_width=True, tooltip="Convert data back to Excel files. Overwrites originals.")
    clear_cache = mo.ui.run_button(label="Clear cache", full_width=True, tooltip="Delete all cached files. Excel data remains untouched.")

    save_config_btn = mo.ui.button(label="Save settings", on_click=save_config, full_width=True)

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

    ratiometric = mo.ui.switch(value=metadata.conditions.ratiometric_dye)
    framerate = mo.ui.number(label="Framerate", start=1, stop=1000, value=metadata.conditions.framerate)
    frame_number = mo.ui.number(label="Number of frames", start=1, stop=1000000, step=1, value=metadata.conditions.frame_number)
    group_1 = mo.ui.text(label="Group 1:", value=metadata.conditions.group1)
    group_2 = mo.ui.text(label="Group 2:", value=metadata.conditions.group2)
    return (
        SD_mult,
        analysis,
        clear_cache,
        convert_from_cache,
        convert_to_cache,
        frame_number,
        framerate,
        group_1,
        group_2,
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
def _(config: "Config", mo):
    file_browser_label = "Click on a name to enter that folder, click on a folder icon to select it. You can only select one at a time. "
    metadata_file = mo.ui.file_browser(
        label=file_browser_label,
        selection_mode="directory",
        multiple=False,
        initial_path=config.input.target_folder
    )
    return (metadata_file,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # TODO

    ## Port existing functionality to marimo:
    - ~~Build the main panel with the 4 buttons~~, hook them up to the data processing backend
    - Add a progress bar to provide feedback on data analysis and file conversions.
    - Reconsider the program's architecture and general behavior. It may be better for repeated analysis with different settings to keep all input data in memory, instead of re-reading cached files. I don't remember exactly why I chose this design, and it may well be the correct one, but I will need to think about this more.
    - Do something about the fact that the two file browsers display the same thing yet behave differently.

    ## New functionality to implement:
    - Use mo.ui.dataframe and/or mo.ui.data_explorer widget(s) to let the user inspect results
    - Architectural change: let the user decide which folders to include in the analysis, instead of using all subfolders in the selected folder
    - Make the metadata editor clearly indicate which folder's data we're looking at
    - Add more filters to exclude bad cells
    - Maybe let the user choose which fitlers to use
    - Maybe add a button to hide/show the config panel
    """)
    return


@app.cell
def _(Config, yaml):
    # Config handling, creation
    def load_config() -> Config:
        with open("config.yaml", "r") as f:
            config_dict = yaml.safe_load(f)

        config = Config(False, config_dict)
        return config

    def save_config(_) -> None:
        with open("config.yaml", "w") as f:
            yaml.dump(config.to_dict(), f)

    config: Config = load_config()
    return config, save_config


@app.cell
def _(METADATA_TEMPLATE, Metadata, load_metadata, metadata_file):
    # Metadata loader cell
    metadata = load_metadata(metadata_file.value[0].path) if metadata_file.value else Metadata(METADATA_TEMPLATE)
    return (metadata,)


@app.cell
def _(METADATA_TEMPLATE, Metadata, Path, Treatments, get_rows, yaml):
    def load_metadata(selected_folder: Path) -> Metadata:
        metadata_path = selected_folder / "metadata.yaml"

        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                loaded_metadata = yaml.safe_load(f)
                metadata = Metadata(loaded_metadata)
        else:
            metadata = Metadata(METADATA_TEMPLATE)

        rows = get_rows()
        new_treatments_obj = Treatments()

        for row in rows:
            begin, end = row["range"] # we are unpacking a 2 item list, so this is fine
            new_treatments_obj[row["name"]] = (begin, end)

        metadata.treatments = new_treatments_obj

        return metadata

    return (load_metadata,)


@app.cell
def _(Treatments, deepcopy, metadata, metadata_file, mo, ui_container, yaml):
    def save_metadata(_):
        metadata_path = metadata_file.value[0].path / "metadata.yaml"

        current_metadata = deepcopy(metadata)
        new_treatments_obj = Treatments()

        for row in ui_container.value:
            begin, end = row["range"] # we are unpacking a 2 item list, so this is fine
            new_treatments_obj[row["name"]] = (begin, end)

        current_metadata.treatments = new_treatments_obj

        metadata_dict = current_metadata.to_dict()

        with open(metadata_path, "w") as f:
            yaml.dump(metadata_dict, f)

    save_metadata_btn = mo.ui.button(label="Save metadata", on_click=save_metadata)
    return (save_metadata_btn,)


@app.cell
def _():
    import marimo as mo
    import yaml
    from interface.templates import CONFIG_TEMPLATE, METADATA_TEMPLATE
    from analysis.toml_data import Config, Metadata, Treatments
    from pathlib import Path
    from copy import deepcopy
    from analysis.engine import AnalysisEngine
    from analysis.converter import Converter

    return (
        AnalysisEngine,
        Config,
        Converter,
        METADATA_TEMPLATE,
        Metadata,
        Path,
        Treatments,
        deepcopy,
        mo,
        yaml,
    )


if __name__ == "__main__":
    app.run()

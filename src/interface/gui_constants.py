FONT_L = ("Arial", 18)
FONT_M = ("Arial", 16)
FONT_S = ("Arial", 12)

BASE_X = 20
BASE_Y = 20
PADDING_Y = 30
PADDING_X = 120
MAIN_BUTTON_Y = 90 # used for placing the frame containing the main 6 buttons and alternatively the progress tracker
PANEL_Y = 230 # used for placing the config and metadata editor panels
PANEL_W = 480 # width of the editor panels
CONFIG_H = 380 # height of the config editor panel
META_H = 640 # height of the metadata editor panel

CONF_SECTION_1_BASE_Y = 20 # first section of the config editor panel
CONF_SECTION_2_BASE_Y = 230 # second section of the config editor panel
META_SECTION_1_BASE_Y = 70 # first section of the metadata editor panel
META_SECTION_2_BASE_Y = 230 # second section of the metadata editor panel
EDITOR_PADDING_X = 200 # BASE_X + this is the x coord for items in the second column of the editor panels
OFFSCREEN_X = 600 # this is used to move unwanted items offscreen
BOTTOM_TABLE_Y = 270 # y coord for the treatment table on the metadata panel

# this defines different screen sizes, resizing is done by a callback function that triggers when the value of
# the StringVar storing the current mode changes.
DISPLAY_MODES: dict[str, str] = {
    "analysis": "500x180",
    "config": "500x640",
    "metadata": "500x800"
}

# this is used for selecting what message we want to display when the program has finished its work
# 1st number: processing y/n, 2nd: summary y/n, 3rd: graphing y/n
MESSAGES: dict[tuple[int, int, int], str] = {
    (0, 0, 0): "Please select at least one action to perform.",
    (1, 0, 0): "Finished processing data.",
    (0, 1, 0): "Finished summarizing results.",
    (0, 0, 1): "Finished making graphs.",
    (1, 1, 0): "Finished processing data and summarizing results.",
    (1, 0, 1): "Finished processing data and making graphs.",
    (0, 1, 1): "Finished summarizing results and making graphs.",
    (1, 1, 1): "Finished processing data, summarizing results, and making graphs."
}

CONFIG_TEMPLATE = {
    "input": {
        "target_folder": "",
        "method": "previous",
        "SD_multiplier": 3,
        "smoothing_range": 5,
        "amp_threshold": 0.3,
        "cv_threshold": 0.1,
        "correction": "True"
    },
    "output": {
        "report_name": "report_",
        "summary_name": "summary"
    }
}

# this is used to create new metadata if the user selects a folder without a metadata.toml file
METADATA_TEMPLATE = {
    "conditions": {
        "ratiometric_dye": "true",
        "framerate": 60,
        "group1": "",
        "group2": ""
    },
    "treatments": {
        "baseline": {
            "begin": 0,
            "end": 60
        }
    }
}

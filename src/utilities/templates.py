CONFIG_TEMPLATE = {
    "input": {
        "target_folder": "",
        "method": "previous",
        "SD_multiplier": 3,
        "smoothing_range": 5,
        "amp_threshold": 0.3,
        "cv_threshold": 0.1,
        "correction": True
    },
    "output": {
        "report_name": "report_",
        "summary_name": "summary"
    }
}

# this is used to create new metadata if the user selects a folder without a metadata.toml file
METADATA_TEMPLATE = {
    "conditions": {
        "ratiometric_dye": True,
        "framerate": 60,
	"frame_number": 600,
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
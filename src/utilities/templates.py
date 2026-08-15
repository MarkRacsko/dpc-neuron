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

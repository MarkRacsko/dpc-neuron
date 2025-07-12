# dpc-neuron

This project is meant to help me and my colleagues analyze and visualize results from my dental pulp - sensory neuron coculture experiments and from Ca measurement microscopy workflows in general.

# Installation
(For those unfamiliar with Python and uv.)
1. To install uv, go to https://docs.astral.sh/uv/getting-started/installation/ and follow the instructions for your OS. (On Windows, type "powershell" into the Start menu search bar, open that, and paste the command there.)
2. Download my program from this Github page by clicking on the green "<> Code" button and selecting "Download ZIP".
3. Extract the zip archive wherever you like.
4. Open the extracted folder where this README and all the other files are. Open a command prompt or terminal here. (On Windows, click the address bar when you are in the right folder, type "cmd" without the quotes and hit Enter.)
5. Run the following command: `uv sync`

(If you're using Mac or Linux, uv will work the same, just use the appropriate install instructions from the linked page, and whatever terminal you have.)

# Usage
To run the program, type `uv run main.py` into the command prompt opened from this folder, or alternatively you can use the provided launcher file. (Which just runs the above uv command.)

The program takes a folder as its input and expects data from individual measurements to be grouped into subfolders within this folder. (All data from one day of experiments goes in one subfolder for me, but this is not mandatory, only the structure is.) Experimental conditions are described by a metadata.toml file that must be present in every subfolder to be processed. Processing configurations are set by a config.toml file, located in the same folder as this README and the Python files. The expected contents of these files are described further below.

## The graphical interface
The program exists in two versions, a command line only one (main.py) and one with a graphical interface (main-gui.py). The graphical version performs the same analysis tasks and has checkboxes that correspond to the CLI version's command line flags, namely:
- Process: to do data processing and create reports
- Tabulate: to summarize all existing reports
- Make graphs: to draw line plots for each cell
- Repeat: normally the program ignores folders that already have a report file in them, this option tells it to process everything anyway.

The GUI version also comes with an editor for the program's config file and the experiment metadata files. The use of these should be fairly straightforward, the only catch is that the metadata editor **does NOT preserve unsaved changes** to its fields if you switch over to the config editor. (The original contents of the loaded metadata file is preserved though.) If you select a folder without a metadata file, the program will create a blank one from a template, or alternatively you can copy an existing metadata file (or the sample) to new folders. If you copy the sample, make sure to rename it to "metadata.toml" as both the editor and the analyzer expect this exact file name. Of course this toml file can also be edited manually, as detailed below.

The bottom row of buttons allows you to convert Excel files to and from the cache (explained further below), or delete the existing one. (Which is necessary if you've changed the Excel files in any folder. If you've merely added new files in one or more new folders, emptying the cache is not necessary.) If you've added new folders with measurements in them, manually pressing the "Convert to cache" button is not actually needed, the program will automatically perform this conversion when necessary.

## How to use the .toml files
Tom's Obvious, Minimal Language (toml) is a simple file format for configuration files, editable by any text editor such as Windows Notepad. A toml file is (can be) divided into sections, each of which can have their own subsections. Subsections may be indented for the sake of clarity, but this is not required. Sections are delineated by their name in square brackets, like this: [section_name], while subsections are marked by [section_name.subsection_name]. The actual configuration data is stored as key-value pairs, like this:

key_1 = "value_1"  
key_2 = 2

When editing one of these files, only change the values, not the names of the keys. Subsections within the treatment section of the metadata file can be renamed, but other section headers cannot.

### The main config file
This file consists of 2 sections:
- input:
    - target_folder: The default option for the processing target
    - method: What method to use for determining if cells reacted to an agonist. Valid values are "baseline", "previous", and "derivative".
    - SD_multiplier: A number (doesn't have to be an integer, decimal separator for non-integers must be dot not comma) describing by how many standard deviations of the baseline must a cell's response amplitude exceed the basis of comparison (the baseline mean, the mean of the last few timepoints of the previous agonist window, or the mean of the baseline's first order derivative) to be considered to have reacted to that agonist.
    - smoothing_range: An odd integer number describing the window size used for the smoothing step. Each value in a cell's data is replaced by the mean of neighbouring values in a window of this size. The size is the total number of elements not the number of neighbours to consider on each side, which is why it must be odd.
- output:
    - report_name: The final file name for subfolder level reports will be constructed from this name, the name of this subfolder, and the .xlsx extension.
    - summary_name: The final file name for the overall summary report.

### The metadata files
These have 2 section:
- conditions:
    - ratiometric_dye: "true" if you're using Fura2 and "false" otherwise.
    - group1 and group2: These describe the experimental groups to be compared. Can be any string values, make sure to put them in quotation marks. Also these group names must be present in the individual file names as the actual grouping is done by checking which group name the file name contains.

- treatments: Consists of subsections, one for each agonist you've applied during the measurement. Subsections need to be named [treatments.something]. The first subsection is expected to be called baseline, others can be named whatever you want (so long as you follow the treatments. naming convention). In the sample file the subsections are indented, but they don't have to be. If you add more subsections, each must have its name in square brackets and contain two keys, one called begin and one called end. The end value should be equal to the next agonist's begin value, or the total number of frames in the measurement for the final agonist used (which in a neuron context is usually potassium chloride, which should be called KCl.) The values for these two keys describe when a given agonist treatment began and ended, respectively. They should be integers.

Note: The reason an agonist's end value and the next agonist's begin value **can** be the same number is that when you take a slice of some sequence in Python like this: sequence[0:60] the first index is inclusive but the second one is not, so the slices [0:60] and [60:120] will not overlap. And the reason the end value and the next begin **should** be the same is that this guarantees detection of slow reactions where the cell does react to the given agonist, but not necessarily in the time window when said agonist is applied.

## The cache
Reading Excel files into pandas DataFrames is dreadfully slow, so I've implemented a caching mechanism to convert Excel files to a more performant file format, and work with those. When the program first encounters a measurement (= a subfolder in the target folder), it reads all measurement files there and converts them into this faster format, storing them in a .cache folder. Do not touch this folder, unless you want to force the program to re-read the excel files, in which case you should delete the .cache folder, for which there is a button in the graphical user interface. (In case you've added or replaced some measurement files. The program does not individually track which files have been cached.)

TODO:
- deal with windows vs UNIX path differences
- investigate why converting to feather format failed on windows at work
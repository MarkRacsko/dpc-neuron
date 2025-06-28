# dpc-neuron

This project is meant to help me analyze and visualize results from my dental pulp - sensory neuron coculture experiments.

# Usage
The program takes a folder as its input and expects data from individual measurements to be grouped into subfolders within this folder. (All data from one day of experiments goes in one subfolder for me, but this is not mandatory, only the structure is.) Experimental conditions are described by a metadata.toml file that must be present in every subfolder to be processed. Processing configurations are set by a config.toml file, located in the same folder as this README and the Python files. The expected contents of these files are described below.

At the moment, the program only has a command line interface, but I'm going to make a graphical one soon.

## How to use the .toml files
Tom's Obvious, Minimal Language (toml) is a simple file format for configuration files, editable by any text editor such as Windows Notepad. A toml file is (can be) divided into sections, each of which can have their own subsections. Subsections may be indented for the sake of clarity, but this is not required. Sections and subsections are delineated by their names in square brackets, like this: [section_name]. The actual configuration data is stored as key-value pairs, like this:

key_1 = "value_1"  
key_2 = 2

When editing one of these files, only change the values, not the names of the keys. Subsections within the treatment section of the metadata file can be renamed, but other section headers cannot.

### The main config file
This file consists of 3 sections:
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
    - ratiometric_dye: 1 if you're using Fura2 and 0 otherwise. (Technically other values considered true and false by Python are also acceptable, but let's keep it simple. 0 and 1.)
    - group1 and group2: These describe the experimental groups to be compared. Can be any string values, make sure to put them in quotation marks. Also these group names must be present in the individual file names as the actual grouping is done by checking which group name the file name contains.
- treatments: Consists of subsections, one for each agonist you've applied during the measurement. Subsections need to be named "treatments.something", without the quotation marks. The first subsection is expected to be called baseline, others can be named whatever you want (so long as you follow the treatments. naming convention). In the sample file the subsections are indented, but they don't have to be. If you add more subsections, each must have its name in square brackets and contain two keys, one called begin and one called end. The end value should be equal to the next agonist's begin value, or the total number of frames in the measurement for the final agonist used (which in a neuron context is usually potassium chloride, which should be called K+.) The values for these two keys describe when a given agonist treatment began and ended, respectively. They should be integers.

TODO:
- switch to uv
- update documentation and provide install instructions
- replace tk.Text with tk.Entry everywhere
- maybe add config options to change properties (size, color, ...) of the graphs
- try to get my hands on the Igor macro Thomas wrote to see how he did things -> asked Balázs
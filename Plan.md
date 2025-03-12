# Ideas
- Results will be in Excel files, one per measured petri dish / ibidi chamber, all measurements from the same day in a single folder, named after the day of measurement (yyyymmdd).
- Already processed days should be separated from unprocessed ones, three options:
    1. Have separate subfolders for them (data/processed and data/new)
    2. Have the program put a hidden file in folders it has already processed, then have it always scan through the entire data folder and ignore folders that contain a marker file.
    3. Have a single database file of some description, that stores this information. Added benefit of this one is that it could also store measurement outcomes such as numbers and percentages of TRPM3/TRPA1/TRPV1 positive neurons.
- When we finish processing a day's measurements, we:
    1. Move its folder from data/new to data/processed
    2. Put the marker file its folder
    3. Update the database (which might just be a .xlsx file)
- The marker file could also be a report of outcomes, so if this file exists then the folder must have been processed already. Then have separate functionality to tabulate these day by day reports and compile an overall report.

- CLI interface, I'm not bothering with a GUI with this one. Arguments/options:
    -p / --process: Process measurements found in subfolders of the given folder. Ignores measurements for whom a report already exists.
    -t / --tabulate: Compile an overall report from measurement reports found in subfolders of the given folder. Can be done at the same time as -p, in this case the program will process everything then make the report. Ideally in the latter case we make the report on the fly, instead of reading in the report files after writing them.
    -pt: shorthand for -p and -t together
    -r / --re: If given with -p, then ignore all existing reports and reprocess everything.
    DIR: The directory to process. Individual result files must be in subdirectories. Defaults to ./data if not provided by user.

- Internal handling of CL arguments:
    1. Check sanity of arguments. Every argument must match one of the available flags or be a valid path. If any argument fails this check or there are more than 1 path-like arguments provided, print an appropriate error message and exit.
    2. Set flag based boolean variables that govern the program's behaviour and explore the given path, looking for measurement results without an accompanying report or report files if -t is set. Create a list that stores subdir names where unprocessed measurements are detected.



# Planned structure of the project
What the program should be doing:
1. Validate command line arguments and exit if they are incorrect
2. Set boolean variables based on plags, explore given directory. Populate list of subdirs where unprocessed files are found.
3. Go through these subdirectories and process them one at a time:
    1. Make list of all Excel files, create report df
    2. Iterate through the list:
        1. Read in file, select columns of interest ([col for col in input_df.columns if "Average" in col])
        2. Parse filename to determine experimental condition
        2. For each column (=cell), perform smoothing, derivation, determine which agonists it responds to
        3. Update report appropriately
    3. Write out report and update tabulated report if -t is in play.
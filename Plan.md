# Ideas
- Results will be in Excel files, one per measured petri dish / ibidi chamber, all measurements from the same day in a single folder, named after the day of measurement (yyyymmdd).
- Already processed days should be separated from unprocessed ones, three options:
    1. ~~Have separate subfolders for them (data/processed and data/new)~~ Unnecessary.
    2. ~~Have the program put a hidden file in folders it has already processed, then have it always scan through the entire data folder and ignore folders that contain a marker file.~~ Went with a version of this, except the marker file is the Excel file that stores the results from that folder.
    3. ~~Have a single database file of some description, that stores this information. Added benefit of this one is that it could also store measurement outcomes such as numbers and percentages of TRPM3/TRPA1/TRPV1 positive neurons.~~ An overall report that tabulates all results will exist but checking individual report files per folder is more convenient. 
- When we finish processing a day's measurements, we:
    1. ~~Move its folder from data/new to data/processed~~
    2. Put the marker file in its folder
    3. ~~Update the database (which might just be a .xlsx file)~~
- The marker file could also be a report of outcomes, so if this file exists then the folder must have been processed already. Then have separate functionality to tabulate these day by day reports and compile an overall report.

- Config file structure:
    1. input section: for input related options such as the default input folder path and the naming convention of experimental groups. These will be used to identify which file is what so the experimental conditions can be included in the report. Regex should be used, not just keywords like "only".
    2. report section: this is for the individual measurement day outputs
    3. tabulated_report: this is for the overall compilation of results

- CLI interface, I'm not bothering with a GUI with this one. Arguments/options:
    -p / --process: Process measurements found in subfolders of the given folder. Ignores measurements for whom a report already exists.
    -t / --tabulate: Compile an overall report from measurement reports found in subfolders of the given folder. Can be done at the same time as -p, in this case the program will process everything then make the report. Ideally in the latter case we make the report on the fly, instead of reading in the report files after writing them.
    -pt: shorthand for -p and -t together
    -r / --re: If given with -p, then ignore all existing reports and reprocess everything.
    DIR: The directory to process. Individual result files must be in subdirectories. Defaults to ./data if not provided by user.

- Internal handling of CL arguments:
    1. Check sanity of arguments. Every argument must match one of the available flags or be a valid path. If any argument fails this check or there are more than 1 path-like arguments provided, print an appropriate error message and exit.
    2. Set flag based boolean variables that govern the program's behaviour and explore the given path, looking for measurement results without an accompanying report or report files if -t is set. ~~Create a list that stores subdir names where unprocessed measurements are detected.~~ This last bit is unnecessary. Iterating over folders is not going to be the performance bottleneck here.

- Path manipulations using pathlib:
    1. Check that the target location is a directory, exit if not.
    2. For each subfolder in target dir:
        1. figure out report path: report_path = subfolder / report_filename (f string here probably because I want to incorporate the subfolder name into the report's name)
        2. Check if the report exists, continue if it does and -r is NOT set.
        3. Process Excel files of measurements found there and make the report. Add it to an overall report if -t or -pt is active.

- Structure of the Excel files produced from ImageJ measurement results:
    - sheets named F380 and F340
    - First column is Time
    - Second column is Background
    - Rest of the columns are measurements from cells
    - Column names reflect cell type

- Processing work:
    1. Read events from accompanying event.csv file, create report dataframe
    2. Figure out which type of measurement this is based on the filename
    3. Correct photobleaching in both F380 and F340 data, calculate ratio
    4. Determine threshold (baseline + stdev * 3)
    5. Smooth (mean 5, for now)
    6. Take the derivative
    7. For each event period, determine if the cell reacted to that event (=agonist), if so, determine amplitude
    8. Update the report appropriately

- Detecting reactions:
    A. any value above baseline mean + 2*std in the given window
    B. any value above mean of last 10 values of previous window + 2*std of baseline
    C. use derivative and baseline mean + 2*std, because responses are usually rapid (if perfusion is good)

- OOP redesign:
    - DataAnalyzer class: creates a SubDir instance for each subdirectory in the target folder, then calls different methods on these based on which flags were passed, also storing the tabulated report DataFrames
    - SubDir class: represents the individual subdirectories where measurement results are stored and has methods to do processing, tabulation, and graphing on a subdirectory level

- Tabulation idea:
    - take it out of the Subdir class
    - the analyzer class iterates over its list of Subdir instances and collects their reports into a dictionary where the keys are the column names in the report. For each report, we check if its columns are in the dict already, if not we add them as a new key, then either way, we add the report's content to the list of reports stored under that key.
    - dict[list[str], list[Series[int]]]
    - then we simply iterate over this dict as key value pairs. For each key, we create a new sheet in the summary, then add all the results from the same conditions into a single df as new columns, column names being the name/date of the experiment

- Graphical config file editor idea:
    - merge report and tabulated report, since .xlsx is the only output format I want to support and it is sufficient
    - have one column with labels and one with text boxes, a dropdown menu for the method, and a Browse button for the folder

- Metadata editor idea:
    - textboxes for the conditions
    - 3 labels and textboxes for the name, begin, end fields
    - add, edit, remove buttons
    - the editor is a class with its mechanism implemented using methods and the individual treatments are stored in Treatment objects
    - Treatment is a dataclass with name, begin, end attrs

- Potential sources of errors:
    - target folder does not exist or does not adhere to prescribed structure
    - SD_multiplier not a number
    - smoothing_range not odd or too large
    - sheets incorrectly named in measurement files
    - keys missing from metadata or config
    - in metadata:
        - ratiometric_dye not in ["true", "false"]
        - group names are wrong
        - treatment begin or end values not integers
        - a begin value is larger than or equal to its corresponding end value
        - a begin value is smaller than the preceding end value

- Make IO operations faster because openpyxl is painfully slow:
    1. Use calamine engine instead
    2. Use a faster file format like json or feather
    3. Use multithreading because the program is overwhelmingly IO bound (90% of processing time spent on IO)

- Conversion utility:
    - has a list of every subfolder
    - conversion to feather:
        1. for folder in subfolders:
        2. list target files
        3. check if a cache folder exists, if not, make one
        4. for every measurement file:
            1. read file with calamine
            2. for every sheet in the file:
            3. filename = original file name - xlsx + . + sheetname + .feather
            4. if filename does not exist: df.to_feather(cache/filename)

# Planned structure of the project
What the program should be doing:
1. Read config file, which will store options that would be inconvenient to have to pass everytime or to make into magic strings/values.
2. Validate command line arguments and exit if they are incorrect.
3. Set boolean variables based on plags, explore given directory. Populate list of subdirs where unprocessed files are found.
4. Go through these subdirectories and process them one at a time:
    0. Check if result file exits, move on to next subdir if it does and -r flag is not set
    1. Make list of all Excel files, create report df
    2. Iterate through the list:
        1. Read in file, both the F340 and F380 sheets
        2. Parse filename to determine experimental condition
        3. Separete the data into Time, Background, Cells (**Both sheets**)
        4. Save cell type information (ie column names) before conversion to numpy
        5. Convert to numpy and transpose because I prefer rows = cells
        6. Substract background (this column will be named "Background" in all files)
        7. For each column (=cell):
            1. Correct photobleaching (F340 and F380 separately)
            2. Calculate ratio
            3. Smooth (mean 5)
            4. Determine which agonists it responds to, relative amplitude of the response
        
        8. Update report appropriately
    3. Write out report and update tabulated report if -t is in play.
5. Write the tabulated summary
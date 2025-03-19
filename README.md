# dpc-neuron

This project is meant to help me analyze and visualize results from my dental pulp - sensory neuron coculture experiments.

TODO:
- ~~write basic plotting code, no plt wrapper because of memory leak~~
- ~~design CLI interface~~
- ~~design internal structure of project~~
- ~~deal with path handling, implement looking in subfolders for report file and measurement files~~
- implement the actual processing work:
    - write helper functions
    - figure out how to check responses, increase compared to last x frames of previous event period is probably going to be the way to go, BUT: high K+ may not induce response after Capsaicin even if the cell is a neuron.
    - taking the derivative and working with that may be a better idea, if a cell responds to an agonist, the response is typically (although not necessarily) quick 
    - implement the solution
    - design output report format, implement saving results
- create config file, it might be better if I replace magic strings like the report name with a configurable input, this is what I'm thinkging of:
    - [default-settings]: target_folder, report_name, report_extension, column_of_interest, tabulated_report_name, tabulated_report_extension
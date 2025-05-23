# dpc-neuron

This project is meant to help me analyze and visualize results from my dental pulp - sensory neuron coculture experiments.

TODO:
- implement IO and preprocessing steps:
    - ~~read F340 and F380 separately~~
    - ~~split the data (time, background, cells)~~
    - ~~read experimental condition~~
    - implement regex for recognizing conditions for improved flexibility (this is a maybe)
- implement the actual processing work:
    - ~~write helper functions~~
    - figure out how to check responses, increase compared to last x frames of previous event period is probably going to be the way to go, BUT: high K+ may not induce response after Capsaicin even if the cell is a neuron.
    - taking the derivative and working with that may be a better idea, if a cell responds to an agonist, the response is typically (although not necessarily) quick 
    - ~~implement the solution~~ or just implement all 3 of my ideas and a config option to choose which one I want
    - figure out what's the best way to implement all 3 ideas at the same time:
        1. Separate functions, put them in a dict, call based on method arg. Upside: pretty. Downside: code duplication, and patch to the common logic needs to be applied 3 times.
        2. Just if statements. Upside: no need to define additional functions, any logic change needs to be applied only once. Downside: the code is a bit of a mess, looks ugly, and main point of refactoring was to reduce the size of my code blocks.
    - figure out how to use my smoothing function on a 2d array
    - ~~design output report format, implement saving results~~
- ~~figure out how to achieve the same result in a vectorized way~~
- refactor gross long code vomit into pretty functions -> WIP
- try to get my hands on the Igor macro Thomas wrote to see how he did things -> asked Balázs
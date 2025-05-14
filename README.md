# dpc-neuron

This project is meant to help me analyze and visualize results from my dental pulp - sensory neuron coculture experiments.

TODO:
- implement IO and preprocessing steps:
    - read F340 and F380 separately
    - split the data (time, background, neurons, DPCs)
    - read experimental condition
- implement the actual processing work:
    - write helper functions
    - figure out how to check responses, increase compared to last x frames of previous event period is probably going to be the way to go, BUT: high K+ may not induce response after Capsaicin even if the cell is a neuron.
    - taking the derivative and working with that may be a better idea, if a cell responds to an agonist, the response is typically (although not necessarily) quick 
    - implement the solution
    - design output report format, implement saving results
- figure out how to achieve the same result in a vectorized way
- refactor gross long code vomit into pretty functions
- try to get my hands on the Igor macro Thomas wrote to see how he did things
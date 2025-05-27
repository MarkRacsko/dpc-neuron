# dpc-neuron

This project is meant to help me analyze and visualize results from my dental pulp - sensory neuron coculture experiments.

TODO:
- implement IO and preprocessing steps:
    - ~~read experimental condition~~
    - implement regex for recognizing conditions for improved flexibility (this is a maybe)
- implement the actual processing work:
    - tabulate report files into one overall file, different experimental conditions (sets of agonists used) need to be handled somehow
    - ~~make line plots for each cell~~
- investigate pd.concat FutureWarning about concating empty stuff
- reevaluate my hotfix to the shape issues, think through if this is the correct solution, apply solution to all versions of the function
- implement saving the ratio values and the coefficients
- fix misalignment on graphs
- find out why graphs look nothing like what I made in Origin
- try to get my hands on the Igor macro Thomas wrote to see how he did things -> asked Balázs
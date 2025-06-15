# dpc-neuron

This project is meant to help me analyze and visualize results from my dental pulp - sensory neuron coculture experiments.

TODO:
- investigate pd.concat FutureWarning about concating empty stuff
- reevaluate my hotfix to the shape issues, think through if this is the correct solution, apply solution to all versions of the function
- ~~implement saving the ratio values~~ and the coefficients
- try to get my hands on the Igor macro Thomas wrote to see how he did things -> asked Balázs
- implement config based grouping of results
- maybe add config options to change properties (size, color, ...) of the graphs
- change event system to a metadata approach, where we store relevant details in a toml file or something similar, that way the regex stuff can be avoided too, and there's room for more configuration options, like supporting fura2 and fluo4 experiments simultaniously
- switch to uv
- implement a GUI version
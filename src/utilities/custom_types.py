"""Serves the purpose of storing all my custom type hints in one place."""
from typing import Protocol

import pandas as pd

# These are used in analysis.engine.py:
type ExperimentalCondition = list[str] # list of agonists used in this particular experiment
type ExperimentalData = tuple[str, pd.Series] # the string is the folder name where the experiment's data is;
# the pd.Series is multi-indexed, by the reaction column names and shows how many cells belong to a given combination
# of reactions (such as TRPM3+ TRPA1- TRPV1- neurons)
# In the Nuitka-compiled version of the program, the [int] typehint had to be removed from pd.Series because
# it caused an error

# This is used in analysis.toml_data.py, by the Treatment class:
type TimeValue = int | str
# This is used in the _Treatment class for the begin and end values of agonist treatments. The reason it exists is that
# the way my validation and data processing functions work forces makes it so that these fields cannot be declared as
# just int or just str. (And I don't want to redesign the whole thing at this point.)

class ProgressBar(Protocol):
    """This Protocol exists because objects from libraries like marimo can sometimes be a huge pain to typehint, and the 
    mo.status.progess_bar is. The real object has several more attributes and methods, I only implemented update because
    this is the only part I will need.
    """
    def update(self, increment: int = 1, title: str | None = None, subtitle: str | None = None) -> None:
        ...
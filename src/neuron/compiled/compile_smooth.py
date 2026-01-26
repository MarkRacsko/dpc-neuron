from setuptools import setup
from Cython.Build import cythonize
from pathlib import Path
import numpy as np

extension = ["cy_smooth", ["cy_smooth.pyx"]]
parent = Path(__file__).parent

setup(
    ext_modules=cythonize(str(parent) + "/cy_smooth.pyx"),
    include_dirs=[np.get_include()],
    py_modules=[],
)
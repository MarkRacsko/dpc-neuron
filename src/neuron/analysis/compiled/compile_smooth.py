import os
import numpy as np

from setuptools import setup, Extension
from Cython.Build import cythonize
from pathlib import Path

extension = Extension(
    name="cy_smooth",
    sources=["cy_smooth.pyx"],
    include_dirs=[np.get_include()]
)

setup(
    ext_modules=cythonize(extension),
    include_dirs=[np.get_include()],
    py_modules=[],
)

folder = Path(__file__).parent
for file in folder.iterdir():
    if file.is_file():
        if file.match("cy_smooth.c"):
            os.remove(file) # not entirely necessary, but might as well
        if file.match("cy_smooth.cpython*.so"):
            os.rename(file, folder / "cy_smooth.so")
        elif file.match("cy_smooth.cpython*.pyd"):
            os.rename(file, folder / "cy_smooth.pyd")
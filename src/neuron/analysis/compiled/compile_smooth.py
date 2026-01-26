from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

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
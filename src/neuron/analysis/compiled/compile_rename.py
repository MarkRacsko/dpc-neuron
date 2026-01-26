import os
from pathlib import Path

folder = Path(__file__).parent
for file in folder.iterdir():
    if file.is_file():
        if file.match("cy_smooth.cpython*.so"):
            os.rename(file, folder / "cy_smooth.so")
        elif file.match("cy_smooth.cpython*.pyd"):
            os.rename(file, folder / "cy_smooth.pyd")
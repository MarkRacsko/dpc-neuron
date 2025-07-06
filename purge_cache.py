from pathlib import Path
from shutil import rmtree

target = Path("./data")
for folder in target.iterdir():
    if folder.is_dir():
        rmtree(folder / ".cache")

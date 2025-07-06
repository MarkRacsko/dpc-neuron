from pathlib import Path
import os

target = Path("./data")

for folder in target.iterdir():
    if folder.is_dir():
        for file in folder.iterdir():
            if file.is_file():
                if "feather" in file.name:
                    os.remove(file)
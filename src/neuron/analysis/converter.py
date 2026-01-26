from pathlib import Path
from shutil import rmtree
from threading import Lock, Thread
from tkinter import IntVar

import pandas as pd
import python_calamine as cala

NAME_SHEET_SEP: str = " SHEET_"
CACHE_NAME = ".cache"

class Converter:
    """Serves the purpose of creating and managing a cache from the input measurement files because reading Excel with
    pandas is painfully slow compared to feather or other binary file formats.
    """
    def __init__(self, folder: Path, report_name: str) -> None:
        self.target_folder = folder.absolute()
        self.report_name = report_name
        self.lock = Lock()

    def convert_to_pickle(self, finished_files: IntVar):
        """Reads in all Excel files found in this measurement folders and converts each of their sheets into a separate
        pickled file. Uses calamine because it is a bit faster than openpyxl.

        Args:
            finished_files (IntVar): A tk variable received from the GUI to keep track of how many files have been
            finished.
        """
        def work(folder: Path, cache_path: Path, files: list[Path]):
            for file in files:
                wb = cala.CalamineWorkbook.from_path(folder / file)
                for sheet in wb.sheet_names:
                    content = wb.get_sheet_by_name(sheet).to_python()
                    headers, numbers = content[0], content[1:]
                    df = pd.DataFrame(data=numbers, columns=headers)

                    df.to_pickle(cache_path / f"{file.name}{NAME_SHEET_SEP}{sheet}.pkl")

                with self.lock:
                    finished_files.set(finished_files.get() + 1)
        
        threads = []
        for folder in self.target_folder.iterdir():
            if folder.is_dir():
                cache_path = folder / CACHE_NAME
                report_path = folder / f"{self.report_name}{folder.name}.xlsx"
                measurement_files = [Path(f.name) for f in folder.glob("*.xlsx") if f != report_path]
                if not cache_path.exists():
                    Path.mkdir(cache_path)
                    threads.append(Thread(target=work, args=(folder, cache_path, measurement_files)))
        
        if threads: # at least one cache needs to be created
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        with self.lock:
            finished_files.set(0)

    def convert_to_excel(self, finished_files: IntVar):
        """Converts the cached pickle files back into Excel, overwriting the original files.

        Args:
            finished_files (IntVar): A tk variable received from the GUI to keep track of how many files have been
            finished.
        """
        def work(folder: Path, cache_path: Path):
            cached_files = [f for f in cache_path.glob("*.pkl")]
            excel_data: dict[str, list[tuple[str, pd.DataFrame]]] = {}
            # filenames mapped to lists of their content as (sheetname, data) pairs
            
            for file in cached_files:
                file_name = file.name
                file_data = pd.read_pickle(cache_path / file_name)
                
                file_name, sheet_name = file_name.split(sep=NAME_SHEET_SEP)
                sheet_name = sheet_name.rstrip(".feather")

                if file_name in excel_data:
                    excel_data[file_name].append((sheet_name, file_data))
                else:
                    excel_data[file_name] = [(sheet_name, file_data)]

            for file_name, contents in excel_data.items():
                contents = sorted(contents, key=lambda x: x[0])
                with pd.ExcelWriter(folder / file_name) as writer:
                    for sheet, df in contents:
                        df.to_excel(writer, sheet_name=sheet, index=False)
                
                with self.lock:
                    finished_files.set(finished_files.get() + 1)


        threads = []
        for folder in self.target_folder.iterdir():
            cache_path = folder / CACHE_NAME
            if cache_path.exists:
                threads.append(Thread(target=work, args=(folder, cache_path)))
            else:
                continue

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        with self.lock:
            finished_files.set(0)

    def purge_cache(self):
        for folder in self.target_folder.iterdir():
            if folder.is_dir():
                cache_path = folder / CACHE_NAME
                if cache_path.exists():
                    rmtree(cache_path)
        
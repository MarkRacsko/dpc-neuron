import pandas as pd
import python_calamine as cala
from pathlib import Path

NAME_SHEET_SEP: str = " SHEET:"

class Converter:
    """Serves the purpose of creating a cache from the input measurement files because reading Excel with pandas is
    painfully slow compared to feather or other binary file formats.
    """
    def __init__(self, folder: Path, cache_path: Path, report_path: Path) -> None:
        self.folder = folder.absolute()
        self.cache_path = cache_path.absolute()
        self.report_path = report_path.absolute()

    def convert_to_feather(self):
        """Reads in all Excel files found in this measurement folder and converts each of their sheets into a separate
        .feather file. Uses calamine because it is a bit faster than openpyxl.
        """
        measurement_files = [Path(f.name) for f in self.folder.glob("*.xlsx") if f != self.report_path]
        if not self.cache_path.exists():
            Path.mkdir(self.cache_path)

        for file in measurement_files:
            wb = cala.CalamineWorkbook.from_path(self.folder / file)
            for sheet in wb.sheet_names:
                content = wb.get_sheet_by_name(sheet).to_python()
                headers, numbers = content[0], content[1:]
                df = pd.DataFrame(data=numbers, columns=headers)

                df.to_feather(self.cache_path / f"{file.stem}{NAME_SHEET_SEP}{sheet}.feather")


    def convert_to_excel(self):
        """Converts the cached .feather files back into Excel, overwriting the original files.
        """
        if not self.cache_path.exists:
            return

        cached_files = [Path(f.name) for f in self.cache_path.glob("*.feather")]
        excel_data: dict[str, list[tuple[str, pd.DataFrame]]] = {}
        
        for file in cached_files:
            file_name, sheet_name = file.stem.split(sep=NAME_SHEET_SEP)
            file_data = pd.read_feather(self.cache_path / file)

            if file.name in excel_data:
                excel_data[file.name].append((sheet_name, file_data))
            else:
                excel_data[file.name] = [(sheet_name, file_data)]

        for file_name, contents in excel_data.items():
            file_name, _ = file_name.split(sep=NAME_SHEET_SEP)
            with pd.ExcelWriter(self.folder / f"{file_name}.xlsx") as writer:
                for sheet, df in contents:
                    df.to_excel(writer, sheet_name=sheet, index=False)

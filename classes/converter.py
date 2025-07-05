import pandas as pd
import python_calamine as cala
from pathlib import Path

class Converter:
    """Serves the purpose of creating a cache from the input measurement files because reading Excel with pandas is
    painfully slow compared to feather or other binary file formats.
    """
    def __init__(self, folder: Path, cache_path: Path, report_path: Path) -> None:
        self.folder = folder
        self.cache_path = cache_path
        self.report_path = report_path

    def convert_to_feather(self):
        """Reads in all Excel files found in this measurement folder and converts each of their sheets into a separate
        .feather file. Uses calamine because it is a bit faster than openpyxl.
        """
        measurement_files = [f for f in self.folder.glob("*.xlsx") if f != self.report_path]

        for file in measurement_files:
            wb = cala.CalamineWorkbook.from_path(file)
            for sheet in wb.sheet_names:
                content = wb.get_sheet_by_name(sheet).to_python()
                headers, numbers = content[0], content[1:]
                df = pd.DataFrame(data=numbers, columns=headers)

                df.to_feather(self.cache_path / f"{file.name}.{sheet}.feather")


    def convert_to_excel(self):
        """Converts the cached .feather files back into Excel, overwriting the original files.
        """

        cached_files = [f for f in self.cache_path.glob("*.feather")]
        excel_data: dict[str, set[tuple[str, pd.DataFrame]]] = {}

        for file in cached_files:
            sheet_name = file.suffixes[0]
            file_data = pd.read_feather(file)
            if file.name in excel_data:
                excel_data[file.name].add((sheet_name, file_data))
            else:
                excel_data[file.name] = {(sheet_name, file_data)}

        for file_name, contents in excel_data.items():
            with pd.ExcelWriter(self.folder / f"{file_name}.xlsx") as writer:
                for sheet, df in contents:
                    df.to_excel(writer, sheet_name=sheet, index=False)

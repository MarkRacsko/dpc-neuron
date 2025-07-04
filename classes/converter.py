import pandas as pd
import python_calamine as cala
from pathlib import Path

class Converter:
    def __init__(self, target: Path, report_name: str) -> None:
        self.folder_list = list(target.iterdir())
        # generators cannot be iterated over more than once, and this object may need to be
        self.report_name = report_name

    def convert_to_feather(self):
        for folder in self.folder_list:
            report_path = folder / f"{self.report_name}{folder.name}.xlsx"
            measurement_files = [f for f in folder.glob("*.xlsx") if f != report_path]
            cache_path = folder / "cache"

            if not cache_path.exists():
                Path.mkdir(cache_path)

            for file in measurement_files:
                wb = cala.CalamineWorkbook.from_path(file)
                for sheet in wb.sheet_names:
                    content = wb.get_sheet_by_name(sheet).to_python()
                    headers, numbers = content[0], content[1:]
                    df = pd.DataFrame(data=numbers, columns=headers)

                    df.to_feather(cache_path / f"{file.name}.{sheet}.feather")


    def convert_to_excel(self):
        for folder in self.folder_list:
            cache_path = folder / "cache"

            if not cache_path.exists():
                continue

            cached_files = [f for f in cache_path.glob("*.feather")]
            excel_data: dict[str, set[tuple[str, pd.DataFrame]]] = {}

            for file in cached_files:
                sheet_name = file.suffixes[0]
                file_data = pd.read_feather(file)
                if file.name in excel_data:
                    excel_data[file.name].add((sheet_name, file_data))
                else:
                    excel_data[file.name] = {(sheet_name, file_data)}

            for file_name, contents in excel_data.items():
                with pd.ExcelWriter(folder / f"{file_name}.xlsx") as writer:
                    for sheet, df in contents:
                        df.to_excel(writer, sheet_name=sheet, index=False)

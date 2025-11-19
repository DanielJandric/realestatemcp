import pandas as pd
from pathlib import Path

ROOT_DIR = Path("c:/OneDriveExport")

def debug_excel():
    excel_files = list(ROOT_DIR.glob("*.xlsx"))
    if not excel_files:
        print("No Excel files found.")
        return

    f = excel_files[0]
    print(f"Inspecting {f.name}...")
    
    try:
        df = pd.read_excel(f, header=None, nrows=20)
        with open("excel_dump.txt", "w", encoding="utf-8") as out:
            out.write(f"File: {f.name}\n")
            out.write(df.fillna("").to_string())
        print("Dumped to excel_dump.txt")
    except Exception as e:
        print(f"Error reading {f.name}: {e}")

if __name__ == "__main__":
    debug_excel()

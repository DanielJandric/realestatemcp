import pandas as pd

def get_headers():
    files = {
        "Litiges": ("c:/OneDriveExport/Incremental1/Litiges.xlsx", 2),
        "Sinistres": ("c:/OneDriveExport/Incremental1/Tableau suivi sinistre.xlsx", 2) # Assuming 2 based on analysis
    }
    
    for name, (path, header_row) in files.items():
        print(f"\n--- {name} Headers (Row {header_row}) ---")
        try:
            df = pd.read_excel(path, header=header_row, nrows=0)
            print(list(df.columns))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    get_headers()

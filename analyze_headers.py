import pandas as pd

FILES = [
    "c:/OneDriveExport/Incremental1/Litiges.xlsx",
    "c:/OneDriveExport/Incremental1/Tableau suivi sinistre.xlsx"
]

def analyze():
    for f in FILES:
        print(f"\n--- Analyzing {f} ---")
        try:
            df = pd.read_excel(f, header=None, nrows=20)
            for idx, row in df.iterrows():
                # Count non-null strings
                non_null = [str(x) for x in row.values if pd.notna(x) and str(x).strip() != ""]
                if len(non_null) > 2:
                    print(f"Row {idx}: {non_null}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    analyze()

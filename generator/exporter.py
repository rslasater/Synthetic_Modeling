import os
import pandas as pd

def ensure_directory_exists(filepath):
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def export_to_csv(transactions, filepath):
    ensure_directory_exists(filepath)
    df = pd.DataFrame(transactions)
    df.to_csv(filepath, index=False)
    print(f"[✔] Exported {len(df)} transactions to {filepath}")

def export_to_excel(data, filepath):
    ensure_directory_exists(filepath)
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        if isinstance(data, dict):
            total = 0
            for sheet, df in data.items():
                df.to_excel(writer, sheet_name=sheet, index=False)
                total += len(df)
            print(f"[✔] Exported {total} rows to {filepath}")
        else:
            df = pd.DataFrame(data)
            df.to_excel(writer, index=False)
            print(f"[✔] Exported {len(df)} transactions to {filepath}")

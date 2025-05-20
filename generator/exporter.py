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

def export_to_excel(transactions, filepath):
    ensure_directory_exists(filepath)
    df = pd.DataFrame(transactions)
    df.to_excel(filepath, index=False, engine='openpyxl')
    print(f"[✔] Exported {len(df)} transactions to {filepath}")

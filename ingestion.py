import pandas as pd
import os

def load_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        # Try UTF-8 first, fallback to latin1 if decoding fails
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding="latin1")

    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)

    else:
        raise ValueError(f"Unsupported file format: {ext}")

    return df
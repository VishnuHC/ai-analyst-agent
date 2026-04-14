import pandas as pd
import os

from ocr_indian import ocr_image
from ocr_structured import process_ocr_text

# NOTE:
# Future upgrade → Smart OCR switching:
# - Clean text → direct parsing
# - Noisy image → EasyOCR
# - High-speed mode → Tesseract (optional)

def clear_stale_data(data_folder="data"):
    """
    Remove only stale processed/metadata files that no longer correspond
    to files in the data folder.
    """
    if not os.path.exists(data_folder):
        return

    # current valid base filenames
    valid_files = {
        os.path.splitext(f)[0]
        for f in os.listdir(data_folder) if not f.startswith(".")
    }

    for folder in ["processed", "metadata"]:
        if not os.path.exists(folder):
            continue

        for file in os.listdir(folder):
            file_base = os.path.splitext(file)[0]
            file_path = os.path.join(folder, file)

            # delete only if not present in data/
            if file_base not in valid_files:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"[Cleanup]: Removed stale file {file}")
                except Exception as e:
                    print(f"[Cleanup Error]: {e}")

def analyze_dataframe_structure(df: pd.DataFrame):
    """
    Detect whether dataframe is:
    - structured (good for calculations)
    - semi-structured (better as text)
    """
    # Heuristic: numeric density
    numeric_cols = df.select_dtypes(include=["number"]).columns
    numeric_ratio = len(numeric_cols) / max(len(df.columns), 1)

    # Heuristic: uniqueness (categorical vs messy text)
    uniqueness = df.nunique().mean()

    # Heuristic: empty cells
    empty_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1] + 1)

    return {
        "numeric_ratio": numeric_ratio,
        "uniqueness": uniqueness,
        "empty_ratio": empty_ratio
    }


def dataframe_to_text(df: pd.DataFrame, max_rows=20):
    """
    Convert dataframe to readable text for LLM when structure is weak
    """
    if df.empty:
        return ""
    sample = df.head(max_rows)
    return sample.to_string(index=False)

def load_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    # --- CSV ---
    if ext == ".csv":
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding="latin1")
            if df.empty:
                print("[Warning]: Empty CSV detected")
                return {"type": "text", "data": ""}

        meta = analyze_dataframe_structure(df)

        print(f"[Ingestion]: profile={meta}")

        # Decide usage mode
        if meta["numeric_ratio"] > 0.4:
            print("[Mode]: Structured → Use for calculations")
            return {"type": "table", "data": df}

        else:
            print("[Mode]: Semi-structured → Use as text")
            text = dataframe_to_text(df)
            return {"type": "text", "data": text}

    # --- Excel ---
    elif ext in [".xlsx", ".xls"]:
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            print(f"[Excel Load Error]: {e}")
            return {"type": "text", "data": ""}

        if df.empty:
            print("[Warning]: Empty Excel file")
            return {"type": "text", "data": ""}

        meta = analyze_dataframe_structure(df)

        print(f"[Ingestion]: profile={meta}")

        if meta["numeric_ratio"] > 0.4:
            print("[Mode]: Structured → Use for calculations")
            return {"type": "table", "data": df}
        else:
            print("[Mode]: Semi-structured → Use as text")
            text = dataframe_to_text(df)
            return {"type": "text", "data": text}

    # --- IMAGE (OCR) ---
    elif ext in [".png", ".jpg", ".jpeg"]:
        print("[OCR Triggered]: Processing image")

        text = ocr_image(file_path)

        # --- Structured OCR Processing ---
        df = process_ocr_text(text)

        if df is not None and not df.empty:
            return {"type": "table", "data": df}
        else:
            return {"type": "text", "data": text}

    # --- FUTURE: Smart OCR Switching Placeholder ---
    elif ext in [".pdf"]:
        print("[PDF]: Falling back to text mode (basic)")
        return {"type": "text", "data": ""}

    else:
        raise ValueError(f"Unsupported file format: {ext}")
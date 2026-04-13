import pandas as pd
import os

from ocr_indian import ocr_image
from ocr_structured import process_ocr_text

# NOTE:
# Future upgrade → Smart OCR switching:
# - Clean text → direct parsing
# - Noisy image → EasyOCR
# - High-speed mode → Tesseract (optional)

def load_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    # --- CSV ---
    if ext == ".csv":
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding="latin1")
        return df

    # --- Excel ---
    elif ext in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)

    # --- IMAGE (OCR) ---
    elif ext in [".png", ".jpg", ".jpeg"]:
        print("[OCR Triggered]: Processing image")

        text = ocr_image(file_path)

        # --- Structured OCR Processing ---
        df = process_ocr_text(text)

        return df

    # --- FUTURE: Smart OCR Switching Placeholder ---
    elif ext in [".pdf"]:
        print("[PDF Detected]: Placeholder for OCR + parser switching")
        raise ValueError("PDF OCR pipeline not implemented yet")

    else:
        raise ValueError(f"Unsupported file format: {ext}")
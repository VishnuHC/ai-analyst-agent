

import re
import pandas as pd
from typing import Dict, Any, List


def extract_key_value_pairs(text: str) -> Dict[str, Any]:
    """
    Extract key-value pairs like:
    Total: 5000
    Date: 12/02/2024
    """
    pairs = {}

    lines = text.split("\n")

    for line in lines:
        # Match patterns like "Key: Value"
        match = re.match(r"([\w\s]+)[:\-]\s*(.+)", line)
        if match:
            key = match.group(1).strip().lower()
            value = match.group(2).strip()

            # Try converting numeric values
            try:
                value = float(value.replace(",", ""))
            except:
                pass

            pairs[key] = value

    return pairs


def extract_numbers(text: str) -> List[float]:
    """
    Extract all numbers from text
    """
    numbers = re.findall(r"\d+\.?\d*", text)
    return [float(num) for num in numbers]


def structured_from_text(text: str) -> pd.DataFrame:
    """
    Convert OCR text into structured DataFrame
    """
    kv_pairs = extract_key_value_pairs(text)
    numbers = extract_numbers(text)

    data = []

    # Add key-value pairs
    for k, v in kv_pairs.items():
        data.append({
            "field": k,
            "value": v,
            "type": "key_value"
        })

    # Add numeric values separately
    for num in numbers:
        data.append({
            "field": "number",
            "value": num,
            "type": "numeric"
        })

    df = pd.DataFrame(data)

    return df


def detect_invoice_like(text: str) -> bool:
    """
    Simple heuristic to detect invoices/receipts
    """
    keywords = ["total", "amount", "invoice", "bill", "tax", "gst"]

    text_lower = text.lower()

    for k in keywords:
        if k in text_lower:
            return True

    return False


def process_ocr_text(text: str) -> pd.DataFrame:
    """
    Main entry point:
    - Detect document type
    - Extract structured data
    """
    if detect_invoice_like(text):
        print("[Structured OCR]: Invoice-like document detected")
        return structured_from_text(text)

    # fallback: return raw lines
    lines = text.split("\n")
    return pd.DataFrame({"text": lines})
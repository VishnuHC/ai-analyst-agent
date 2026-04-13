import os
from typing import List, Dict, Any

import easyocr


# Default languages: English + common Indian languages
DEFAULT_LANGUAGES = ["en", "hi", "te", "ta"]


class OCRIndian:
    def __init__(self, languages: List[str] = None, gpu: bool = False):
        """
        Initialize EasyOCR reader.
        """
        self.languages = languages if languages else DEFAULT_LANGUAGES
        self.gpu = gpu

        print(f"[OCR] Initializing with languages: {self.languages}")
        self.reader = easyocr.Reader(self.languages, gpu=self.gpu)

    def extract_text(self, image_path: str) -> str:
        """
        Extract raw text from an image.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"File not found: {image_path}")

        results = self.reader.readtext(image_path)

        # results = [(bbox, text, confidence)]
        texts = [res[1] for res in results]

        return "\n".join(texts)

    def extract_with_metadata(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extract text with bounding boxes and confidence.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"File not found: {image_path}")

        results = self.reader.readtext(image_path)

        structured = []
        for bbox, text, conf in results:
            structured.append({
                "text": text,
                "confidence": float(conf),
                "bbox": bbox
            })

        return structured


# --- Utility function for quick use ---
def ocr_image(image_path: str, languages: List[str] = None) -> str:
    """
    Simple wrapper for quick OCR usage.
    """
    ocr = OCRIndian(languages=languages)
    return ocr.extract_text(image_path)


# --- Batch OCR (for folders) ---
def ocr_folder(folder_path: str, languages: List[str] = None) -> Dict[str, str]:
    """
    OCR all images in a folder.
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    results = {}
    ocr = OCRIndian(languages=languages)

    for file in os.listdir(folder_path):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            full_path = os.path.join(folder_path, file)
            try:
                text = ocr.extract_text(full_path)
                results[file] = text
                print(f"[OCR] Processed: {file}")
            except Exception as e:
                print(f"[OCR Error] {file}: {e}")

    return results

import os
import fitz  # for PDF page extraction
from pdf_loader import extract_pdf_text
from ocr_engine import extract_text_from_image


def load_documents(folder="docs"):
    """
    Load all supported documents and extract text
    """
    documents = []

    if not os.path.exists(folder):
        return documents

    for file in os.listdir(folder):
        path = os.path.join(folder, file)

        if file.endswith(".pdf"):
            doc = fitz.open(path)
            for i, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    documents.append((text, file, i + 1))

        elif file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg"):
            text = extract_text_from_image(path)
            documents.append((text, file, None))

        elif file.endswith(".txt"):
            with open(path, "r") as f:
                documents.append((f.read(), file, None))

    return documents
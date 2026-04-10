

import fitz  # PyMuPDF


def extract_pdf_text(path):
    """
    Extract text from a PDF file
    """
    text = ""
    doc = fitz.open(path)

    for page in doc:
        text += page.get_text()

    return text


import pytesseract
from PIL import Image


def extract_text_from_image(path):
    """
    Extract text from an image using OCR
    """
    img = Image.open(path)
    text = pytesseract.image_to_string(img)
    return text
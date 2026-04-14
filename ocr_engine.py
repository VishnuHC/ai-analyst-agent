import cv2
import numpy as np
from langdetect import detect
from deep_translator import GoogleTranslator

OCR_CACHE = {}
OCR_LANGUAGES = ['en', 'hi', 'te', 'ta']  # English, Hindi, Telugu, Tamil


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except:
        return "unknown"


def translate_to_english(text: str, source_lang: str) -> str:
    try:
        if source_lang == "en":
            return text
        translated = GoogleTranslator(source=source_lang, target='en').translate(text)
        return translated
    except Exception as e:
        print(f"[Translation Error]: {e}")
        return text


def ocr_image(image_path: str, languages=None) -> str:
    """
    Smart OCR:
    - Clean/simple image → Tesseract (fast)
    - Complex/noisy → EasyOCR (accurate)
    """

    cache_key = (image_path, tuple(languages) if languages else tuple(OCR_LANGUAGES))
    if cache_key in OCR_CACHE:
        return OCR_CACHE[cache_key]

    try:
        img = cv2.imread(image_path)

        if img is None:
            raise ValueError("Image not found or unreadable")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # --- Quality heuristic ---
        variance = np.var(gray)

        # --- Decision logic ---
        if variance > 1000:
            print("[OCR] Using Tesseract (clean image)")
            try:
                import pytesseract
                text = pytesseract.image_to_string(gray)
                lang = detect_language(text)
                print(f"[Detected Language]: {lang}")

                translated_text = translate_to_english(text, lang)

                OCR_CACHE[cache_key] = translated_text
                return translated_text
            except Exception as e:
                print(f"[Tesseract Failed]: {e}")

        # Fallback → EasyOCR
        print("[OCR] Using EasyOCR (complex image)")
        import easyocr
        langs = languages if languages else OCR_LANGUAGES
        reader = easyocr.Reader(langs, gpu=False)
        result = reader.readtext(image_path, detail=0)

        text = "\n".join(result)
        lang = detect_language(text)
        print(f"[Detected Language]: {lang}")

        translated_text = translate_to_english(text, lang)

        OCR_CACHE[cache_key] = translated_text
        return translated_text

    except Exception as e:
        print(f"[OCR Error]: {e}")
        return ""

# --- Compatibility wrapper ---
def extract_text_from_image(image_path: str) -> str:
    """
    Wrapper for backward compatibility with existing imports
    """
    return ocr_image(image_path)
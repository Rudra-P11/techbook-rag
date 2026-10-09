import shutil
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self):
        self._available = False
        self.pytesseract = None

        try:
            import pytesseract
            # Verify if tesseract executable binary is present in PATH
            tesseract_bin = shutil.which("tesseract")
            if tesseract_bin:
                pytesseract.get_tesseract_version()
                self.pytesseract = pytesseract
                self._available = True
                logger.info(f"Tesseract OCR binary detected at: {tesseract_bin}")
            else:
                logger.info("Tesseract binary not found in system PATH. Native PDF text extraction enabled.")
        except Exception:
            self._available = False
            logger.info("Tesseract binary not found in system PATH. Native PDF text extraction enabled.")

    def is_available(self) -> bool:
        return self._available

    def ocr_image(self, image: Image.Image) -> str:
        if not self._available or not self.pytesseract:
            return ""

        try:
            text = self.pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.warning(f"OCR execution failed: {e}")
            return ""


ocr_service = OCRService()
